"""Coordination Qt de la verification asynchrone des alertes."""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal

from app.services.alert_events import depiler_evenements_alertes, publier_evenement_alerte
from app.services.alerte_service import AlerteService


LOGGER = logging.getLogger(__name__)


class _WorkerSignals(QObject):
    termine = Signal(bool)


class _AlertWorker(QRunnable):
    def __init__(self, service: AlerteService, produit_ids: set[int] | None) -> None:
        super().__init__()
        self.service = service
        self.produit_ids = produit_ids
        self.signals = _WorkerSignals()

    def run(self) -> None:
        succes = False
        try:
            self.service.reconcilier_alertes(produit_ids=self.produit_ids)
            succes = True
        except Exception:
            LOGGER.exception("La reconciliation des alertes a echoue.")
        self.signals.termine.emit(succes)


class AlertCoordinator(QObject):
    """Traite la file immediatement et lance un controle complet chaque minute."""

    alerts_updated = Signal()

    def __init__(self, service: AlerteService | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._service = service or AlerteService()
        self._pool = QThreadPool.globalInstance()
        self._running = False
        self._queue_timer = QTimer(self)
        self._queue_timer.setInterval(250)
        self._queue_timer.timeout.connect(self._traiter_file)
        self._sweep_timer = QTimer(self)
        self._sweep_timer.setInterval(60_000)
        self._sweep_timer.timeout.connect(lambda: publier_evenement_alerte(None))

    def demarrer(self) -> None:
        self._service.reinitialiser_alertes_actives_au_demarrage()
        self._queue_timer.start()
        self._sweep_timer.start()
        publier_evenement_alerte(None)

    def arreter(self) -> None:
        self._queue_timer.stop()
        self._sweep_timer.stop()

    def _traiter_file(self) -> None:
        if self._running:
            return
        events = depiler_evenements_alertes()
        if not events:
            return
        produit_ids = None if None in events else {int(value) for value in events if value is not None}
        self._running = True
        worker = _AlertWorker(self._service, produit_ids)
        worker.signals.termine.connect(self._termine)
        self._pool.start(worker)

    def _termine(self, succes: bool) -> None:
        self._running = False
        if succes:
            self.alerts_updated.emit()
