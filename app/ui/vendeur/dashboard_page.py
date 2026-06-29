"""Tableau de bord personnel du vendeur."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from app.core.exceptions import SalmospharmError
from app.services.auth_service import SessionUtilisateur
from app.services.rapport_service import RapportService
from app.ui.components.charts import SalesLineChart
from app.ui.components.dashboard import DashboardMetricCard, empty_label, panel_header
from app.ui.components.icons import ui_icon


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
        self.setObjectName("sellerDashboard")
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)
        cards = QHBoxLayout()
        cards.setSpacing(16)
        self.sales_card = DashboardMetricCard("Ventes du jour", "cart", "green")
        self.transactions_card = DashboardMetricCard("Transactions", "receipt", "blue")
        self.total_card = DashboardMetricCard("Total encaissé (CDF)", "wallet", "green")
        self.items_card = DashboardMetricCard("Articles vendus", "stock", "blue")
        for card in (self.sales_card, self.transactions_card, self.total_card, self.items_card):
            cards.addWidget(card, 1)
        root.addLayout(cards)

        middle = QHBoxLayout()
        middle.setSpacing(16)
        chart_panel = _panel("sellerEvolutionPanel")
        header, _ = panel_header("Évolution des ventes (CDF)")
        period = QPushButton("Aujourd’hui")
        period.setObjectName("dashboardPeriodButton")
        header.addWidget(period)
        chart_panel.layout().addLayout(header)
        self.chart_host = QVBoxLayout()
        chart_panel.layout().addLayout(self.chart_host, 1)
        middle.addWidget(chart_panel, 3)

        recent_panel = _panel("sellerRecentSalesPanel")
        header, button = panel_header("Ventes récentes", "Voir tout")
        button.clicked.connect(lambda: self.voir_tout_demande.emit("historique_ventes"))
        recent_panel.layout().addLayout(header)
        self.recent_layout = QVBoxLayout()
        recent_panel.layout().addLayout(self.recent_layout)
        middle.addWidget(recent_panel, 2)
        root.addLayout(middle, 3)

        bottom = QHBoxLayout()
        bottom.setSpacing(16)
        products_panel = _panel("sellerTopProductsPanel")
        products_panel.layout().addLayout(panel_header("Produits les plus vendus aujourd’hui")[0])
        self.products_table = QTableWidget(0, 3)
        self.products_table.setObjectName("dashboardTable")
        self.products_table.setHorizontalHeaderLabels(["Produit", "Quantité vendue", "Chiffre d’affaires (CDF)"])
        self.products_table.verticalHeader().setVisible(False)
        self.products_table.setShowGrid(False)
        self.products_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.products_table.horizontalHeader().setStretchLastSection(True)
        products_panel.layout().addWidget(self.products_table)
        bottom.addWidget(products_panel, 3)

        summary = _panel("sellerSummaryPanel")
        summary.layout().addLayout(panel_header("Résumé du jour")[0])
        self.average_value = _summary_row(summary.layout(), "Panier moyen", "wallet")
        self.best_value = _summary_row(summary.layout(), "Meilleure vente", "money")
        self.hour_value = _summary_row(summary.layout(), "Heure la plus active", "history")
        self.article_value = _summary_row(summary.layout(), "Total d’articles", "stock")
        summary.layout().addStretch(1)
        bottom.addWidget(summary, 2)
        root.addLayout(bottom, 2)

    def on_show(self) -> None:
        try:
            data = self._rapport_service.synthese_vendeur(self.session_utilisateur)
        except SalmospharmError:
            return
        self.sales_card.set_data(_cdf(data.total), None, "Activité personnelle")
        self.transactions_card.set_data(str(data.transactions), None, "Ventes validées")
        self.total_card.set_data(_cdf(data.total), None, "Espèces encaissées")
        self.items_card.set_data(str(data.articles), None, "Quantité totale")
        _clear_layout(self.chart_host)
        self.chart_host.addWidget(
            SalesLineChart(
                [label for label, _value in data.evolution_horaire],
                [value for _label, value in data.evolution_horaire],
            )
        )
        _clear_layout(self.recent_layout)
        for sale in data.ventes:
            self.recent_layout.addWidget(_sale_row(sale.numero_vente, sale.date_vente, sale.total))
        if not data.ventes:
            self.recent_layout.addWidget(empty_label("Aucune vente aujourd’hui."))
        self.products_table.setRowCount(len(data.produits))
        for row, product in enumerate(data.produits):
            self.products_table.setRowHeight(row, 34)
            for column, value in enumerate((product.produit_nom, str(product.quantite), _number(product.total))):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | (Qt.AlignmentFlag.AlignRight if column else Qt.AlignmentFlag.AlignLeft))
                self.products_table.setItem(row, column, item)
        self.average_value.setText(_cdf(data.panier_moyen))
        self.best_value.setText(_cdf(data.meilleure_vente))
        self.hour_value.setText(data.heure_active)
        self.article_value.setText(str(data.articles))

    def set_compact(self, compact: bool) -> None:
        self.layout().setSpacing(10 if compact else 16)
        for card in self.findChildren(DashboardMetricCard):
            card.setMinimumHeight(88 if compact else 104)


def _panel(name: str) -> QFrame:
    panel = QFrame()
    panel.setObjectName(name)
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(18, 15, 18, 15)
    layout.setSpacing(10)
    return panel


def _summary_row(layout: QVBoxLayout, title: str, icon: str) -> QLabel:
    row = QFrame()
    row.setObjectName("dashboardSummaryRow")
    row_layout = QHBoxLayout(row)
    row_layout.setContentsMargins(7, 7, 7, 7)
    icon_label = QLabel()
    icon_label.setPixmap(ui_icon(icon, "#15933a", 16).pixmap(16, 16))
    label = QLabel(title)
    label.setObjectName("dashboardSummaryLabel")
    value = QLabel("—")
    value.setObjectName("dashboardSummaryValue")
    row_layout.addWidget(icon_label)
    row_layout.addWidget(label)
    row_layout.addStretch(1)
    row_layout.addWidget(value)
    layout.addWidget(row)
    return value


def _sale_row(number: str, date_value: str, total: int) -> QFrame:
    row = QFrame()
    row.setObjectName("dashboardSaleRow")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(7, 6, 7, 6)
    icon = QLabel()
    icon.setObjectName("dashboardSaleIcon")
    icon.setFixedSize(34, 34)
    icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
    icon.setPixmap(ui_icon("receipt", "#173b68", 17).pixmap(17, 17))
    texts = QVBoxLayout()
    texts.setSpacing(0)
    number_label = QLabel(number)
    number_label.setObjectName("dashboardRowTitle")
    date_label = QLabel(date_value)
    date_label.setObjectName("dashboardRowSubtitle")
    texts.addWidget(number_label)
    texts.addWidget(date_label)
    amount = QLabel(_cdf(total))
    amount.setObjectName("dashboardSaleAmount")
    layout.addWidget(icon)
    layout.addLayout(texts, 1)
    layout.addWidget(amount)
    return row


def _clear_layout(layout: QVBoxLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget:
            widget.setParent(None)
            widget.deleteLater()


def _number(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def _cdf(value: int) -> str:
    return f"{_number(value)} CDF"
