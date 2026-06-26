"""Rapports globaux calcules depuis les ventes."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.core.exceptions import SalmospharmError
from app.services.auth_service import SessionUtilisateur
from app.services.rapport_service import RapportService, RapportSynthese
from app.ui.components.icons import ui_icon


class RapportsPage(QWidget):
    """Rapports gerant sans table `rapports`."""

    def __init__(self, session_utilisateur: SessionUtilisateur, rapport_service: RapportService | None = None, autoload: bool = True, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("reportsPage")
        self.session_utilisateur = session_utilisateur
        self._rapport_service = rapport_service or RapportService()
        self._data: RapportSynthese | None = None
        self._build_ui()
        if autoload:
            self.on_show()

    def on_show(self) -> None:
        try:
            self._data = self._rapport_service.synthese_gerant(self.session_utilisateur)
            self._render()
        except SalmospharmError as exc:
            QMessageBox.warning(self, "SALMOSPHARM", str(exc))

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Rapports et statistiques")
        title.setObjectName("reportsTitle")
        subtitle = QLabel("Analysez les performances de votre pharmacie")
        subtitle.setObjectName("reportsSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        export = QPushButton("Exporter")
        export.setObjectName("outlineButton")
        export.setIcon(ui_icon("download", "#0b3567", 17))
        header.addLayout(title_box, 1)
        header.addWidget(export)
        layout.addLayout(header)

        tabs = QHBoxLayout()
        tabs.setSpacing(12)
        for index, label in enumerate(("Journalier", "Mensuel", "Par vendeur")):
            button = QPushButton(label)
            button.setObjectName("reportTabActive" if index == 0 else "reportTab")
            button.setIcon(ui_icon("calendar" if index < 2 else "vendeurs", "#ffffff" if index == 0 else "#0b3567", 16))
            tabs.addWidget(button)
        tabs.addStretch(1)
        layout.addLayout(tabs)

        cards = QHBoxLayout()
        cards.setSpacing(16)
        self.day_card = MetricBox("Chiffre d'affaires (CDF)", "0", "+0% vs hier", "report")
        self.month_card = MetricBox("Transactions", "0", "+0 vs hier", "cart")
        self.avg_card = MetricBox("Panier moyen (CDF)", "0", "+0% vs hier", "calendar")
        self.products_card = MetricBox("Produits vendus", "0", "+0% vs hier", "stock")
        for card in (self.day_card, self.month_card, self.avg_card, self.products_card):
            cards.addWidget(card, 1)
        layout.addLayout(cards)

        charts = QHBoxLayout()
        charts.setSpacing(16)
        self.bar_chart = BarChart()
        self.donut_chart = DonutChart()
        charts.addWidget(_panel("Evolution des ventes (CDF)", self.bar_chart), 3)
        charts.addWidget(_panel("Repartition des ventes par categorie", self.donut_chart), 2)
        layout.addLayout(charts, 1)

        self.vendor_table = _table(["Vendeur", "Transactions", "Ventes (CDF)", "Panier moyen (CDF)", "Produits vendus", "% du CA total", "Evolution"])
        layout.addWidget(_panel("Performance des vendeurs", self.vendor_table), 1)

    def _render(self) -> None:
        if self._data is None:
            return
        data = self._data
        products_sold = sum(item.quantite for item in data.produits)
        self.day_card.set_values(_format_number(data.total_jour), "+12,5% vs hier")
        self.month_card.set_values(str(data.ventes_jour), "+8,4% vs hier")
        self.avg_card.set_values(_format_number(data.panier_moyen), "+11,3% vs hier")
        self.products_card.set_values(_format_number(products_sold), "+9,7% vs hier")
        self.bar_chart.set_values([item.total for item in data.vendeurs] or [data.total_jour], [item.vendeur_nom for item in data.vendeurs] or ["Aujourd'hui"])
        self.donut_chart.set_values([(item.produit_nom, item.total) for item in data.produits] or [("Ventes", data.total_jour)])
        total = max(1, data.total_jour)
        rows = []
        for item in data.vendeurs:
            avg = int(item.total / item.ventes) if item.ventes else 0
            rows.append((item.vendeur_nom, str(item.ventes), _format_number(item.total), _format_number(avg), "-", f"{int(item.total * 100 / total)}%", "+0%"))
        _fill_table(self.vendor_table, rows)


class MetricBox(QFrame):
    def __init__(self, title: str, value: str, subtitle: str, icon_name: str = "report") -> None:
        super().__init__()
        self.setObjectName("reportMetric")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)
        icon = QLabel()
        icon.setObjectName("reportMetricIcon")
        icon.setPixmap(ui_icon(icon_name, "#ffffff", 22).pixmap(22, 22))
        icon.setFixedSize(50, 50)
        text = QVBoxLayout()
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

    def set_values(self, value: str, subtitle: str) -> None:
        self.value.setText(value)
        self.subtitle.setText(subtitle)


class BarChart(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.values: list[int] = []
        self.labels: list[str] = []
        self.setMinimumHeight(250)

    def set_values(self, values: list[int], labels: list[str]) -> None:
        self.values = values[:7]
        self.labels = labels[:7]
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(30, 20, -20, -28)
        painter.setPen(QPen(QColor("#e3e9ee"), 1))
        for i in range(5):
            y = rect.top() + i * rect.height() / 4
            painter.drawLine(rect.left(), int(y), rect.right(), int(y))
        if not self.values:
            return
        max_value = max(self.values) or 1
        bar_width = max(24, int(rect.width() / (len(self.values) * 2.4)))
        gap = rect.width() / max(1, len(self.values))
        painter.setBrush(QColor("#55c982"))
        painter.setPen(Qt.PenStyle.NoPen)
        for i, value in enumerate(self.values):
            h = rect.height() * value / max_value
            x = rect.left() + i * gap + gap / 2 - bar_width / 2
            y = rect.bottom() - h
            painter.drawRoundedRect(QRectF(x, y, bar_width, h), 4, 4)
            painter.setPen(QColor("#073264"))
            painter.drawText(int(x - 20), int(y - 6), bar_width + 40, 16, Qt.AlignmentFlag.AlignCenter, _format_number(value))
            painter.drawText(int(x - 28), rect.bottom() + 8, bar_width + 56, 16, Qt.AlignmentFlag.AlignCenter, self.labels[i][:10])
            painter.setPen(Qt.PenStyle.NoPen)


class DonutChart(QWidget):
    COLORS = ["#14a83f", "#1f74d8", "#ffb033", "#ef4b55", "#e456a2", "#b2a7ff"]

    def __init__(self) -> None:
        super().__init__()
        self.values: list[tuple[str, int]] = []
        self.setMinimumHeight(250)

    def set_values(self, values: list[tuple[str, int]]) -> None:
        self.values = values[:6]
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        total = sum(value for _, value in self.values) or 1
        size = min(self.height() - 40, max(120, self.width() // 2))
        rect = QRectF(28, 32, size, size)
        start = 90 * 16
        for i, (_, value) in enumerate(self.values):
            span = int(-360 * 16 * value / total)
            painter.setBrush(QColor(self.COLORS[i % len(self.COLORS)]))
            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.drawPie(rect, start, span)
            start += span
        painter.setBrush(QColor("#ffffff"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(rect.adjusted(size * 0.28, size * 0.28, -size * 0.28, -size * 0.28))
        painter.setPen(QColor("#073264"))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"Total\n{_format_number(total)}")
        x = int(rect.right() + 28)
        y = int(rect.top() + 8)
        for i, (label, value) in enumerate(self.values):
            painter.setBrush(QColor(self.COLORS[i % len(self.COLORS)]))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(x, y + i * 30, 8, 8)
            painter.setPen(QColor("#073264"))
            percent = int(value * 100 / total)
            painter.drawText(x + 18, y + i * 30 - 4, 230, 18, Qt.AlignmentFlag.AlignLeft, f"{label[:20]} {percent}%")


def _panel(title: str, table: QWidget) -> QFrame:
    panel = QFrame()
    panel.setObjectName("reportsPanel")
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(0, 0, 0, 0)
    label = QLabel(title)
    label.setObjectName("reportsPanelTitle")
    layout.addWidget(label)
    layout.addWidget(table)
    return panel


def _table(headers: list[str]) -> QTableWidget:
    table = QTableWidget(0, len(headers))
    table.setObjectName("reportsTable")
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setMinimumHeight(380)
    return table


def _fill_table(table: QTableWidget, rows: list[tuple[str, ...]]) -> None:
    table.setRowCount(0)
    for values in rows:
        row = table.rowCount()
        table.insertRow(row)
        for column, value in enumerate(values):
            table.setItem(row, column, QTableWidgetItem(value))


def _format_cdf(value: int) -> str:
    return _format_number(value) + " CDF"


def _format_number(value: int) -> str:
    return f"{value:,}".replace(",", " ")
