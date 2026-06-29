"""Tableau de bord gerant alimente par les services metier."""

from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import Qt, Signal
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
from app.services.alerte_service import AlerteService
from app.services.auth_service import SessionUtilisateur
from app.services.produit_service import ProduitService
from app.services.rapport_service import RapportService
from app.ui.components.charts import SalesLineChart
from app.ui.components.icons import ui_icon


class GerantDashboardPage(QWidget):
    voir_tout_demande = Signal(str)

    def __init__(
        self,
        session_utilisateur: SessionUtilisateur,
        rapport_service: RapportService | None = None,
        produit_service: ProduitService | None = None,
        alerte_service: AlerteService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.session_utilisateur = session_utilisateur
        self._rapport_service = rapport_service or RapportService()
        self._produit_service = produit_service or ProduitService()
        self._alerte_service = alerte_service or AlerteService()
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
        self.sales_card = StatCard("Chiffre d'affaires", "0 CDF", "cart", "green")
        self.transactions_card = StatCard("Transactions", "0", "transactions", "blue")
        self.average_card = StatCard("Panier moyen", "0 CDF", "wallet", "green")
        self.products_card = StatCard("Produits vendus", "0", "product", "blue")
        self.alerts_card = StatCard("Alertes actives", "0", "warning", "orange")
        for index, card in enumerate(
            (
                self.sales_card,
                self.transactions_card,
                self.average_card,
                self.products_card,
                self.alerts_card,
            )
        ):
            cards.addWidget(card, index // 3, index % 3)
        layout.addLayout(cards)

        panels = QHBoxLayout()
        chart_panel = QFrame()
        chart_panel.setObjectName("contentPanel")
        chart_layout = QVBoxLayout(chart_panel)
        chart_layout.addWidget(QLabel("Evolution des ventes (CDF)"))
        self.chart_host = QVBoxLayout()
        chart_layout.addLayout(self.chart_host)
        panels.addWidget(chart_panel, 3)

        product_panel = QFrame()
        product_panel.setObjectName("contentPanel")
        product_layout = QVBoxLayout(product_panel)
        header = QHBoxLayout()
        header.addWidget(QLabel("Produits les plus vendus"))
        header.addStretch(1)
        view_products = QPushButton("Voir tout")
        view_products.clicked.connect(lambda: self.voir_tout_demande.emit("rapports"))
        header.addWidget(view_products)
        product_layout.addLayout(header)
        self.products_table = QTableWidget(0, 3)
        self.products_table.setHorizontalHeaderLabels(["Produit", "Quantite", "CA (CDF)"])
        self.products_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.products_table.verticalHeader().setVisible(False)
        product_layout.addWidget(self.products_table)
        panels.addWidget(product_panel, 2)
        layout.addLayout(panels, 1)

        links = QHBoxLayout()
        for label, target in (
            ("Vendeurs", "vendeurs"),
            ("Historique des actions", "historique"),
            ("Alertes", "alertes"),
        ):
            button = QPushButton(label)
            button.setObjectName("outlineButton")
            button.clicked.connect(
                lambda checked=False, key=target: self.voir_tout_demande.emit(key)
            )
            links.addWidget(button)
        layout.addLayout(links)

    def _set_period(self, days: int) -> None:
        self._jours = days
        self.on_show()

    def on_show(self) -> None:
        fin = date.today()
        debut = fin - timedelta(days=self._jours - 1)
        try:
            rapport = self._rapport_service.rapport_periode(
                self.session_utilisateur,
                date_debut=debut,
                date_fin=fin,
            )
            alertes = self._alerte_service.lister_alertes(
                self.session_utilisateur, non_lues_seulement=False
            )
        except Exception:
            # Le point d'entree migre la base avant l'UI; ce repli garde les
            # apercus et tests de widgets autonomes non bloquants.
            return
        self.sales_card.set_value(_cdf(rapport.total_jour))
        self.transactions_card.set_value(str(rapport.ventes_jour))
        self.average_card.set_value(_cdf(rapport.panier_moyen))
        self.products_card.set_value(str(rapport.produits_vendus))
        self.alerts_card.set_value(str(len(alertes)))
        while self.chart_host.count():
            item = self.chart_host.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        evolution = rapport.evolution or []
        maximum = max(1, max((item.total for item in evolution), default=0))
        self.chart_host.addWidget(
            SalesLineChart(
                [item.date_vente.strftime("%d/%m") for item in evolution],
                [item.total / maximum for item in evolution],
            )
        )
        self.products_table.setRowCount(len(rapport.produits[:5]))
        for row, item in enumerate(rapport.produits[:5]):
            for column, value in enumerate(
                (item.produit_nom, str(item.quantite), _number(item.total))
            ):
                self.products_table.setItem(row, column, QTableWidgetItem(value))


class StatCard(QFrame):
    def __init__(self, title: str, value: str, icon: str, color: str) -> None:
        super().__init__()
        self.setObjectName("statCard")
        self.setMinimumHeight(104)
        layout = QHBoxLayout(self)
        bubble = QLabel()
        bubble.setObjectName(f"iconBubble_{color}")
        bubble.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bubble.setFixedSize(48, 48)
        bubble.setPixmap(ui_icon(icon, "#ffffff", 24).pixmap(24, 24))
        layout.addWidget(bubble)
        texts = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("statTitle")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("statValue")
        texts.addWidget(title_label)
        texts.addWidget(self.value_label)
        layout.addLayout(texts, 1)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


def _number(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def _cdf(value: int) -> str:
    return f"{_number(value)} CDF"
