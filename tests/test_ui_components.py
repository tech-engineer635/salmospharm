import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCharts import QChartView
from PySide6.QtWidgets import QApplication

from app.ui.components.charts import DonutChart, ProgressDonutChart, SalesBarChart, SalesLineChart
from app.ui.components.icons import ui_icon


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_ui_icon_retourne_une_icone_qtawesome_visible():
    _app()

    icon = ui_icon("dashboard", "#0b3567", 24)

    assert not icon.isNull()
    assert not icon.pixmap(24, 24).isNull()


def test_tous_les_graphiques_utilisent_qtcharts():
    _app()

    line = SalesLineChart(["08h", "10h"], [0.2, 0.8])
    bars = SalesBarChart()
    donut = DonutChart()
    progress = ProgressDonutChart(57)
    bars.set_values([100, 200], ["Lun", "Mar"])
    donut.set_values([("Medicaments", 100), ("Soins", 50)])

    assert all(isinstance(widget, QChartView) for widget in (line, bars, donut, progress))
    assert line.chart().series()
    assert bars.chart().series()
    assert donut.chart().series()
    assert progress.chart().series()
