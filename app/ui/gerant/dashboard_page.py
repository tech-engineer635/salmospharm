"""Tableau de bord global du gerant, alimente par les services."""

from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from app.services.alerte_service import AlerteService
from app.services.auth_service import SessionUtilisateur
from app.services.rapport_service import RapportService
from app.ui.components.charts import SalesLineChart
from app.ui.components.dashboard import DashboardMetricCard, empty_label, panel_header
from app.ui.components.icons import ui_icon


class GerantDashboardPage(QWidget):
    voir_tout_demande = Signal(str)

    def __init__(
        self,
        session_utilisateur: SessionUtilisateur,
        rapport_service: RapportService | None = None,
        produit_service=None,
        alerte_service: AlerteService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.session_utilisateur = session_utilisateur
        self._rapport_service = rapport_service or RapportService()
        self._alerte_service = alerte_service or AlerteService()
        self.setObjectName("managerDashboard")
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)
        cards = QHBoxLayout()
        cards.setSpacing(14)
        self.sales_card = DashboardMetricCard("Ventes du jour", "cart", "green")
        self.transactions_card = DashboardMetricCard("Transactions", "transactions", "blue")
        self.stock_card = DashboardMetricCard("Articles vendables", "stock", "green")
        self.low_stock_card = DashboardMetricCard("Stock faible", "warning", "orange")
        self.expiry_card = DashboardMetricCard("Expirations proches", "calendar", "red")
        for card in (self.sales_card, self.transactions_card, self.stock_card, self.low_stock_card, self.expiry_card):
            cards.addWidget(card, 1)
        root.addLayout(cards)

        middle = QHBoxLayout()
        middle.setSpacing(16)
        chart_panel = _panel("salesEvolutionPanel")
        chart_layout = chart_panel.layout()
        header, _ = panel_header("Évolution des ventes (CDF)")
        period = QPushButton("7 derniers jours")
        period.setObjectName("dashboardPeriodButton")
        header.addWidget(period)
        chart_layout.addLayout(header)
        self.chart_host = QVBoxLayout()
        chart_layout.addLayout(self.chart_host, 1)
        middle.addWidget(chart_panel, 3)

        products_panel = _panel("topProductsPanel")
        products_layout = products_panel.layout()
        header, button = panel_header("Top produits vendus", "Voir tout")
        button.clicked.connect(lambda: self.voir_tout_demande.emit("rapports"))
        products_layout.addLayout(header)
        self.products_table = _table(["Produit", "Quantité", "CA (CDF)"])
        products_layout.addWidget(self.products_table)
        middle.addWidget(products_panel, 2)
        root.addLayout(middle, 3)

        bottom = QHBoxLayout()
        bottom.setSpacing(16)
        self.vendor_table = _table(["Vendeur", "Ventes (CDF)", "Transactions", "Panier moyen"])
        vendor_panel = _panel("vendorSummaryPanel")
        header, button = panel_header("Synthèse par vendeur", "Voir tout")
        button.clicked.connect(lambda: self.voir_tout_demande.emit("vendeurs"))
        vendor_panel.layout().addLayout(header)
        vendor_panel.layout().addWidget(self.vendor_table)
        bottom.addWidget(vendor_panel, 1)

        activity_panel = _panel("recentActivityPanel")
        header, button = panel_header("Activités récentes", "Voir tout")
        button.clicked.connect(lambda: self.voir_tout_demande.emit("historique"))
        activity_panel.layout().addLayout(header)
        self.activities_layout = QVBoxLayout()
        activity_panel.layout().addLayout(self.activities_layout)
        bottom.addWidget(activity_panel, 1)

        alerts_panel = _panel("quickAlertsPanel")
        header, button = panel_header("Alertes rapides", "Voir tout")
        button.clicked.connect(lambda: self.voir_tout_demande.emit("alertes"))
        alerts_panel.layout().addLayout(header)
        self.alerts_layout = QVBoxLayout()
        alerts_panel.layout().addLayout(self.alerts_layout)
        bottom.addWidget(alerts_panel, 1)
        root.addLayout(bottom, 3)

    def on_show(self) -> None:
        today = date.today()
        try:
            report = self._rapport_service.rapport_periode(
                self.session_utilisateur, date_debut=today, date_fin=today
            )
            week = self._rapport_service.rapport_periode(
                self.session_utilisateur,
                date_debut=today - timedelta(days=6),
                date_fin=today,
            )
            actions = self._rapport_service.lister_actions(
                self.session_utilisateur, limit=5
            )
            alerts = self._alerte_service.lister_alertes(
                self.session_utilisateur, non_lues_seulement=False
            )
        except Exception:
            return
        low = [item for item in alerts if "STOCK" in item.type_alerte]
        expiry = [item for item in alerts if "EXPIR" in item.type_alerte or "PRODUIT_EXPIRE" in item.type_alerte]
        self.sales_card.set_data(_cdf(report.total_jour), report.tendance_ca)
        self.transactions_card.set_data(str(report.ventes_jour), report.tendance_transactions)
        self.stock_card.set_data(str(report.stock_vendable), None, "Unités vendables")
        self.low_stock_card.set_data(str(len(low)), None, "Alertes actives")
        self.expiry_card.set_data(str(len(expiry)), None, "Lots à surveiller")
        _replace_chart(
            self.chart_host,
            [item.date_vente.strftime("%d/%m") for item in week.evolution or []],
            [item.total for item in week.evolution or []],
        )
        _fill_table(self.products_table, [(p.produit_nom, str(p.quantite), _number(p.total)) for p in week.produits[:5]])
        _fill_table(self.vendor_table, [(v.vendeur_nom, _number(v.total), str(v.ventes), _number(v.panier_moyen)) for v in report.vendeurs[:5]])
        _clear_layout(self.activities_layout)
        for action in actions[:5]:
            title = action.details or action.action
            self.activities_layout.addWidget(_info_row("history", _shorten(title), action.date_action, "blue"))
        if not actions:
            self.activities_layout.addWidget(empty_label("Aucune activité récente."))
        _clear_layout(self.alerts_layout)
        for alert in (low[:3] + expiry[:3])[:6]:
            tone = "orange" if "STOCK" in alert.type_alerte else "red"
            self.alerts_layout.addWidget(_info_row("warning", alert.message, alert.type_alerte.replace("_", " ").title(), tone))
        if not alerts:
            self.alerts_layout.addWidget(empty_label("Aucune alerte active."))

    def set_compact(self, compact: bool) -> None:
        self.layout().setSpacing(10 if compact else 16)
        for card in self.findChildren(DashboardMetricCard):
            card.setMinimumHeight(88 if compact else 104)


