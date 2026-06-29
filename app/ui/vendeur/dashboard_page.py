"""Tableau de bord personnel du vendeur."""

from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.exceptions import SalmospharmError
from app.services.auth_service import SessionUtilisateur
from app.services.rapport_service import RapportService


class VendeurDashboardPage(QWidget):
    voir_tout_demande = Signal(str)

    def __init__(
        self,
        session_utilisateur: SessionUtilisateur,
        rapport_service: RapportService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.session_utilisateur = session_utilisateur
        self._rapport_service = rapport_service or RapportService()
        self._jours = 1
        self.setObjectName("dashboardPage")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        periods = QHBoxLayout()
        periods.addWidget(QLabel("Periode"))
        group = QButtonGroup(self)
        for label, days in (("Jour", 1), ("7 jours", 7), ("30 jours", 30)):
            button = QPushButton(label)
            button.setCheckable(True)
            button.setObjectName("smallButton")
            button.setChecked(days == 1)
            button.clicked.connect(lambda checked=False, value=days: self._set_period(value))
            group.addButton(button)
            periods.addWidget(button)
        periods.addStretch(1)
        layout.addLayout(periods)

        cards = QGridLayout()
        self.total_card = MetricCard("Total encaisse", "0 CDF")
        self.transactions_card = MetricCard("Transactions", "0")
        self.average_card = MetricCard("Panier moyen", "0 CDF")
        self.items_card = MetricCard("Articles vendus", "0")
        for index, card in enumerate(
            (self.total_card, self.transactions_card, self.average_card, self.items_card)
        ):
            cards.addWidget(card, index // 2, index % 2)
        layout.addLayout(cards)

        panel = QFrame()
        panel.setObjectName("contentPanel")
        panel_layout = QVBoxLayout(panel)
        header = QHBoxLayout()
        header.addWidget(QLabel("Ventes recentes"))
        header.addStretch(1)
        view = QPushButton("Voir tout")
        view.setObjectName("outlineButton")
        view.clicked.connect(lambda: self.voir_tout_demande.emit("historique_ventes"))
        header.addWidget(view)
        panel_layout.addLayout(header)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Numero", "Date", "Articles", "Total (CDF)"]
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        panel_layout.addWidget(self.table)
        layout.addWidget(panel, 1)

    def _set_period(self, days: int) -> None:
        self._jours = days
        self.on_show()

    def on_show(self) -> None:
        fin = date.today()
        debut = fin - timedelta(days=self._jours - 1)
        try:
            ventes = self._rapport_service.lister_ventes(
                self.session_utilisateur,
                date_debut=debut,
                date_fin=fin,
                limit=100,
            )
        except SalmospharmError as exc:
            QMessageBox.warning(self, "Tableau de bord", str(exc))
            return
        total = sum(item.total for item in ventes)
        articles = sum(item.articles for item in ventes)
        self.total_card.set_value(_cdf(total))
        self.transactions_card.set_value(str(len(ventes)))
        self.average_card.set_value(_cdf(int(total / len(ventes)) if ventes else 0))
        self.items_card.set_value(str(articles))
        self.table.setRowCount(len(ventes[:10]))
        for row, item in enumerate(ventes[:10]):
            for column, value in enumerate(
                (
                    item.numero_vente,
                    item.date_vente,
                    str(item.articles),
                    _number(item.total),
                )
            ):
                self.table.setItem(row, column, QTableWidgetItem(value))


class MetricCard(QFrame):
    def __init__(self, title: str, value: str) -> None:
        super().__init__()
        self.setObjectName("statCard")
        layout = QVBoxLayout(self)
        title_label = QLabel(title)
        title_label.setObjectName("statTitle")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("statValue")
        layout.addWidget(title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


def _number(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def _cdf(value: int) -> str:
    return f"{_number(value)} CDF"
