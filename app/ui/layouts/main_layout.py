"""Layout principal connecte de SALMOSPHARM 133."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractButton,
    QAbstractItemView,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QMainWindow,
    QLineEdit,
    QScrollArea,
    QStackedWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.constants import ROLE_GERANT, ROLE_VENDEUR
from app.services.auth_service import SessionUtilisateur
from app.services.alert_coordinator import AlertCoordinator
from app.ui.components.ticket_preview import TicketPreviewPage
from app.ui.components.field_contrast import appliquer_contraste_champs
from app.ui.gerant.alertes import AlertesPage
from app.ui.gerant.dashboard_page import GerantDashboardPage
from app.ui.gerant.historique import HistoriqueActionsPage, HistoriqueVentesGerantPage
from app.ui.gerant.parametres import BackupPanel
from app.ui.gerant.parametres.settings_panel import (
    GeneralSettingsPanel,
    SecuritySettingsPanel,
)
from app.ui.gerant.produits import ProduitsPage
from app.ui.gerant.rapports import RapportsPage
from app.ui.gerant.stock import StockPage
from app.ui.gerant.vendeurs import VendeursPage
from app.ui.layouts.sidebar import Sidebar
from app.ui.layouts.topbar import Topbar
from app.ui.vendeur.dashboard_page import VendeurDashboardPage
from app.ui.vendeur.historique_ventes import HistoriqueVentesVendeurPage
from app.ui.vendeur.nouvelle_vente import NouvelleVentePage
from app.ui.vendeur.recherche_produit_page import RechercheProduitPage


APP_TITLE = "SALMOSPHARM 133"


class MainWindow(QMainWindow):
    """Fenetre principale apres authentification, sans acces direct a SQLite."""

    deconnexion_demandee = Signal()
    redemarrage_demande = Signal()

    def __init__(
        self,
        session_utilisateur: SessionUtilisateur,
        alert_coordinator: AlertCoordinator | None = None,
    ) -> None:
        super().__init__()
        self.session_utilisateur = session_utilisateur
        self._pages: dict[str, int] = {}
        self._page_widgets: dict[str, QWidget] = {}
        self._alert_coordinator = alert_coordinator
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(1080, 680)
        self.resize(1320, 820)
        self._build_ui()
        self._apply_style()
        self._apply_accessibility()
        appliquer_contraste_champs(self)
        self.navigate("dashboard")

    def toggle_sidebar(self) -> None:
        self.sidebar.setHidden(not self.sidebar.isHidden())

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "sidebar"):
            self.sidebar.setVisible(self.width() >= 1180)
        settings = getattr(self, "_page_widgets", {}).get("parametres")
        if settings is not None and hasattr(settings, "set_compact"):
            settings.set_compact(self.width() < 1200)
        for key in ("dashboard", "vendeurs", "rapports", "alertes"):
            page = getattr(self, "_page_widgets", {}).get(key)
            if page is not None and hasattr(page, "set_compact"):
                page.set_compact(self.width() < 1200)

    def navigate(self, key: str) -> None:
        if key not in self._pages:
            return
        self.content_stack.setCurrentIndex(self._pages[key])
        self.sidebar.set_active(key)
        self.topbar.set_title(self._page_title_for_session(key))
        self.topbar.set_reports_mode(key == "rapports")
        page = self._page_widgets.get(key)
        if page is not None and hasattr(page, "set_compact"):
            page.set_compact(self.width() < 1200)
        if page is not None and hasattr(page, "on_show"):
            page.on_show()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("mainRoot")
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = Sidebar(self.session_utilisateur)
        self.sidebar.navigation_demandee.connect(self.navigate)
        self.sidebar.deconnexion_demandee.connect(self.deconnexion_demandee.emit)
        root_layout.addWidget(self.sidebar)

        workspace = QWidget()
        workspace.setObjectName("workspace")
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)

        self.topbar = Topbar(self.session_utilisateur)
        self.topbar.deconnexion_demandee.connect(self.deconnexion_demandee.emit)
        self.topbar.menu_demande.connect(self.toggle_sidebar)
        self.topbar.recherche_demandee.connect(self._rechercher_produit)
        self.topbar.alertes_demandees.connect(self._ouvrir_alertes)
        if self._alert_coordinator is not None:
            self._alert_coordinator.alerts_updated.connect(self._actualiser_alertes)
        workspace_layout.addWidget(self.topbar)

        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("contentStack")
        workspace_layout.addWidget(self.content_stack, 1)
        root_layout.addWidget(workspace, 1)
        self.setCentralWidget(root)
        self._register_pages()

    def _register_pages(self) -> None:
        if self.session_utilisateur.role == ROLE_GERANT:
            dashboard = GerantDashboardPage(self.session_utilisateur)
            dashboard.voir_tout_demande.connect(self.navigate)
            self._add_page("dashboard", dashboard)
            self._add_page("produits", ProduitsPage(self.session_utilisateur, autoload=False))
            self._add_page("stock", StockPage(self.session_utilisateur, autoload=False))
            nouvelle_vente = NouvelleVentePage(self.session_utilisateur, autoload=False)
            nouvelle_vente.ticket_genere.connect(self._afficher_ticket)
            self._add_page("nouvelle_vente", nouvelle_vente)
            facture_page = TicketPreviewPage(self.session_utilisateur)
            facture_page.retour_demande.connect(lambda: self.navigate("dashboard"))
            self._add_page("factures", facture_page)
            self._add_page("vendeurs", VendeursPage(self.session_utilisateur, autoload=False))
            ventes_page = HistoriqueVentesGerantPage(self.session_utilisateur, autoload=False)
            ventes_page.ticket_demande.connect(self._afficher_ticket)
            historique = HistoriqueActionsPage(self.session_utilisateur, autoload=False)
            self._add_page("ventes", ventes_page)
            self._add_page("historique", historique)
            self._add_page("rapports", RapportsPage(self.session_utilisateur, autoload=False))
            alertes_page = AlertesPage(self.session_utilisateur, autoload=False)
            alertes_page.compteur_change.connect(self.topbar.set_alert_count)
            alertes_page.produit_demande.connect(self._ouvrir_produit)
            alertes_page.navigation_demandee.connect(self.navigate)
            self._add_page("alertes", alertes_page)
            settings = SettingsPage(self.session_utilisateur)
            settings.redemarrage_demande.connect(self.redemarrage_demande.emit)
            self._add_page("parametres", settings)
            return

        if self.session_utilisateur.role == ROLE_VENDEUR:
            dashboard = VendeurDashboardPage(self.session_utilisateur)
            dashboard.voir_tout_demande.connect(self.navigate)
            self._add_page("dashboard", dashboard)
            nouvelle_vente = NouvelleVentePage(self.session_utilisateur, autoload=False)
            nouvelle_vente.ticket_genere.connect(self._afficher_ticket)
            self._add_page("nouvelle_vente", nouvelle_vente)
            facture_page = TicketPreviewPage(self.session_utilisateur)
            facture_page.retour_demande.connect(lambda: self.navigate("nouvelle_vente"))
            self._add_page("factures", facture_page)
            historique = HistoriqueVentesVendeurPage(self.session_utilisateur, autoload=False)
            historique.ticket_demande.connect(self._afficher_ticket)
            self._add_page("historique_ventes", historique)
            self._add_page("produits", RechercheProduitPage(self.session_utilisateur))

    def _add_page(self, key: str, page: QWidget) -> None:
        scroll = QScrollArea()
        scroll.setObjectName("pageScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        container = QWidget()
        container.setObjectName("pageContainer")
        layout = QVBoxLayout(container)
        if key == "vendeurs":
            layout.setContentsMargins(24, 8, 22, 8)
        elif key == "nouvelle_vente":
            layout.setContentsMargins(24, 10, 22, 10)
        elif key in {"ventes", "historique", "historique_ventes", "rapports", "alertes", "factures"}:
            layout.setContentsMargins(24, 14, 22, 14)
        elif key in {"produits", "stock"}:
            layout.setContentsMargins(26, 18, 22, 18)
        else:
            layout.setContentsMargins(28, 26, 28, 26)
        layout.addWidget(page)
        scroll.setWidget(container)
        self._pages[key] = self.content_stack.addWidget(scroll)
        self._page_widgets[key] = page

    def _apply_accessibility(self) -> None:
        """Complete les noms accessibles sans remplacer les libelles metier."""

        for widget in self.findChildren(QWidget):
            if widget.accessibleName():
                continue
            name = ""
            if isinstance(widget, QAbstractButton):
                name = widget.text().strip() or widget.toolTip()
            elif isinstance(widget, QLineEdit):
                name = widget.placeholderText()
            elif isinstance(widget, QComboBox):
                name = widget.currentText()
            elif isinstance(widget, QAbstractItemView):
                name = widget.objectName().replace("_", " ")
            if name:
                widget.setAccessibleName(name)

    def _afficher_ticket(self, ticket: object, message: str) -> None:
        page = self._page_widgets.get("factures")
        if page is not None and hasattr(page, "set_ticket"):
            page.set_ticket(ticket, message)
        self.navigate("factures")

    def _rechercher_produit(self, terme: str) -> None:
        key = "produits"
        self.navigate(key)
        page = self._page_widgets.get(key)
        if page is not None and hasattr(page, "appliquer_recherche"):
            page.appliquer_recherche(terme)
        elif page is not None and hasattr(page, "search_input"):
            page.search_input.setText(terme)
            page.search_input.setFocus()

    def _ouvrir_alertes(self) -> None:
        if self.session_utilisateur.role == ROLE_GERANT:
            self.navigate("alertes")

    def _actualiser_alertes(self) -> None:
        for key in ("alertes", "dashboard"):
            page = self._page_widgets.get(key)
            if page is not None and hasattr(page, "on_show"):
                page.on_show()

    def _ouvrir_produit(self, produit_id: int) -> None:
        self.navigate("produits")
        page = self._page_widgets.get("produits")
        if page is not None and hasattr(page, "selectionner_produit"):
            page.selectionner_produit(produit_id)

    def _page_title_for_session(self, key: str) -> str:
        if self.session_utilisateur.role == ROLE_VENDEUR and key == "dashboard":
            return "Tableau de bord vendeur"
        if self.session_utilisateur.role == ROLE_VENDEUR and key == "produits":
            return "Recherche produit"
        return _page_title(key)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget#mainRoot {
                background-color: #f4f7f8;
                color: #12263a;
                font-family: "Segoe UI";
            }
            QFrame#sidebar {
                background-color: #ffffff;
                border-right: 1px solid #e5ebf0;
            }
            QLabel#sidebarLogo {
                min-height: 190px;
            }
            QScrollArea#sidebarNavScroll {
                background: transparent;
                border: none;
            }
            QScrollArea#sidebarNavScroll QWidget {
                background: transparent;
            }
            QPushButton#navButton,
            QPushButton#logoutButton {
                border: none;
                border-radius: 0;
                color: #132b46;
                font-size: 16px;
                font-weight: 500;
                min-height: 42px;
                padding: 0 34px;
                text-align: left;
            }
            QPushButton#navButton:hover {
                background-color: #f4fbf6;
                color: #0c8e37;
            }
            QPushButton#navButton[active="true"] {
                background-color: #edf9f0;
                color: #108d38;
                font-weight: 800;
                border-left: 5px solid #16a33a;
            }
            QPushButton#logoutButton {
                background-color: transparent;
                color: #132b46;
                padding: 0;
                min-height: 34px;
            }
            QPushButton#logoutButton:hover {
                color: #108d38;
            }
            QPushButton#profileButton {
                background: transparent;
                border: none;
                color: #2d4055;
                font-size: 16px;
                font-weight: 800;
                min-width: 26px;
            }
            QPushButton#profileButton:hover {
                color: #108d38;
            }
            QFrame#userCard {
                background-color: #ffffff;
                border: 1px solid #e6ebf0;
                border-radius: 8px;
                margin: 0 16px;
            }
            QLabel#userAvatar {
                background-color: #edf3f8;
                border-radius: 24px;
                color: #12314f;
                font-size: 24px;
            }
            QLabel#userRoleTitle {
                color: #10243b;
                font-size: 13px;
                font-weight: 900;
            }
            QLabel#userName {
                color: #10243b;
                font-size: 13px;
            }
            QFrame#userSeparator {
                background-color: #e8eef2;
            }
            QWidget#workspace {
                background-color: #fbfdff;
            }
            QFrame#topbar {
                background-color: #fbfdff;
                border-bottom: none;
            }
            QLabel#topbarTitle {
                color: #0b2f4f;
                font-size: 28px;
                font-weight: 900;
            }
            QLabel#topbarSubtitle {
                color: #68778a;
                font-size: 14px;
            }
            QPushButton#menuButton {
                background-color: #ffffff;
                border: 1px solid #edf1f5;
                border-radius: 8px;
                color: #26394f;
                font-size: 20px;
            }
            QLineEdit#topbarSearch {
                background-color: #ffffff;
                border: 1px solid #e3e9ee;
                border-radius: 7px;
                color: #24364a;
                font-size: 13px;
                min-height: 42px;
                padding: 0 16px;
            }
            QLineEdit,
            QSpinBox,
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #dce5eb;
                border-radius: 7px;
                color: #24364a;
                font-size: 13px;
                min-height: 36px;
                padding: 0 10px;
            }
            QLineEdit:focus,
            QSpinBox:focus,
            QComboBox:focus {
                border-color: #16a33a;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #17324d;
                selection-background-color: #0b5fa5;
                selection-color: #ffffff;
                outline: none;
            }
            QCheckBox {
                color: #334e68;
                font-size: 13px;
                font-weight: 700;
                spacing: 8px;
            }
            QPushButton#primaryButton {
                background-color: #108d38;
                border: none;
                border-radius: 7px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 800;
                min-height: 38px;
                padding: 0 16px;
            }
            QPushButton#primaryButton:hover {
                background-color: #0b7831;
            }
            QPushButton#dangerButton {
                background-color: #fff5f5;
                border: 1px solid #f3c1c5;
                border-radius: 7px;
                color: #b4232f;
                font-size: 13px;
                font-weight: 800;
                min-height: 38px;
                padding: 0 16px;
            }
            QPushButton#dangerButton:disabled {
                background-color: #f3f6f8;
                border-color: #e0e7ed;
                color: #8a98a8;
            }
            QPushButton#successButton {
                background-color: #edf9f0;
                border: 1px solid #9bd8ad;
                border-radius: 7px;
                color: #0a7f31;
                font-size: 13px;
                font-weight: 900;
                min-height: 38px;
                padding: 0 16px;
            }
            QPushButton#successButton:hover {
                background-color: #dff4e5;
            }
            QTableWidget#productsTable {
                background-color: #ffffff;
                border: 1px solid #e3e9ee;
                border-radius: 7px;
                color: #24364a;
                gridline-color: #edf1f4;
                selection-background-color: #edf9f0;
                selection-color: #10243b;
            }
            QHeaderView::section {
                background-color: #f6f9fb;
                border: none;
                border-bottom: 1px solid #e3e9ee;
                color: #516276;
                font-size: 12px;
                font-weight: 800;
                min-height: 34px;
                padding: 0 8px;
            }
            QPushButton#dateButton,
            QPushButton#bellButton {
                background-color: #ffffff;
                border: 1px solid #e3e9ee;
                border-radius: 7px;
                color: #24364a;
                font-size: 13px;
                min-height: 42px;
            }
            QPushButton#bellButton {
                color: #108d38;
                font-weight: 900;
            }
            QScrollArea#pageScroll {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 10px;
                margin: 12px 0 12px 0;
            }
            QScrollBar::handle:vertical {
                background: #b8c0c9;
                border-radius: 5px;
                min-height: 26px;
            }
            QScrollBar::handle:vertical:hover {
                background: #8f9aa8;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                background: transparent;
                height: 12px;
                subcontrol-origin: margin;
            }
            QScrollBar::sub-line:vertical {
                subcontrol-position: top;
            }
            QScrollBar::add-line:vertical {
                subcontrol-position: bottom;
            }
            QScrollBar::up-arrow:vertical {
                image: none;
                width: 0;
                height: 0;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 5px solid #8f9aa8;
            }
            QScrollBar::down-arrow:vertical {
                image: none;
                width: 0;
                height: 0;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #8f9aa8;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
            }
            QScrollBar:horizontal {
                background: transparent;
                height: 10px;
                margin: 0 12px 0 12px;
            }
            QScrollBar::handle:horizontal {
                background: #b8c0c9;
                border-radius: 5px;
                min-width: 26px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #8f9aa8;
            }
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                background: transparent;
                width: 12px;
                subcontrol-origin: margin;
            }
            QScrollBar::sub-line:horizontal {
                subcontrol-position: left;
            }
            QScrollBar::add-line:horizontal {
                subcontrol-position: right;
            }
            QScrollBar::left-arrow:horizontal {
                image: none;
                width: 0;
                height: 0;
                border-top: 4px solid transparent;
                border-bottom: 4px solid transparent;
                border-right: 5px solid #8f9aa8;
            }
            QScrollBar::right-arrow:horizontal {
                image: none;
                width: 0;
                height: 0;
                border-top: 4px solid transparent;
                border-bottom: 4px solid transparent;
                border-left: 5px solid #8f9aa8;
            }
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {
                background: transparent;
            }
            QScrollArea#pageScroll > QWidget > QWidget,
            QWidget#pageContainer,
            QWidget#dashboardPage {
                background-color: #fbfdff;
            }
            QLabel#pageLead {
                color: #334e68;
                font-size: 15px;
                font-weight: 700;
            }
            QFrame#statCard,
            QFrame#productMetricCard,
            QFrame#contentPanel,
            QFrame#placeholderCard {
                background-color: #ffffff;
                border: 1px solid #edf1f4;
                border-radius: 10px;
            }
            QWidget#managerDashboard,
            QWidget#sellerDashboard {
                background-color: #fbfdff;
                font-family: "Segoe UI";
            }
            QFrame#dashboardMetricCard,
            QFrame#salesEvolutionPanel,
            QFrame#topProductsPanel,
            QFrame#vendorSummaryPanel,
            QFrame#recentActivityPanel,
            QFrame#quickAlertsPanel,
            QFrame#sellerEvolutionPanel,
            QFrame#sellerRecentSalesPanel,
            QFrame#sellerTopProductsPanel,
            QFrame#sellerSummaryPanel {
                background-color: #ffffff;
                border: 1px solid #e3e9ef;
                border-radius: 10px;
            }
            QFrame#dashboardMetricCard {
                min-height: 104px;
            }
            QLabel#dashboardMetricIcon_green,
            QLabel#dashboardMetricIcon_blue,
            QLabel#dashboardMetricIcon_orange,
            QLabel#dashboardMetricIcon_red {
                border-radius: 23px;
            }
            QLabel#dashboardMetricIcon_green { background-color: #16a33a; }
            QLabel#dashboardMetricIcon_blue { background-color: #1f74d8; }
            QLabel#dashboardMetricIcon_orange { background-color: #ff8614; }
            QLabel#dashboardMetricIcon_red { background-color: #ef4b55; }
            QLabel#dashboardMetricTitle {
                color: #526b8b;
                font-size: 11px;
            }
            QLabel#dashboardMetricValue {
                color: #073264;
                font-size: 19px;
                font-weight: 900;
            }
            QLabel#dashboardMetricTrend {
                color: #64748b;
                font-size: 9px;
                font-weight: 700;
            }
            QLabel#dashboardMetricTrend[trend="positive"] { color: #15933a; }
            QLabel#dashboardMetricTrend[trend="negative"] { color: #ef4b55; }
            QLabel#dashboardPanelTitle {
                color: #073264;
                font-size: 14px;
                font-weight: 900;
            }
            QPushButton#dashboardLinkButton {
                background: transparent;
                border: none;
                color: #1269c7;
                font-size: 10px;
                font-weight: 700;
                min-height: 24px;
                padding: 0 4px;
            }
            QPushButton#dashboardPeriodButton {
                background-color: #ffffff;
                border: 1px solid #dce5ed;
                border-radius: 6px;
                color: #526b8b;
                font-size: 10px;
                min-height: 30px;
                padding: 0 10px;
            }
            QTableWidget#dashboardTable {
                background-color: #ffffff;
                border: none;
                color: #173b68;
                font-size: 10px;
                gridline-color: #e7edf2;
                selection-background-color: #eef9f0;
                selection-color: #073264;
            }
            QTableWidget#dashboardTable QHeaderView::section {
                background-color: #ffffff;
                border: none;
                border-bottom: 1px solid #e3e9ef;
                color: #526b8b;
                font-size: 9px;
                font-weight: 700;
                min-height: 28px;
                padding: 0 5px;
            }
            QFrame#dashboardInfoRow,
            QFrame#dashboardSaleRow,
            QFrame#dashboardSummaryRow {
                background-color: transparent;
                border: none;
                border-bottom: 1px solid #edf1f4;
            }
            QLabel#dashboardSmallIcon_blue,
            QLabel#dashboardSmallIcon_orange,
            QLabel#dashboardSmallIcon_red {
                border-radius: 6px;
            }
            QLabel#dashboardSmallIcon_blue { background-color: #1f74d8; }
            QLabel#dashboardSmallIcon_orange { background-color: #ff8614; }
            QLabel#dashboardSmallIcon_red { background-color: #ef4b55; }
            QLabel#dashboardRowTitle {
                color: #173b68;
                font-size: 10px;
                font-weight: 700;
            }
            QLabel#dashboardRowSubtitle {
                color: #71839a;
                font-size: 9px;
            }
            QLabel#dashboardEmpty {
                color: #71839a;
                font-size: 11px;
                padding: 18px;
            }
            QLabel#dashboardSaleIcon {
                background-color: #f7f9fb;
                border: 1px solid #e3e9ef;
                border-radius: 7px;
            }
            QLabel#dashboardSaleAmount {
                color: #15933a;
                font-size: 11px;
                font-weight: 900;
            }
            QLabel#dashboardSummaryLabel {
                color: #526b8b;
                font-size: 10px;
            }
            QLabel#dashboardSummaryValue {
                color: #15933a;
                font-size: 11px;
                font-weight: 900;
            }
            QWidget#productsPage {
                background-color: #fbfdff;
            }
            QWidget#productSearchPage {
                background-color: #fbfdff;
                font-family: "Segoe UI";
            }
            QLineEdit#productLookupSearch {
                background-color: #ffffff;
                border: 1px solid #dce5ed;
                border-radius: 9px;
                color: #073264;
                font-size: 13px;
                min-height: 52px;
                padding: 0 14px;
            }
            QScrollArea#productCategoriesScroll {
                background: transparent;
                border: none;
            }
            QScrollArea#productCategoriesScroll QWidget {
                background: transparent;
            }
            QPushButton#productCategoryChip {
                background-color: #ffffff;
                border: 1px solid #dce5ed;
                border-radius: 8px;
                color: #173b68;
                font-size: 11px;
                font-weight: 700;
                min-height: 36px;
                padding: 0 16px;
            }
            QPushButton#productCategoryChip:hover {
                border-color: #7bc990;
                color: #15933a;
            }
            QPushButton#productCategoryChip:checked {
                background-color: #eef9f0;
                border-color: #56b96f;
                color: #138736;
            }
            QFrame#productLookupPanel,
            QFrame#productLookupInfo {
                background-color: #ffffff;
                border: 1px solid #e3e9ef;
                border-radius: 10px;
            }
            QTableWidget#productLookupTable {
                background-color: #ffffff;
                border: none;
                color: #173b68;
                font-size: 11px;
                selection-background-color: #eef9f0;
                selection-color: #073264;
            }
            QTableWidget#productLookupTable QHeaderView::section {
                background-color: #ffffff;
                border: none;
                border-bottom: 1px solid #e3e9ef;
                color: #073264;
                font-size: 10px;
                font-weight: 900;
                min-height: 40px;
                padding: 0 10px;
            }
            QLabel#productStockBadge {
                border-radius: 7px;
                font-size: 10px;
                font-weight: 800;
                margin: 10px 8px;
                min-width: 76px;
                padding: 3px 8px;
            }
            QLabel#productStockBadge[tone="green"] {
                background-color: #eaf8ee;
                color: #138736;
            }
            QLabel#productStockBadge[tone="orange"] {
                background-color: #fff3e5;
                color: #c65e00;
            }
            QLabel#productStockBadge[tone="red"] {
                background-color: #ffecef;
                color: #c92f3d;
            }
            QLabel#productLookupEmpty {
                color: #71839a;
                font-size: 12px;
                padding: 24px;
            }
            QLabel#productLookupInfoText {
                color: #173b68;
                font-size: 11px;
            }
            QWidget#productsPage QLineEdit,
            QWidget#productsPage QSpinBox,
            QWidget#productsPage QComboBox {
                min-height: 24px;
                font-size: 12px;
                padding: 0 8px;
            }
            QWidget#productsPage QPushButton#primaryButton,
            QWidget#productsPage QPushButton#outlineButton,
            QWidget#productsPage QPushButton#dangerButton,
            QWidget#productsPage QPushButton#successButton,
            QWidget#productsPage QPushButton#blueButton {
                min-height: 34px;
                font-size: 12px;
            }
            QWidget#productsPage QPushButton#primaryButton,
            QWidget#productsPage QPushButton#outlineButton,
            QWidget#productsPage QPushButton#dangerButton,
            QWidget#productsPage QPushButton#successButton,
            QWidget#productsPage QPushButton#blueButton {
                min-height: 30px;
                padding: 0 12px;
            }
            QWidget#stockPage QLineEdit,
            QWidget#stockPage QSpinBox,
            QWidget#stockPage QComboBox,
            QWidget#stockPage QDateEdit {
                min-height: 36px;
                font-size: 12px;
                padding: 0 8px;
            }
            QWidget#stockPage QPushButton#primaryButton,
            QWidget#stockPage QPushButton#blueButton,
            QWidget#stockPage QPushButton#outlineButton {
                min-height: 32px;
                font-size: 12px;
                padding: 0 12px;
            }
            QWidget#stockPage QCheckBox {
                min-height: 30px;
                font-size: 12px;
                spacing: 8px;
            }
            QWidget#salePage {
                background-color: #fbfdff;
            }
            QWidget#ticketPage {
                background-color: #fbfdff;
            }
            QFrame#salePanel {
                background-color: #ffffff;
                border: 1px solid #edf1f4;
                border-radius: 10px;
            }
            QLineEdit#saleSearch {
                min-width: 560px;
                max-width: 680px;
                min-height: 38px;
                border-radius: 8px;
                padding-left: 4px;
            }
            QWidget#salePage QPushButton#primaryButton,
            QWidget#salePage QPushButton#outlineButton,
            QWidget#salePage QPushButton#dangerButton,
            QWidget#salePage QPushButton#successButton {
                min-height: 32px;
                font-size: 12px;
                padding: 0 12px;
            }
            QPushButton#categoryChip {
                background-color: #ffffff;
                border: 1px solid #dfe8f0;
                border-radius: 14px;
                color: #0b3567;
                font-size: 13px;
                font-weight: 800;
                min-height: 34px;
                padding: 0 18px;
            }
            QPushButton#categoryChip[active="true"] {
                background-color: #108d38;
                border-color: #108d38;
                color: #ffffff;
            }
            QFrame#productSaleCard {
                background-color: #ffffff;
                border: 1px solid #dfe8f0;
                border-radius: 8px;
            }
            QLabel#productThumbnail,
            QLabel#cartThumb {
                background-color: #e9f7fb;
                border: 1px solid #bfe5f2;
                border-radius: 4px;
                color: #0b5f8a;
                font-size: 9px;
                font-weight: 900;
            }
            QLabel#productCardName {
                color: #073264;
                font-size: 12px;
                font-weight: 900;
            }
            QLabel#productCardDesc {
                color: #526173;
                font-size: 11px;
            }
            QLabel#productCardPrice {
                color: #073264;
                font-size: 18px;
                font-weight: 900;
            }
            QLabel#productCardStock {
                color: #0e8d37;
                font-size: 13px;
                font-weight: 800;
            }
            QLabel#salePanelTitle {
                color: #073264;
                font-size: 16px;
                font-weight: 900;
            }
            QLabel#cartHeader {
                color: #0b3567;
                font-size: 12px;
                font-weight: 800;
            }
            QFrame#cartRow {
                border-top: 1px solid #edf1f4;
                background-color: #ffffff;
            }
            QLabel#cartProductName {
                color: #073264;
                font-size: 12px;
                font-weight: 800;
            }
            QLabel#cartProductDesc {
                color: #526173;
                font-size: 11px;
            }
            QLabel#cartValue {
                color: #073264;
                font-size: 15px;
                font-weight: 800;
            }
            QPushButton#quantityButton {
                background-color: #ffffff;
                border: 1px solid #dfe8f0;
                color: #0b3567;
                font-size: 16px;
                font-weight: 900;
            }
            QLabel#quantityValue {
                background-color: #ffffff;
                border-top: 1px solid #dfe8f0;
                border-bottom: 1px solid #dfe8f0;
                color: #073264;
                font-size: 13px;
                font-weight: 900;
            }
            QPushButton#iconDangerButton {
                background-color: transparent;
                border: none;
            }
            QLabel#cartCount {
                color: #073264;
                font-size: 13px;
                font-weight: 900;
            }
            QLabel#summaryLabel {
                color: #0b3567;
                font-size: 13px;
                font-weight: 800;
            }
            QLabel#summaryValue {
                color: #073264;
                font-size: 14px;
                font-weight: 900;
            }
            QLabel#summaryCurrency {
                color: #526173;
                font-size: 12px;
                font-weight: 800;
            }
            QLineEdit#saleAmountInput,
            QSpinBox#saleAmountInput {
                min-height: 36px;
                font-size: 13px;
            }
            QFrame#summarySeparator {
                background-color: #dfe8f0;
            }
            QLabel#totalAmount {
                color: #16943c;
                font-size: 22px;
                font-weight: 900;
            }
            QLabel#cashInfo {
                background-color: #e4f1ff;
                border-radius: 7px;
                color: #0b3567;
                font-size: 13px;
                font-weight: 800;
                min-height: 36px;
                padding: 0 14px;
            }
            QLabel#paymentHint {
                color: #31547a;
                font-size: 12px;
                font-weight: 700;
                min-height: 16px;
            }
            QLabel#saleEmpty {
                color: #64748b;
                font-size: 13px;
                padding: 12px 4px;
            }
            QLabel#ticketPageTitle {
                color: #073264;
                font-size: 26px;
                font-weight: 900;
            }
            QLabel#ticketBreadcrumb {
                color: #31547a;
                font-size: 13px;
                font-weight: 700;
            }
            QLabel#ticketNotice {
                background-color: #e4f1ff;
                border: 1px solid #c8e0ff;
                border-radius: 7px;
                color: #0b3567;
                font-size: 13px;
                font-weight: 800;
                padding: 10px 14px;
            }
            QFrame#ticketCard {
                background-color: #ffffff;
                border: 1px solid #edf1f4;
                border-radius: 10px;
            }
            QLabel#ticketLogo {
                background-color: #ffffff;
                color: #0b3567;
                font-size: 18px;
                font-weight: 900;
            }
            QLabel#ticketPharmacy {
                color: #073264;
                font-size: 20px;
                font-weight: 900;
            }
            QLabel#ticketMeta {
                color: #31547a;
                font-size: 13px;
                font-weight: 700;
            }
            QFrame#invoiceBox {
                background-color: #ffffff;
                border: 1px solid #dfe8f0;
                border-radius: 8px;
                min-width: 240px;
            }
            QLabel#invoiceTitle {
                color: #108d38;
                font-size: 19px;
                font-weight: 900;
            }
            QLabel#invoiceNumber {
                color: #073264;
                font-size: 17px;
                font-weight: 900;
            }
            QLabel#ticketBarcode {
                color: #10243b;
                font-family: "Consolas";
                font-size: 20px;
                font-weight: 900;
            }
            QFrame#ticketPartyBox {
                background-color: #ffffff;
                border: 1px solid #dfe8f0;
                border-radius: 8px;
            }
            QLabel#ticketPartyTitle {
                color: #0b3567;
                font-size: 12px;
                font-weight: 900;
            }
            QLabel#ticketPartyValue {
                color: #073264;
                font-size: 15px;
                font-weight: 900;
            }
            QLabel#ticketPartySub {
                color: #31547a;
                font-size: 12px;
                font-weight: 700;
            }
            QLabel#ticketTableHeader {
                background-color: #064f8e;
                color: #ffffff;
                font-size: 12px;
                font-weight: 900;
                min-height: 34px;
                padding: 0 12px;
            }
            QLabel#ticketTableCell {
                background-color: #ffffff;
                border-bottom: 1px solid #edf1f4;
                color: #073264;
                font-size: 12px;
                font-weight: 700;
                min-height: 34px;
                padding: 0 12px;
            }
            QFrame#ticketTotals {
                background-color: #ffffff;
                border: 1px solid #edf1f4;
                border-radius: 8px;
                min-width: 420px;
            }
            QLabel#ticketTotalLabel,
            QLabel#ticketTotalValue {
                color: #073264;
                font-size: 13px;
                font-weight: 800;
            }
            QLabel#ticketTotalLabelStrong {
                color: #073264;
                font-size: 16px;
                font-weight: 900;
            }
            QLabel#ticketTotalValueStrong {
                color: #073264;
                font-size: 19px;
                font-weight: 900;
            }
            QFrame#invoiceMetricCard,
            QFrame#invoiceListPanel,
            QFrame#invoicePreviewPanel {
                background-color: #ffffff;
                border: 1px solid #e3e9ef;
                border-radius: 10px;
            }
            QFrame#invoiceMetricCard {
                min-height: 104px;
            }
            QLabel#invoiceMetricIcon {
                border-radius: 20px;
                min-height: 40px;
                max-height: 40px;
                min-width: 40px;
                max-width: 40px;
            }
            QLabel#invoiceMetricTitle {
                color: #526b8b;
                font-size: 11px;
            }
            QLabel#invoiceMetricValue {
                color: #082c59;
                font-size: 19px;
                font-weight: 900;
            }
            QLabel#invoiceMetricTrend {
                color: #15933a;
                font-size: 10px;
                font-weight: 700;
            }
            QLineEdit#invoiceListSearch {
                min-height: 38px;
            }
            QPushButton#invoiceFilterButton,
            QPushButton#invoiceMoreButton {
                background-color: #ffffff;
                border: 1px solid #dce5ed;
                border-radius: 6px;
                color: #173b68;
                min-height: 38px;
                padding: 0 14px;
            }
            QPushButton#invoiceMoreButton {
                font-size: 20px;
                min-width: 34px;
                max-width: 34px;
                padding: 0;
            }
            QTableWidget#invoiceListTable,
            QTableWidget#invoiceLinesTable {
                background-color: #ffffff;
                border: none;
                color: #15375f;
                font-size: 11px;
                gridline-color: #e7edf2;
                selection-background-color: #eef9f0;
                selection-color: #087c2e;
            }
            QTableWidget#invoiceListTable QHeaderView::section,
            QTableWidget#invoiceLinesTable QHeaderView::section {
                background-color: #f7f9fb;
                border: none;
                border-bottom: 1px solid #dfe7ee;
                color: #405b7f;
                font-size: 10px;
                font-weight: 700;
                min-height: 34px;
                padding: 0 8px;
            }
            QLabel#invoiceFooter {
                color: #73849b;
                font-size: 10px;
            }
            QPushButton#invoicePageButton,
            QPushButton#invoicePageActive {
                background-color: #ffffff;
                border: 1px solid #dce5ed;
                border-radius: 5px;
                color: #173b68;
                min-height: 27px;
                min-width: 27px;
                max-width: 27px;
                padding: 0;
            }
            QPushButton#invoicePageActive {
                background-color: #15933a;
                border-color: #15933a;
                color: #ffffff;
            }
            QLabel#invoicePreviewTitle {
                color: #082c59;
                font-size: 17px;
                font-weight: 900;
            }
            QLabel#invoiceStatusBadge {
                background-color: #eaf8ee;
                border-radius: 6px;
                color: #138736;
                font-size: 10px;
                font-weight: 700;
                padding: 4px 8px;
            }
            QLabel#invoiceWord {
                color: #15933a;
                font-size: 20px;
                font-weight: 900;
            }
            QFrame#invoiceParties {
                background-color: #ffffff;
                border: 1px solid #dfe7ee;
                border-radius: 7px;
            }
            QLabel#invoicePartyIcon {
                background-color: #f7f9fb;
                border: 1px solid #dfe7ee;
                border-radius: 15px;
                min-height: 30px;
                max-height: 30px;
                min-width: 30px;
                max-width: 30px;
            }
            QLabel#invoiceGrandTotal {
                color: #129039;
                font-size: 14px;
                font-weight: 900;
            }
            QLabel#invoiceTotalLabel,
            QLabel#invoiceTotalValue {
                color: #526b8b;
                font-size: 11px;
            }
            QPushButton#invoicePrintButton,
            QPushButton#invoiceDownloadButton {
                border-radius: 6px;
                font-size: 13px;
                font-weight: 800;
                min-height: 46px;
            }
            QPushButton#invoicePrintButton {
                background-color: #ffffff;
                border: 1px solid #1254a0;
                color: #1254a0;
            }
            QPushButton#invoiceDownloadButton {
                background-color: #087a3b;
                border: none;
                color: #ffffff;
            }
            QPushButton#invoicePrintButton:disabled,
            QPushButton#invoiceDownloadButton:disabled {
                background-color: #edf1f4;
                border-color: #cfd8e1;
                color: #7b8998;
            }
            QWidget#reportsPage,
            QWidget#historyPage,
            QWidget#alertsPage {
                background-color: #fbfdff;
            }
            QLineEdit#alertsSearch {
                min-height: 38px;
                min-width: 340px;
            }
            QComboBox#alertsFilter {
                min-height: 38px;
                min-width: 180px;
            }
            QFrame#alertsMetricCard,
            QFrame#alertsListPanel,
            QFrame#alertsWatchPanel {
                background-color: #ffffff;
                border: 1px solid #e3e9ef;
                border-radius: 10px;
            }
            QFrame#alertsMetricCard { min-height: 104px; }
            QLabel#alertsMetricIcon_orange,
            QLabel#alertsMetricIcon_yellow,
            QLabel#alertsMetricIcon_red,
            QLabel#alertsMetricIcon_violet { border-radius: 23px; }
            QLabel#alertsMetricIcon_orange { background-color: #ff8614; }
            QLabel#alertsMetricIcon_yellow { background-color: #e8ac08; }
            QLabel#alertsMetricIcon_red { background-color: #ef4b55; }
            QLabel#alertsMetricIcon_violet { background-color: #7c3fc0; }
            QLabel#alertsMetricTitle {
                color: #526b8b;
                font-size: 11px;
                font-weight: 700;
            }
            QLabel#alertsMetricValue {
                color: #073264;
                font-size: 21px;
                font-weight: 900;
            }
            QLabel#alertsMetricSubtitle {
                color: #71839a;
                font-size: 9px;
            }
            QLabel#alertsPanelTitle {
                color: #073264;
                font-size: 15px;
                font-weight: 900;
            }
            QTableWidget#alertsTable {
                background-color: #ffffff;
                border: none;
                color: #173b68;
                font-size: 10px;
                selection-background-color: #eef9f0;
                selection-color: #073264;
            }
            QTableWidget#alertsTable QHeaderView::section {
                background-color: #ffffff;
                border: none;
                border-bottom: 1px solid #e3e9ef;
                color: #526b8b;
                font-size: 9px;
                font-weight: 700;
                min-height: 30px;
                padding: 0 5px;
            }
            QLabel#alertsBadge {
                border-radius: 6px;
                font-size: 9px;
                font-weight: 800;
                margin: 9px 4px;
                padding: 3px 5px;
            }
            QLabel#alertsBadge[tone="orange"] { background-color: #fff3e5; color: #c65e00; }
            QLabel#alertsBadge[tone="yellow"] { background-color: #fff8dc; color: #9a6b00; }
            QLabel#alertsBadge[tone="red"] { background-color: #ffecef; color: #c92f3d; }
            QLabel#alertsBadge[tone="green"] { background-color: #eaf8ee; color: #138736; }
            QLabel#alertsBadge[tone="blue"] { background-color: #eaf3ff; color: #1269c7; }
            QPushButton#alertsRowButton,
            QPushButton#alertsPageButton {
                background-color: #ffffff;
                border: 1px solid #dce5ed;
                border-radius: 6px;
                color: #1269c7;
                font-size: 9px;
                min-height: 30px;
                padding: 0 8px;
            }
            QPushButton#alertsPageButton { min-width: 30px; max-width: 30px; padding: 0; }
            QLabel#alertsFooter,
            QLabel#alertsEmpty {
                color: #71839a;
                font-size: 10px;
            }
            QLabel#alertsWatchSummary {
                background-color: #eef9f0;
                border-radius: 7px;
                color: #138736;
                font-size: 12px;
                font-weight: 800;
                padding: 12px;
            }
            QLabel#alertsWatchHeading {
                color: #073264;
                font-size: 11px;
                font-weight: 900;
                margin-top: 8px;
            }
            QLabel#alertsDistribution,
            QLabel#alertsRecentItem {
                color: #526b8b;
                font-size: 10px;
                line-height: 1.4;
                padding: 6px 2px;
            }
            QPushButton#alertsPrimaryButton,
            QPushButton#alertsSecondaryButton {
                border-radius: 7px;
                font-size: 11px;
                font-weight: 800;
                min-height: 38px;
            }
            QPushButton#alertsPrimaryButton {
                background-color: #15933a;
                border: none;
                color: #ffffff;
            }
            QPushButton#alertsSecondaryButton {
                background-color: #ffffff;
                border: 1px solid #15933a;
                color: #15933a;
            }
            QLabel#reportsTitle {
                color: #073264;
                font-size: 24px;
                font-weight: 900;
            }
            QLabel#reportsSubtitle {
                color: #31547a;
                font-size: 13px;
                font-weight: 700;
            }
            QFrame#reportsPeriod {
                background-color: #ffffff;
                border: 1px solid #dfe8f0;
                border-radius: 7px;
                min-height: 42px;
            }
            QDateEdit#reportsDateEdit {
                background: transparent;
                border: none;
                color: #0b3567;
                font-size: 12px;
                font-weight: 700;
                min-height: 36px;
                min-width: 108px;
                padding: 0 4px;
            }
            QDateEdit#reportsDateEdit::drop-down {
                border: none;
                width: 16px;
            }
            QLabel#reportsPeriodArrow {
                color: #7890aa;
                font-size: 15px;
                min-width: 18px;
            }
            QPushButton#reportsExportButton {
                background-color: #ffffff;
                border: 1px solid #dfe8f0;
                border-radius: 7px;
                color: #0b3567;
                font-size: 12px;
                font-weight: 800;
                min-height: 42px;
                padding: 0 18px;
            }
            QPushButton#reportsExportButton:hover {
                border-color: #0b3567;
                background-color: #f7fbff;
            }
            QPushButton#reportsExportButton:disabled {
                color: #8a98a8;
                background-color: #f4f7f9;
            }
            QPushButton#reportTab,
            QPushButton#reportTabActive {
                background-color: #ffffff;
                border: 1px solid #dfe8f0;
                border-radius: 8px;
                color: #0b3567;
                font-size: 12px;
                font-weight: 800;
                min-height: 38px;
                padding: 0 22px;
            }
            QPushButton#reportTabActive {
                background-color: #108d38;
                border-color: #108d38;
                color: #ffffff;
            }
            QLabel#filterPill {
                background-color: #ffffff;
                border: 1px solid #dfe8f0;
                border-radius: 7px;
                color: #0b3567;
                font-size: 13px;
                font-weight: 800;
                min-height: 38px;
                padding: 0 14px;
            }
            QFrame#reportsPanel,
            QFrame#reportMetric {
                background-color: #ffffff;
                border: 1px solid #edf1f4;
                border-radius: 8px;
            }
            QLabel#reportMetricIcon {
                background-color: #18a640;
                border-radius: 25px;
            }
            QLabel#reportMetricIconBlue {
                background-color: #2474d8;
                border-radius: 25px;
            }
            QLabel#reportsPanelTitle {
                color: #073264;
                font-size: 14px;
                font-weight: 900;
            }
            QLabel#reportsChartContext,
            QPushButton#reportsSeeAll {
                background-color: #f8fbfd;
                border: 1px solid #dfe8f0;
                border-radius: 6px;
                color: #31547a;
                font-size: 10px;
                min-height: 26px;
                padding: 0 10px;
            }
            QPushButton#reportsSeeAll:hover {
                color: #0a8f35;
                border-color: #9bd8ad;
            }
            QLabel#reportMetricTitle {
                color: #31547a;
                font-size: 11px;
                font-weight: 800;
            }
            QLabel#reportMetricValue {
                color: #073264;
                font-size: 20px;
                font-weight: 900;
            }
            QLabel#reportMetricSubtitle {
                color: #108d38;
                font-size: 10px;
                font-weight: 800;
            }
            QLabel#reportMetricSubtitle[trendState="negative"] {
                color: #d13b47;
            }
            QLabel#reportsEmptyState {
                background-color: #f7fafc;
                border: 1px solid #e4ebf1;
                border-radius: 7px;
                color: #516b85;
                font-size: 13px;
                min-height: 44px;
            }
            QTableWidget#reportsTable {
                background-color: #ffffff;
                border: none;
                color: #073264;
                gridline-color: #edf1f4;
                selection-background-color: #edf9f0;
                selection-color: #10243b;
                alternate-background-color: #fbfdff;
                font-size: 11px;
            }
            QTableWidget#reportsTable QHeaderView::section {
                background-color: #ffffff;
                color: #607a96;
                font-size: 10px;
                font-weight: 700;
                min-height: 30px;
                border-bottom: 1px solid #edf1f4;
            }
            QLabel#actionSummaryRow {
                color: #073264;
                font-size: 13px;
                font-weight: 800;
                min-height: 30px;
            }
            QWidget#vendorsPage {
                background-color: #fbfdff;
            }
            QLabel#vendorsTitle {
                color: #073264;
                font-size: 26px;
                font-weight: 900;
            }
            QLabel#vendorsSubtitle {
                color: #31547a;
                font-size: 14px;
            }
            QLineEdit#vendorsSearch {
                min-width: 360px;
                max-width: 430px;
                min-height: 36px;
                border-radius: 8px;
                padding-left: 4px;
            }
            QFrame#vendorMetricCard,
            QFrame#vendorsPanel {
                background-color: #ffffff;
                border: 1px solid #edf1f4;
                border-radius: 10px;
            }
            QLabel#vendorMetricIcon_green {
                background-color: #16a33a;
                border-radius: 23px;
            }
            QLabel#vendorMetricIcon_blue {
                background-color: #1f74d8;
                border-radius: 23px;
            }
            QLabel#vendorMetricIcon_red {
                background-color: #ef4b55;
                border-radius: 23px;
            }
            QLabel#vendorMetricTitle {
                color: #31547a;
                font-size: 12px;
                font-weight: 800;
            }
            QLabel#vendorMetricValue {
                color: #073264;
                font-size: 22px;
                font-weight: 900;
            }
            QLabel#vendorMetricSubtitle {
                color: #64748b;
                font-size: 12px;
            }
            QLabel#vendorsPanelTitle {
                color: #073264;
                font-size: 16px;
                font-weight: 900;
            }
            QTableWidget#vendorsTable {
                background-color: #ffffff;
                border: none;
                color: #24364a;
                gridline-color: #edf1f4;
                selection-background-color: #edf9f0;
                selection-color: #10243b;
            }
            QWidget#vendorsPage QPushButton#primaryButton,
            QWidget#vendorsPage QPushButton#outlineButton,
            QWidget#vendorsPage QPushButton#blueButton,
            QWidget#vendorsPage QPushButton#dangerButton,
            QWidget#vendorsPage QPushButton#successButton {
                min-height: 36px;
                font-size: 12px;
                padding: 0 12px;
            }
            QLabel#vendorFormLabel {
                color: #0b3567;
                font-size: 12px;
                font-weight: 800;
            }
            QLineEdit#vendorFormInput {
                min-height: 36px;
                font-size: 13px;
            }
            QLabel#vendorInfo {
                background-color: #edf9f0;
                border: 1px solid #cfead8;
                border-radius: 7px;
                color: #107133;
                font-size: 12px;
                font-weight: 700;
                padding: 12px;
            }
            QLabel#vendorsFooter {
                color: #64748b;
                font-size: 12px;
            }
            QScrollArea#stockSideScroll,
            QScrollArea#stockSideScroll QWidget#stockSideContainer {
                background: transparent;
                border: none;
            }
            QLabel#productsPageTitle {
                color: #073264;
                font-size: 24px;
                font-weight: 900;
            }
            QLabel#productsPageSubtitle {
                color: #31547a;
                font-size: 13px;
            }
            QLineEdit#productsHeroSearch {
                min-width: 360px;
                max-width: 440px;
                min-height: 38px;
            }
            QLabel#productMetricIcon_green {
                background-color: #12a83f;
                border-radius: 20px;
            }
            QLabel#productMetricIcon_blue {
                background-color: #1f74d8;
                border-radius: 20px;
            }
            QLabel#productMetricIcon_orange {
                background-color: #ff8a00;
                border-radius: 20px;
            }
            QLabel#productMetricIcon_purple {
                background-color: #7b3fba;
                border-radius: 20px;
            }
            QLabel#productMetricTitle {
                color: #31547a;
                font-size: 12px;
                font-weight: 800;
            }
            QLabel#productMetricValue {
                color: #073264;
                font-size: 18px;
                font-weight: 900;
            }
            QLabel#productMetricTrend_green,
            QLabel#productMetricTrend_blue {
                color: #108d38;
                font-size: 12px;
                font-weight: 700;
            }
            QLabel#productMetricTrend_orange {
                color: #f07900;
                font-size: 12px;
                font-weight: 700;
            }
            QLabel#productMetricTrend_purple {
                color: #7b3fba;
                font-size: 12px;
                font-weight: 700;
            }
            QLabel#sidePanelTitle {
                color: #073264;
                font-size: 15px;
                font-weight: 900;
            }
            QLabel#formFieldLabel {
                color: #31547a;
                font-size: 10px;
                font-weight: 800;
            }
            QLabel#productStatusHint {
                color: #31547a;
                font-size: 12px;
                line-height: 18px;
                padding: 4px 0;
            }
            QLabel#iconBubble_green {
                background-color: #16a33a;
                border-radius: 27px;
                color: #ffffff;
                font-size: 20px;
                font-weight: 900;
            }
            QLabel#iconBubble_blue {
                background-color: #1269c7;
                border-radius: 27px;
                color: #ffffff;
                font-size: 20px;
                font-weight: 900;
            }
            QLabel#iconBubble_orange {
                background-color: #ff991f;
                border-radius: 27px;
                color: #ffffff;
                font-size: 20px;
                font-weight: 900;
            }
            QLabel#iconBubble_red {
                background-color: #ef4b55;
                border-radius: 27px;
                color: #ffffff;
                font-size: 20px;
                font-weight: 900;
            }
            QLabel#statTitle {
                color: #5b6b7f;
                font-size: 12px;
                font-weight: 800;
            }
            QLabel#statValue {
                color: #0b2f4f;
                font-size: 23px;
                font-weight: 900;
            }
            QLabel#statTrend {
                color: #16a33a;
                font-size: 12px;
            }
            QLabel#panelTitle,
            QLabel#placeholderTitle {
                color: #10243b;
                font-size: 17px;
                font-weight: 900;
            }
            QLabel#panelRow {
                color: #334e68;
                font-size: 12px;
                padding: 4px 0;
            }
            QLabel#greenRow,
            QLabel#saleAmount {
                color: #148d37;
                font-weight: 900;
            }
            QLabel#activityRow,
            QLabel#saleText {
                color: #334e68;
                font-size: 12px;
            }
            QLabel#warningRow {
                color: #8a5319;
                font-size: 12px;
            }
            QLabel#dangerRow {
                color: #854049;
                font-size: 12px;
            }
            QLabel#tableHeader {
                color: #516276;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton#smallButton {
                background-color: #ffffff;
                border: 1px solid #e1e7ed;
                border-radius: 6px;
                color: #516276;
                padding: 6px 12px;
            }
            QPushButton#outlineButton {
                background-color: #ffffff;
                border: 1px solid #dfe8f0;
                border-radius: 7px;
                color: #0b3567;
                font-size: 13px;
                font-weight: 800;
                min-height: 38px;
                padding: 0 16px;
            }
            QPushButton#outlineButton:disabled {
                color: #8a98a8;
                background-color: #f7fafc;
            }
            QPushButton#blueButton {
                background-color: #064f8e;
                border: none;
                border-radius: 7px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 900;
                min-height: 38px;
                padding: 0 16px;
            }
            QPushButton#blueButton:hover {
                background-color: #043f73;
            }
            QPushButton#linkButton {
                background-color: transparent;
                border: none;
                color: #1269c7;
                font-size: 12px;
                font-weight: 800;
                padding: 0;
            }
            QPushButton#paginationButton,
            QPushButton#paginationButtonActive {
                background-color: #ffffff;
                border: 1px solid #dfe8f0;
                border-radius: 7px;
                color: #0b3567;
                font-size: 13px;
                font-weight: 800;
                min-width: 32px;
                min-height: 32px;
            }
            QPushButton#paginationButtonActive {
                background-color: #064f8e;
                color: #ffffff;
                border-color: #064f8e;
            }
            QLabel#productsFooterText {
                color: #64748b;
                font-size: 12px;
            }
            QComboBox#pageSizeCombo {
                min-width: 104px;
                min-height: 32px;
            }
            QLabel#linkLabel {
                color: #1269c7;
                text-decoration: underline;
            }
            QLabel#saleIcon {
                background-color: #f8fafc;
                border: 1px solid #edf1f4;
                border-radius: 6px;
                min-width: 38px;
                min-height: 38px;
            }
            QLabel#placeholderText {
                color: #526173;
                font-size: 14px;
                line-height: 20px;
            }
            QLabel#homeLogo {
                background-color: transparent;
            }
            QPushButton#photoButton {
                background-color: #0f8f3a;
                border: none;
                border-radius: 7px;
                color: #ffffff;
                font-size: 14px;
                font-weight: 800;
                min-height: 42px;
                padding: 0 18px;
            }
            QPushButton#photoButton:hover {
                background-color: #0b7831;
            }
            QFrame#backupPanel {
                background-color: #ffffff;
                border: 1px solid #dfe8f0;
                border-radius: 8px;
            }
            QLabel#backupTitle {
                color: #073264;
                font-size: 17px;
                font-weight: 900;
            }
            QWidget#settingsPage QLabel {
                color: #17324d;
            }
            QWidget#settingsPage QLabel#settingsFieldLabel {
                color: #102f50;
                font-size: 13px;
                font-weight: 700;
            }
            QLabel#backupSubtitle,
            QLabel#backupStatus {
                color: #526b85;
                font-size: 12px;
            }
            QLabel#backupStatus {
                background-color: #f6f9fb;
                border: 1px solid #e3eaf0;
                border-radius: 6px;
                min-height: 36px;
                padding: 0 12px;
            }
            QLabel#backupMetaValue {
                color: #173f68;
                font-size: 12px;
            }
            QCheckBox#backupAutoCheckbox {
                color: #173f68;
                min-height: 28px;
                spacing: 8px;
            }
            QComboBox#backupFrequencyCombo {
                background-color: #ffffff;
                border: 1px solid #cfdbe6;
                border-radius: 6px;
                color: #173f68;
                min-height: 34px;
                min-width: 250px;
                padding: 0 10px;
            }
            QPushButton#backupPrimaryButton,
            QPushButton#backupSecondaryButton,
            QPushButton#backupSettingsButton {
                border-radius: 7px;
                font-size: 12px;
                font-weight: 800;
                min-height: 38px;
                padding: 0 16px;
            }
            QPushButton#backupPrimaryButton {
                background-color: #108d38;
                border: 1px solid #108d38;
                color: #ffffff;
            }
            QPushButton#backupSecondaryButton {
                background-color: #ffffff;
                border: 1px solid #cfdbe6;
                color: #0b3567;
            }
            QPushButton#backupSettingsButton {
                background-color: #f5f8fb;
                border: 1px solid #cfdbe6;
                color: #0b3567;
            }
            QPushButton#backupPrimaryButton:focus,
            QPushButton#backupSecondaryButton:focus,
            QPushButton#backupSettingsButton:focus,
            QComboBox#backupFrequencyCombo:focus,
            QCheckBox#backupAutoCheckbox:focus {
                border: 2px solid #1875d1;
            }
            QPushButton:focus,
            QLineEdit:focus,
            QSpinBox:focus,
            QComboBox:focus,
            QDateEdit:focus,
            QTableWidget:focus {
                border: 2px solid #1875d1;
            }
            QPushButton#backupPrimaryButton:disabled,
            QPushButton#backupSecondaryButton:disabled,
            QPushButton#backupSettingsButton:disabled {
                background-color: #eef2f5;
                border-color: #dce3e8;
                color: #8b98a5;
            }
            QLabel#profilePhoto {
                background-color: #edf3f8;
                border: 1px solid #d9e3ea;
                border-radius: 60px;
                color: #12314f;
                font-size: 42px;
                font-weight: 800;
            }
            MainWindow[theme="dark"] QWidget#workspace,
            MainWindow[theme="dark"] QWidget#pageContainer,
            MainWindow[theme="dark"] QWidget#dashboardPage,
            MainWindow[theme="dark"] QFrame#topbar {
                background-color: #111827;
            }
            MainWindow[theme="dark"] QFrame#contentPanel,
            MainWindow[theme="dark"] QFrame#statCard,
            MainWindow[theme="dark"] QFrame#productMetricCard,
            MainWindow[theme="dark"] QFrame#placeholderCard,
            MainWindow[theme="dark"] QFrame#backupPanel {
                background-color: #1f2937;
                border-color: #374151;
            }
            MainWindow[theme="dark"] QLabel {
                color: #e5e7eb;
            }
            MainWindow[theme="dark"] QLineEdit#topbarSearch,
            MainWindow[theme="dark"] QLineEdit,
            MainWindow[theme="dark"] QSpinBox,
            MainWindow[theme="dark"] QComboBox,
            MainWindow[theme="dark"] QComboBox#backupFrequencyCombo,
            MainWindow[theme="dark"] QPushButton#dateButton,
            MainWindow[theme="dark"] QPushButton#bellButton,
            MainWindow[theme="dark"] QPushButton#menuButton {
                background-color: #1f2937;
                border-color: #374151;
                color: #e5e7eb;
            }
            """
        )


