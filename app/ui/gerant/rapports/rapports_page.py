"""Rapports globaux calcules depuis les ventes."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import QDate, QSize, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDateEdit,
    QFileDialog,
    QFrame,
    QHeaderView,
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
from app.core.paths import get_exports_dir
from app.services.auth_service import SessionUtilisateur
from app.services.rapport_service import RapportService, RapportSynthese
from app.ui.components.charts import DonutChart, SalesBarChart
from app.ui.components.icons import ui_icon


class RapportsPage(QWidget):
    """Rapports gerant sans table `rapports`."""

    def __init__(self, session_utilisateur: SessionUtilisateur, rapport_service: RapportService | None = None, autoload: bool = True, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("reportsPage")
        self.session_utilisateur = session_utilisateur
        self._rapport_service = rapport_service or RapportService()
        self._data: RapportSynthese | None = None
        self._mode = "JOURNALIER"
        self._show_all_sellers = False
        self._tab_buttons: dict[str, QPushButton] = {}
        self._build_ui()
        if autoload:
            self.on_show()

    def on_show(self) -> None:
        self._charger_rapport()

    def _charger_rapport(self) -> None:
        try:
            self._data = self._rapport_service.rapport_periode(
                self.session_utilisateur,
                date_debut=self.start_date.date().toPython(),
                date_fin=self.end_date.date().toPython(),
                mode=self._mode,
            )
            self._render()
        except SalmospharmError as exc:
            QMessageBox.warning(self, "SALMOSPHARM", str(exc))

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        header = QHBoxLayout()
        header.setSpacing(18)
        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        title = QLabel("Rapports et statistiques")
        title.setObjectName("reportsTitle")
        subtitle = QLabel("Analysez les performances de votre pharmacie")
        subtitle.setObjectName("reportsSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box, 1)

        period = QFrame()
        period.setObjectName("reportsPeriod")
        period_layout = QHBoxLayout(period)
        period_layout.setContentsMargins(12, 0, 10, 0)
        period_layout.setSpacing(8)
        period_icon = QLabel()
        period_icon.setPixmap(ui_icon("calendar", "#0b3567", 18).pixmap(18, 18))
        period_layout.addWidget(period_icon)
        today = date.today()
        self.start_date = _date_edit(today - timedelta(days=6), "Date de debut du rapport")
        self.end_date = _date_edit(today, "Date de fin du rapport")
        arrow = QLabel("→")
        arrow.setObjectName("reportsPeriodArrow")
        arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        period_layout.addWidget(self.start_date)
        period_layout.addWidget(arrow)
        period_layout.addWidget(self.end_date)
        self.start_date.dateChanged.connect(lambda _value: self._charger_rapport())
        self.end_date.dateChanged.connect(lambda _value: self._charger_rapport())
        header.addWidget(period)

        self.export_button = QPushButton("Exporter")
        self.export_button.setObjectName("reportsExportButton")
        self.export_button.setIcon(ui_icon("download", "#0b3567", 17))
        self.export_button.setIconSize(QSize(17, 17))
        self.export_button.setAccessibleName("Exporter le rapport en Excel")
        self.export_button.clicked.connect(self._exporter)
        header.addWidget(self.export_button)
        layout.addLayout(header)

        tabs = QHBoxLayout()
        tabs.setSpacing(12)
        for mode, label, icon_name in (
            ("JOURNALIER", "Journalier", "calendar"),
            ("MENSUEL", "Mensuel", "calendar"),
            ("VENDEUR", "Par vendeur", "vendeurs"),
        ):
            button = QPushButton(label)
            button.setCheckable(True)
            button.setAccessibleName(f"Afficher le rapport {label.lower()}")
            button.clicked.connect(lambda _checked=False, value=mode: self._changer_mode(value))
            button.setProperty("iconName", icon_name)
            self._tab_buttons[mode] = button
            tabs.addWidget(button)
        tabs.addStretch(1)
        layout.addLayout(tabs)
        self._sync_tabs()

        cards = QHBoxLayout()
        cards.setSpacing(16)
        self.day_card = MetricBox("Chiffre d'affaires (CDF)", "0", "+0% vs periode precedente", "report", "green")
        self.month_card = MetricBox("Transactions", "0", "+0% vs periode precedente", "cart", "blue")
        self.avg_card = MetricBox("Panier moyen (CDF)", "0", "+0% vs periode precedente", "calendar", "green")
        self.products_card = MetricBox("Produits vendus", "0", "+0% vs periode precedente", "stock", "blue")
        for card in (self.day_card, self.month_card, self.avg_card, self.products_card):
            cards.addWidget(card, 1)
        layout.addLayout(cards)

        charts = QHBoxLayout()
        charts.setSpacing(16)
        self.bar_chart = SalesBarChart()
        self.donut_chart = DonutChart()
        self.chart_panel, self.chart_title = _panel("Evolution des ventes (CDF)", self.bar_chart, "7 derniers jours")
        self.donut_panel, _ = _panel("Repartition des ventes par categorie", self.donut_chart)
        charts.addWidget(self.chart_panel, 3)
        charts.addWidget(self.donut_panel, 2)
        layout.addLayout(charts, 1)

        self.vendor_table = _table(["Vendeur", "Transactions", "Ventes (CDF)", "Panier moyen (CDF)", "Produits vendus", "% du CA total", "Evolution"])
        self.vendor_panel, _ = _panel("Performance des vendeurs", self.vendor_table)
        self.show_all_button = QPushButton("Voir tout")
        self.show_all_button.setObjectName("reportsSeeAll")
        self.show_all_button.clicked.connect(self._toggle_all_sellers)
        self.vendor_panel.layout().itemAt(0).layout().addWidget(self.show_all_button)
        layout.addWidget(self.vendor_panel, 1)

        self.empty_label = QLabel("Aucune vente validee sur cette periode.")
        self.empty_label.setObjectName("reportsEmptyState")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setAccessibleName("Aucune donnee de rapport")
        self.empty_label.hide()
        layout.addWidget(self.empty_label)

    def _render(self) -> None:
        if self._data is None:
            return
        data = self._data
        self.day_card.set_values(_format_number(data.total_jour), data.tendance_ca)
        self.month_card.set_values(str(data.ventes_jour), data.tendance_transactions)
        self.avg_card.set_values(_format_number(data.panier_moyen), data.tendance_panier)
        self.products_card.set_values(_format_number(data.produits_vendus), data.tendance_produits)

        if self._mode == "VENDEUR":
            self.chart_title.setText("Ventes par vendeur (CDF)")
            values = [item.total for item in data.vendeurs]
            labels = [item.vendeur_nom for item in data.vendeurs]
        else:
            self.chart_title.setText("Evolution des ventes (CDF)")
            values = [item.total for item in data.evolution or []]
            labels = [_date_courte(item.date_vente) for item in data.evolution or []]
        self.bar_chart.set_values(values or [0], labels or ["-"])
        self.donut_chart.set_values(
            [(item.categorie_nom, item.total) for item in data.categories or []]
            or [("Aucune vente", 0)]
        )

        visible_sellers = data.vendeurs if self._show_all_sellers else data.vendeurs[:4]
        rows = [
            (
                item.vendeur_nom,
                str(item.ventes),
                _format_number(item.total),
                _format_number(item.panier_moyen),
                _format_number(item.produits_vendus),
                _format_percent(item.part_ca),
                _format_trend(item.evolution),
            )
            for item in visible_sellers
        ]
        rows.append(
            (
                "Total",
                str(data.ventes_jour),
                _format_number(data.total_jour),
                _format_number(data.panier_moyen),
                _format_number(data.produits_vendus),
                "100%" if data.total_jour else "0%",
                _format_trend(data.tendance_ca),
            )
        )
        _fill_table(self.vendor_table, rows, total_row=True)
        self.show_all_button.setVisible(len(data.vendeurs) > 4)
        self.show_all_button.setText("Reduire" if self._show_all_sellers else "Voir tout")
        self.empty_label.setVisible(data.ventes_jour == 0)
        self.export_button.setEnabled(data.ventes_jour > 0)

    def _changer_mode(self, mode: str) -> None:
        self._mode = mode
        today = date.today()
        self.start_date.blockSignals(True)
        self.end_date.blockSignals(True)
        if mode == "JOURNALIER":
            self.start_date.setDate(QDate(today.year, today.month, today.day).addDays(-6))
            self.end_date.setDate(QDate(today.year, today.month, today.day))
        elif mode == "MENSUEL":
            self.start_date.setDate(QDate(today.year, today.month, 1))
            self.end_date.setDate(QDate(today.year, today.month, today.day))
        self.start_date.blockSignals(False)
        self.end_date.blockSignals(False)
        self._sync_tabs()
        self._charger_rapport()

    def _sync_tabs(self) -> None:
        for mode, button in self._tab_buttons.items():
            active = mode == self._mode
            button.setChecked(active)
            button.setObjectName("reportTabActive" if active else "reportTab")
            icon_name = button.property("iconName")
            button.setIcon(ui_icon(icon_name, "#ffffff" if active else "#0b3567", 16))
            button.style().unpolish(button)
            button.style().polish(button)

    def _toggle_all_sellers(self) -> None:
        self._show_all_sellers = not self._show_all_sellers
        self._render()

    def _exporter(self) -> None:
        if self._data is None:
            return
        debut = self._data.date_debut or date.today()
        fin = self._data.date_fin or debut
        default_name = f"rapport_{self._mode.lower()}_{debut.isoformat()}_{fin.isoformat()}.xlsx"
        destination, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter le rapport Excel",
            str(get_exports_dir() / default_name),
            "Classeur Excel (*.xlsx)",
        )
        if not destination:
            return
        try:
            path = self._rapport_service.exporter_excel(
                self.session_utilisateur, self._data, Path(destination)
            )
        except SalmospharmError as exc:
            QMessageBox.warning(self, "SALMOSPHARM", str(exc))
            return
        QMessageBox.information(
            self, "SALMOSPHARM", f"Rapport exporte avec succes :\n{path}"
        )


class MetricBox(QFrame):
    def __init__(
        self,
        title: str,
        value: str,
        subtitle: str,
        icon_name: str = "report",
        variant: str = "green",
    ) -> None:
        super().__init__()
        self.setObjectName("reportMetric")
        self.setAccessibleName(title)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)
        icon = QLabel()
        icon.setObjectName("reportMetricIconBlue" if variant == "blue" else "reportMetricIcon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setPixmap(ui_icon(icon_name, "#ffffff", 22).pixmap(22, 22))
        icon.setFixedSize(50, 50)
        text = QVBoxLayout()
        text.setSpacing(3)
        label = QLabel(title)
        label.setObjectName("reportMetricTitle")
        self.value = QLabel(value)
        self.value.setObjectName("reportMetricValue")
        self.subtitle = QLabel(subtitle)
        self.subtitle.setObjectName("reportMetricSubtitle")
        text.addWidget(label)
        text.addWidget(self.value)
        text.addWidget(self.subtitle)
        layout.addWidget(icon)
        layout.addLayout(text, 1)

    def set_values(self, value: str, trend: float) -> None:
        self.value.setText(value)
        self.subtitle.setText(f"{_format_trend(trend)} vs periode precedente")
        self.subtitle.setProperty("trendState", "negative" if trend < 0 else "positive")
        self.subtitle.style().unpolish(self.subtitle)
        self.subtitle.style().polish(self.subtitle)


def _panel(title: str, table: QWidget, context: str = "") -> tuple[QFrame, QLabel]:
    panel = QFrame()
    panel.setObjectName("reportsPanel")
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(16, 12, 16, 10)
    layout.setSpacing(6)
    header = QHBoxLayout()
    label = QLabel(title)
    label.setObjectName("reportsPanelTitle")
    header.addWidget(label)
    header.addStretch(1)
    if context:
        context_label = QLabel(context)
        context_label.setObjectName("reportsChartContext")
        header.addWidget(context_label)
    layout.addLayout(header)
    layout.addWidget(table)
    return panel, label


def _table(headers: list[str]) -> QTableWidget:
    table = QTableWidget(0, len(headers))
    table.setObjectName("reportsTable")
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    table.setShowGrid(False)
    table.setAlternatingRowColors(False)
    table.setMinimumHeight(185)
    table.setMaximumHeight(250)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
    return table


def _fill_table(
    table: QTableWidget,
    rows: list[tuple[str, ...]],
    *,
    total_row: bool = False,
) -> None:
    table.setRowCount(0)
    for row_index, values in enumerate(rows):
        row = table.rowCount()
        table.insertRow(row)
        table.setRowHeight(row, 32)
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            if column == 0 and not (total_row and row_index == len(rows) - 1):
                item.setIcon(ui_icon("user", "#607a96", 15))
            if column > 0:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if total_row and row_index == len(rows) - 1:
                item.setForeground(QColor("#0a8f35"))
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            table.setItem(row, column, item)


def _date_edit(value: date, accessible_name: str) -> QDateEdit:
    editor = QDateEdit(QDate(value.year, value.month, value.day))
    editor.setObjectName("reportsDateEdit")
    editor.setDisplayFormat("dd MMM yyyy")
    editor.setCalendarPopup(True)
    editor.setAccessibleName(accessible_name)
    editor.setKeyboardTracking(False)
    return editor


def _date_courte(value: date) -> str:
    mois = (
        "jan",
        "fev",
        "mar",
        "avr",
        "mai",
        "juin",
        "juil",
        "aout",
        "sep",
        "oct",
        "nov",
        "dec",
    )
    return f"{value.day} {mois[value.month - 1]}"


def _format_percent(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",")


def _format_trend(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.1f}%".replace(".", ",")


def _format_cdf(value: int) -> str:
    return _format_number(value) + " CDF"


def _format_number(value: int) -> str:
    return f"{value:,}".replace(",", " ")