def _panel(name: str) -> QFrame:
    panel = QFrame()
    panel.setObjectName(name)
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(9)
    return panel


def _table(headers: list[str]) -> QTableWidget:
    table = QTableWidget(0, len(headers))
    table.setObjectName("dashboardTable")
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setShowGrid(False)
    table.horizontalHeader().setStretchLastSection(True)
    return table


def _fill_table(table: QTableWidget, rows: list[tuple[str, ...]]) -> None:
    table.setRowCount(len(rows))
    for row, values in enumerate(rows):
        table.setRowHeight(row, 32)
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | (Qt.AlignmentFlag.AlignRight if column else Qt.AlignmentFlag.AlignLeft))
            table.setItem(row, column, item)


def _info_row(icon: str, title: str, subtitle: str, tone: str) -> QFrame:
    row = QFrame()
    row.setObjectName("dashboardInfoRow")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(7, 5, 7, 5)
    bubble = QLabel()
    bubble.setObjectName(f"dashboardSmallIcon_{tone}")
    bubble.setFixedSize(26, 26)
    bubble.setAlignment(Qt.AlignmentFlag.AlignCenter)
    bubble.setPixmap(ui_icon(icon, "#ffffff", 13).pixmap(13, 13))
    texts = QVBoxLayout()
    texts.setSpacing(0)
    label = QLabel(title)
    label.setObjectName("dashboardRowTitle")
    label.setWordWrap(True)
    sub = QLabel(subtitle)
    sub.setObjectName("dashboardRowSubtitle")
    texts.addWidget(label)
    texts.addWidget(sub)
    layout.addWidget(bubble)
    layout.addLayout(texts, 1)
    return row


def _replace_chart(layout: QVBoxLayout, labels: list[str], values: list[int]) -> None:
    _clear_layout(layout)
    layout.addWidget(SalesLineChart(labels, values))


def _clear_layout(layout: QVBoxLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget:
            widget.setParent(None)
            widget.deleteLater()


def _shorten(value: str, maximum: int = 58) -> str:
    cleaned = " ".join(value.split())
    return cleaned if len(cleaned) <= maximum else f"{cleaned[:maximum - 1]}…"


def _number(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def _cdf(value: int) -> str:
    return f"{_number(value)} CDF"
