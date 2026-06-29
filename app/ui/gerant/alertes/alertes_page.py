"""Consultation des alertes stock et expiration."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.core.exceptions import SalmospharmError
from app.services.alerte_service import AlerteService
from app.services.auth_service import SessionUtilisateur


class AlertesPage(QWidget):
    """Liste les alertes metier et permet de les marquer comme lues."""

    def __init__(self, session_utilisateur: SessionUtilisateur, alerte_service: AlerteService | None = None, autoload: bool = True, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("alertsPage")
        self.session_utilisateur = session_utilisateur
        self._alerte_service = alerte_service or AlerteService()
        self._build_ui()
        if autoload:
            self.on_show()

    def on_show(self) -> None:
        self._charger()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        title = QLabel("Alertes")
        title.setObjectName("reportsTitle")
        subtitle = QLabel("Surveillez les stocks faibles et les lots proches de l'expiration.")
        subtitle.setObjectName("reportsSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        filters = QHBoxLayout()
        self.type_combo = QComboBox()
        self.type_combo.addItem("Tous les types", "")
        self.type_combo.addItem("Stock faible ou rupture", "STOCK_FAIBLE")
        self.type_combo.addItem("Expiration proche", "EXPIRATION_PROCHE")
        self.type_combo.addItem("Produit expire", "PRODUIT_EXPIRE")
        self.type_combo.currentIndexChanged.connect(self._charger)
        self.status_combo = QComboBox()
        self.status_combo.addItem("Toutes les alertes actives", "")
        self.status_combo.addItem("Non lues", "NON_LUE")
        self.status_combo.addItem("Acquittees", "LUE")
        self.status_combo.currentIndexChanged.connect(self._charger)
        filters.addWidget(self.type_combo)
        filters.addWidget(self.status_combo)
        filters.addStretch(1)
        layout.addLayout(filters)
        panel = QFrame()
        panel.setObjectName("reportsPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_title = QLabel("Alertes recentes")
        panel_title.setObjectName("reportsPanelTitle")
        panel_title.setContentsMargins(18, 16, 18, 12)
        panel_layout.addWidget(panel_title)
        self.table = QTableWidget(0, 6)
        self.table.setObjectName("reportsTable")
        self.table.setHorizontalHeaderLabels(["Type", "Produit", "Lot", "Message", "Statut", "Action"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setMinimumHeight(500)
        self.table.cellDoubleClicked.connect(self._ouvrir_produit)
        panel_layout.addWidget(self.table)
        layout.addWidget(panel, 1)

    def _charger(self) -> None:
        try:
            alertes = self._alerte_service.lister_alertes(self.session_utilisateur)
            non_lues = sum(1 for alerte in alertes if alerte.est_lue == 0)
            self.compteur_change.emit(non_lues)
            type_filtre = str(self.type_combo.currentData() or "")
            statut = str(self.status_combo.currentData() or "")
            alertes = [
                alerte
                for alerte in alertes
                if (not type_filtre or alerte.type_alerte == type_filtre)
                and (
                    not statut
                    or (statut == "NON_LUE" and alerte.est_lue == 0)
                    or (statut == "LUE" and alerte.est_lue == 1)
                )
            ]
            self.table.setRowCount(0)
            for alerte in alertes:
                row = self.table.rowCount()
                self.table.insertRow(row)
                values = [
                    alerte.type_alerte,
                    alerte.produit.nom if alerte.produit is not None else "",
                    alerte.lot.numero_lot if alerte.lot is not None else "-",
                    alerte.message or "",
                    "Lue" if alerte.est_lue else "Non lue",
                ]
                for column, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setData(Qt.ItemDataRole.UserRole, alerte.id)
                    self.table.setItem(row, column, item)
                button = QPushButton("Marquer lue")
                button.setObjectName("outlineButton")
                button.setEnabled(alerte.est_lue == 0)
                button.clicked.connect(lambda checked=False, alerte_id=alerte.id: self._marquer_lue(alerte_id))
                self.table.setCellWidget(row, 5, button)
                produit_item = self.table.item(row, 1)
                if produit_item is not None:
                    produit_item.setToolTip("Double-cliquez pour ouvrir le produit")
                    produit_item.setData(
                        Qt.ItemDataRole.UserRole + 1, alerte.produit_id
                    )
        except SalmospharmError as exc:
            QMessageBox.warning(self, "SALMOSPHARM", str(exc))

    def _ouvrir_produit(self, row: int, _column: int) -> None:
        item = self.table.item(row, 1)
        if item is None:
            return
        produit_id = item.data(Qt.ItemDataRole.UserRole + 1)
        if produit_id is not None:
            self.produit_demande.emit(int(produit_id))

    def _marquer_lue(self, alerte_id: int) -> None:
        try:
            self._alerte_service.marquer_lue(self.session_utilisateur, alerte_id=alerte_id)
            self._charger()
        except SalmospharmError as exc:
            QMessageBox.warning(self, "SALMOSPHARM", str(exc))
    compteur_change = Signal(int)
    produit_demande = Signal(int)
