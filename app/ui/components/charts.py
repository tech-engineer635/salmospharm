"""Graphiques Qt Charts reutilisables pour les tableaux de bord."""

from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QLineSeries,
    QPieSeries,
    QValueAxis,
)
from PySide6.QtCore import QMargins, QPointF, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QLabel


INK = QColor("#073264")
MUTED = QColor("#65758b")
GRID = QColor("#e3e9ee")
GREEN = QColor("#16a34a")


def _base_chart() -> QChart:
    chart = QChart()
    chart.setFont(QFont("Segoe UI", 9))
    chart.setAnimationOptions(QChart.AnimationOption.NoAnimation)
    chart.setBackgroundVisible(False)
    chart.setPlotAreaBackgroundVisible(False)
    chart.setMargins(QMargins(6, 6, 6, 2))
    chart.legend().hide()
    return chart


class SalesLineChart(QChartView):
    """Courbe de ventes avec zone legere et axes categoriels."""

    def __init__(self, labels: Sequence[str], values: Sequence[float]) -> None:
        self._chart = _base_chart()
        super().__init__(self._chart)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setStyleSheet("background: transparent; border: none;")
        self.setMinimumHeight(260)
        self.set_values(labels, values)

    def set_values(self, labels: Sequence[str], values: Sequence[float]) -> None:
        self._chart.removeAllSeries()
        for axis in tuple(self._chart.axes()):
            self._chart.removeAxis(axis)

        safe_values = list(values) or [0.0]
        safe_labels = list(labels) or [""]
        maximum = max(safe_values)
        divisor = 1_000_000 if maximum >= 1_000_000 else (1_000 if maximum >= 1_000 else 1)
        scaled_values = [value / divisor for value in safe_values]

        line = QLineSeries()
        line.setPointsVisible(True)
        for index, value in enumerate(scaled_values):
            line.append(QPointF(index, float(value)))
        line.setPen(QPen(GREEN, 3))
        self._chart.addSeries(line)

        x_axis = QBarCategoryAxis()
        x_axis.append(safe_labels)
        x_axis.setLabelsColor(MUTED)
        x_axis.setLabelsFont(QFont("Segoe UI", 8))
        x_axis.setGridLineColor(GRID)
        x_axis.setLineVisible(False)

        y_axis = QValueAxis()
        y_axis.setRange(0.0, max(1.0, max(scaled_values) * 1.15))
        y_axis.setTickCount(5)
        if divisor == 1_000_000:
            y_axis.setLabelFormat("%.1fM")
        elif divisor == 1_000:
            y_axis.setLabelFormat("%.0fK")
        y_axis.setLabelsVisible(True)
        y_axis.setLabelsFont(QFont("Segoe UI", 8))
        y_axis.setGridLineColor(GRID)
        y_axis.setLineVisible(False)

        self._chart.addAxis(x_axis, Qt.AlignmentFlag.AlignBottom)
        self._chart.addAxis(y_axis, Qt.AlignmentFlag.AlignLeft)
        line.attachAxis(x_axis)
        line.attachAxis(y_axis)