class SettingsPage(QWidget):
    """Sauvegarde locale et restauration réservées au gérant."""

    redemarrage_demande = Signal()

    def __init__(
        self,
        session_utilisateur: SessionUtilisateur,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("settingsPage")
        self.session_utilisateur = session_utilisateur
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self.backup_panel = BackupPanel(session_utilisateur)
        self.backup_panel.restart_requested.connect(self.redemarrage_demande.emit)
        self.settings_grid = QGridLayout()
        self.settings_grid.setSpacing(16)
        self.general_panel = GeneralSettingsPanel(session_utilisateur)
        self.security_panel = SecuritySettingsPanel(session_utilisateur)
        self.settings_grid.addWidget(self.general_panel, 0, 0)
        self.settings_grid.addWidget(self.security_panel, 0, 1)
        self.settings_grid.addWidget(self.backup_panel, 1, 1)
        layout.addLayout(self.settings_grid)
        layout.addStretch(1)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.set_compact(self.window().width() < 1200)

    def set_compact(self, compact: bool) -> None:
        self.settings_grid.addWidget(self.general_panel, 0, 0, 1, 1)
        self.settings_grid.addWidget(
            self.security_panel, 1, 0
        )
        self.settings_grid.addWidget(
            self.backup_panel,
            2 if compact else 0,
            0 if compact else 1,
            1 if compact else 2,
            1,
        )
        self.settings_grid.invalidate()
        self.updateGeometry()


def _page_title(key: str) -> str:
    titles = {
        "dashboard": "Tableau de bord",
        "produits": "Produits",
        "stock": "Stock",
        "ventes": "Ventes",
        "factures": "Factures",
        "rapports": "Rapports",
        "vendeurs": "Vendeurs",
        "historique": "Historique",
        "alertes": "Alertes",
        "parametres": "Parametres",
        "nouvelle_vente": "Nouvelle vente",
        "historique_ventes": "Historique des ventes",
    }
    return titles.get(key, "SALMOSPHARM")
