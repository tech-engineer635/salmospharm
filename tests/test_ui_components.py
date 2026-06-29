import os
from datetime import date

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCharts import QChartView
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QComboBox, QDateEdit, QLabel, QLineEdit, QWidget

from app.core.constants import ROLE_GERANT
from app.services.auth_service import SessionUtilisateur
from app.services.rapport_service import (
    RapportCategorieItem,
    RapportEvolutionItem,
    RapportSynthese,
    RapportVendeurItem,
)
from app.ui.components.charts import DonutChart, ProgressDonutChart, SalesBarChart, SalesLineChart
from app.ui.components.icons import ui_icon
from app.ui.components.field_contrast import appliquer_contraste_champs
from app.ui.gerant.rapports import RapportsPage


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


def test_contraste_des_champs_reste_lisible_actif_et_desactive():
    _app()
    root = QWidget()
    field = QLineEdit(root)
    label = QLabel("Nom du champ", root)
    field.setPlaceholderText("Texte indicatif")

    appliquer_contraste_champs(root)
    palette = field.palette()

    assert palette.color(QPalette.ColorRole.Text).name() == "#17324d"
    assert palette.color(QPalette.ColorRole.PlaceholderText).name() == "#66788a"
    assert (
        palette.color(
            QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text
        ).name()
        == "#526579"
    )
    assert label.palette().color(QPalette.ColorRole.WindowText).name() == "#17324d"


def test_contraste_du_popup_dropdown_reste_lisible():
    _app()
    root = QWidget()
    combo = QComboBox(root)
    combo.addItems(["Toutes les alertes actives", "Non lues"])

    appliquer_contraste_champs(root)
    popup_palette = combo.view().palette()

    assert popup_palette.color(QPalette.ColorRole.Base).name() == "#ffffff"
    assert popup_palette.color(QPalette.ColorRole.Text).name() == "#17324d"
    assert popup_palette.color(QPalette.ColorRole.Highlight).name() == "#0b5fa5"
    assert popup_palette.color(QPalette.ColorRole.HighlightedText).name() == "#ffffff"


def test_page_rapports_utilise_periode_graphiques_et_total_vendeurs():
    app = _app()
    session = SessionUtilisateur(1, "Gerant", "gerant", ROLE_GERANT)
    page = RapportsPage(session, autoload=False)
    page._data = RapportSynthese(
        ventes_jour=2,
        total_jour=3500,
        ventes_mois=2,
        total_mois=3500,
        panier_moyen=1750,
        vendeurs=[
            RapportVendeurItem(
                2,
                "Jean K.",
                2,
                3500,
                produits_vendus=3,
                panier_moyen=1750,
                part_ca=100,
                evolution=12.5,
            )
        ],
        produits=[],
        date_debut=date(2026, 6, 26),
        date_fin=date(2026, 6, 28),
        produits_vendus=3,
        evolution=[
            RapportEvolutionItem(date(2026, 6, 26), 1, 2000),
            RapportEvolutionItem(date(2026, 6, 27), 0, 0),
            RapportEvolutionItem(date(2026, 6, 28), 1, 1500),
        ],
        categories=[
            RapportCategorieItem("Medicaments", 2, 2000),
            RapportCategorieItem("Soins", 1, 1500),
        ],
        tendance_ca=12.5,
    )

    page._render()
    app.processEvents()

    assert len(page.findChildren(QDateEdit)) == 2
    assert isinstance(page.bar_chart, QChartView)
    assert isinstance(page.donut_chart, QChartView)
    assert page.day_card.value.text() == "3 500"
    assert page.vendor_table.item(page.vendor_table.rowCount() - 1, 0).text() == "Total"
    assert page.export_button.isEnabled()