class SalesBarChart(QChartView):
    """Histogramme des ventes, avec etiquettes de valeurs."""

    def __init__(self) -> None:
        self._chart = _base_chart()
        super().__init__(self._chart)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setStyleSheet("background: transparent; border: none;")
        self.setMinimumHeight(230)
        self.setAccessibleName("Evolution des ventes")
        self._value_labels: list[QLabel] = []
        self._values: list[int] = []
        self._axis_maximum = 1.0
        self._divisor = 1.0
        self._chart.plotAreaChanged.connect(lambda _rect: self._position_value_labels())
        self.set_values([0], [""])

    def set_values(self, values: Sequence[int], labels: Sequence[str]) -> None:
        self._chart.removeAllSeries()
        for axis in tuple(self._chart.axes()):
            self._chart.removeAxis(axis)

        safe_values = [max(0, int(value)) for value in list(values)[:12]] or [0]
        safe_labels = [str(label)[:12] for label in list(labels)[:7]] or [""]
        safe_values = safe_values[: len(safe_labels)]
        maximum = max(safe_values) or 1
        self._divisor = 1_000_000 if maximum >= 1_000_000 else (1_000 if maximum >= 1_000 else 1)
        chart_values = [value / self._divisor for value in safe_values]
        self._axis_maximum = (max(chart_values) or 1) * 1.24
        self._values = safe_values
        bar_set = QBarSet("Ventes (CDF)")
        bar_set.append(chart_values)
        bar_set.setColor(QColor("#55c982"))
        bar_set.setBorderColor(QColor("#55c982"))

        series = QBarSeries()
        series.append(bar_set)
        series.setBarWidth(0.48)
        series.setLabelsVisible(False)
        self._chart.addSeries(series)

        x_axis = QBarCategoryAxis()
        x_axis.append(safe_labels)
        x_axis.setLabelsColor(MUTED)
        x_axis.setLabelsFont(QFont("Segoe UI", 8))
        x_axis.setGridLineVisible(False)
        x_axis.setLineVisible(False)

        y_axis = QValueAxis()
        y_axis.setRange(0, self._axis_maximum)
        y_axis.setTickCount(5)
        if self._divisor == 1_000_000:
            y_axis.setLabelFormat("%.1fM")
        elif self._divisor == 1_000:
            y_axis.setLabelFormat("%.0fK")
        else:
            y_axis.setLabelFormat("%.0f")
        y_axis.setLabelsColor(MUTED)
        y_axis.setLabelsFont(QFont("Segoe UI", 8))
        y_axis.setGridLineColor(GRID)
        y_axis.setLineVisible(False)

        self._chart.addAxis(x_axis, Qt.AlignmentFlag.AlignBottom)
        self._chart.addAxis(y_axis, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(x_axis)
        series.attachAxis(y_axis)
        self._rebuild_value_labels()
        QTimer.singleShot(0, self._position_value_labels)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        QTimer.singleShot(0, self._position_value_labels)

    def _rebuild_value_labels(self) -> None:
        for label in self._value_labels:
            label.hide()
            label.deleteLater()
        self._value_labels = []
        for value in self._values:
            label = QLabel(_format_number(value), self.viewport())
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(
                "background: transparent; color: #073264; font: 700 8px 'Segoe UI';"
            )
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            label.setAccessibleName(f"Ventes {_format_number(value)} CDF")
            label.show()
            self._value_labels.append(label)

    def _position_value_labels(self) -> None:
        if not self._value_labels:
            return
        plot = self._chart.plotArea()
        count = len(self._value_labels)
        for index, (label, value) in enumerate(zip(self._value_labels, self._values)):
            x = plot.left() + plot.width() * (index + 0.5) / count
            scaled = value / self._divisor
            y = plot.bottom() - plot.height() * scaled / self._axis_maximum
            label.setGeometry(int(x - 48), max(0, int(y - 23)), 96, 18)
            label.raise_()


class DonutChart(QChartView):
    """Diagramme annulaire avec legende et total central."""

    COLORS = ("#14a83f", "#1f74d8", "#ffb033", "#ef4b55", "#e456a2", "#b2a7ff")

    def __init__(self) -> None:
        self._chart = _base_chart()
        super().__init__(self._chart)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setStyleSheet("background: transparent; border: none;")
        self.setMinimumHeight(230)
        self.setAccessibleName("Repartition des ventes par categorie")
        self._legend_rows: list[tuple[QLabel, QLabel]] = []
        self._center = QLabel(self.viewport())
        self._center.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._center.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._center.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._center.setStyleSheet("color: #073264; font-size: 12px; font-weight: 700; background: transparent;")
        self.set_values([("Ventes", 0)])

    def set_values(self, values: Sequence[tuple[str, int]]) -> None:
        self._chart.removeAllSeries()
        entries = [(str(label), max(0, int(value))) for label, value in list(values)[:6]]
        if not entries:
            entries = [("Ventes", 0)]
        total = sum(value for _, value in entries)

        series = QPieSeries()
        series.setHoleSize(0.56)
        series.setPieSize(0.66)
        series.setHorizontalPosition(0.25)
        legend_entries: list[tuple[str, str]] = []
        for index, (label, value) in enumerate(entries):
            percent = value * 100 / total if total else 0
            color = self.COLORS[index % len(self.COLORS)]
            legend = f"{label[:25]}  {_format_number(value)} ({percent:.1f}%)"
            slice_ = series.append(legend, value or (1 if len(entries) == 1 else 0))
            slice_.setColor(QColor(color))
            slice_.setBorderColor(QColor("#ffffff"))
            slice_.setBorderWidth(2)
            slice_.setLabelVisible(False)
            legend_entries.append((color, legend))
        self._chart.addSeries(series)
        self._chart.legend().hide()
        self._rebuild_legend(legend_entries)
        self._center.setText(f"Total\n{_format_number(total)}\nCDF")
        self._position_overlays()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._position_overlays()

    def _rebuild_legend(self, entries: Sequence[tuple[str, str]]) -> None:
        for swatch, label in self._legend_rows:
            swatch.hide()
            label.hide()
            swatch.deleteLater()
            label.deleteLater()
        self._legend_rows = []
        for color, text in entries:
            swatch = QLabel(self.viewport())
            swatch.setStyleSheet(f"background: {color}; border-radius: 3px;")
            swatch.setFixedSize(7, 7)
            label = QLabel(text, self.viewport())
            label.setStyleSheet(
                "background: transparent; color: #073264; font: 7px 'Segoe UI';"
            )
            label.setToolTip(text)
            label.setAccessibleName(text)
            swatch.show()
            label.show()
            self._legend_rows.append((swatch, label))

    def _position_overlays(self) -> None:
        diameter = min(92, max(64, self.height() // 3))
        center_x = int(self.width() * 0.25)
        center_y = int(self.height() * 0.52)
        self._center.setGeometry(center_x - diameter // 2, center_y - diameter // 2, diameter, diameter)
        self._center.raise_()
        legend_x = int(self.width() * 0.53)
        start_y = max(24, int((self.height() - len(self._legend_rows) * 25) / 2))
        label_width = max(120, self.width() - legend_x - 8)
        for index, (swatch, label) in enumerate(self._legend_rows):
            y = start_y + index * 25
            swatch.move(legend_x, y + 5)
            label.setGeometry(legend_x + 14, y, label_width - 14, 18)
            swatch.raise_()
            label.raise_()


class ProgressDonutChart(QChartView):
    """Anneau de progression compact utilise sur le dashboard vendeur."""

    def __init__(self, progress: int) -> None:
        self._chart = _base_chart()
        super().__init__(self._chart)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setStyleSheet("background: transparent; border: none;")
        self.setFixedSize(126, 126)
        self._label = QLabel(self.viewport())
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._label.setStyleSheet("color: #16a33a; font-weight: 700; background: transparent;")
        self._label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.set_progress(progress)

    def set_progress(self, progress: int) -> None:
        progress = min(100, max(0, int(progress)))
        self._chart.removeAllSeries()
        series = QPieSeries()
        series.setHoleSize(0.72)
        series.setPieSize(0.9)
        done = series.append("Realise", progress)
        done.setColor(GREEN)
        remaining = series.append("Restant", 100 - progress)
        remaining.setColor(QColor("#e8edf1"))
        for slice_ in series.slices():
            slice_.setBorderWidth(0)
        self._chart.addSeries(series)
        self._label.setText(f"{progress}%")
        self._label.setGeometry(0, 0, self.width(), self.height())
        self._label.raise_()


def _format_number(value: int) -> str:
    return f"{value:,}".replace(",", " ")
