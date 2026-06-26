"""Layout principal connecte de SALMOSPHARM 133."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QFrame,
    QLabel,
    QMainWindow,
    QRadioButton,
    QScrollArea,
    QStackedWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.constants import ROLE_GERANT, ROLE_VENDEUR
from app.services.auth_service import SessionUtilisateur
from app.ui.gerant.dashboard_page import GerantDashboardPage
from app.ui.gerant.produits import ProduitsPage
from app.ui.layouts.sidebar import Sidebar
from app.ui.layouts.topbar import Topbar
from app.ui.vendeur.dashboard_page import VendeurDashboardPage


APP_TITLE = "SALMOSPHARM 133"


class MainWindow(QMainWindow):
    """Fenetre principale apres authentification, sans acces direct a SQLite."""

    deconnexion_demandee = Signal()

    def __init__(self, session_utilisateur: SessionUtilisateur) -> None:
        super().__init__()
        self.session_utilisateur = session_utilisateur
        self._pages: dict[str, int] = {}
        self._page_widgets: dict[str, QWidget] = {}
        self._theme = "light"
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(1080, 680)
        self.resize(1320, 820)
        self._build_ui()
        self._apply_style()
        self.navigate("dashboard")

    def toggle_sidebar(self) -> None:
        self.sidebar.setHidden(not self.sidebar.isHidden())

    def navigate(self, key: str) -> None:
        if key not in self._pages:
            return
        if self.sidebar.isHidden():
            self.sidebar.show()
        self.content_stack.setCurrentIndex(self._pages[key])
        self.sidebar.set_active(key)
        self.topbar.set_title(_page_title(key))
        page = self._page_widgets.get(key)
        if page is not None and hasattr(page, "on_show"):
            page.on_show()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("mainRoot")
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = Sidebar(self.session_utilisateur.role)
        self.sidebar.navigation_demandee.connect(self.navigate)
        self.sidebar.deconnexion_demandee.connect(self.deconnexion_demandee.emit)
        self.sidebar.profil_demande.connect(lambda: self.navigate("profil"))
        root_layout.addWidget(self.sidebar)

        workspace = QWidget()
        workspace.setObjectName("workspace")
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)

        self.topbar = Topbar(self.session_utilisateur)
        self.topbar.deconnexion_demandee.connect(self.deconnexion_demandee.emit)
        self.topbar.menu_demande.connect(self.toggle_sidebar)
        workspace_layout.addWidget(self.topbar)

        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("contentStack")
        workspace_layout.addWidget(self.content_stack, 1)
        root_layout.addWidget(workspace, 1)
        self.setCentralWidget(root)
        self._register_pages()

    def _register_pages(self) -> None:
        profile_page = ProfilePage(self.session_utilisateur)
        profile_page.photo_changee.connect(self.sidebar.set_profile_photo)
        self._add_page("profil", profile_page)
        if self.session_utilisateur.role == ROLE_GERANT:
            dashboard = GerantDashboardPage()
            dashboard.voir_tout_demande.connect(self.navigate)
            self._add_page("dashboard", dashboard)
            self._add_page("produits", ProduitsPage(self.session_utilisateur, autoload=False))
            for key in ("stock", "ventes", "factures", "rapports", "vendeurs", "historique", "alertes"):
                self._add_page(key, PlaceholderPage(_page_title(key), _placeholder_text(key)))
            self._add_page("parametres", SettingsPage(self.set_theme))
            for key in ("details_top_produits", "details_vendeurs", "details_activites", "details_alertes"):
                self._add_page(key, PlaceholderPage(_page_title(key), _placeholder_text(key)))
            return

        if self.session_utilisateur.role == ROLE_VENDEUR:
            dashboard = VendeurDashboardPage(self.session_utilisateur)
            dashboard.voir_tout_demande.connect(self.navigate)
            self._add_page("dashboard", dashboard)
            for key in ("nouvelle_vente", "historique_ventes", "produits", "factures"):
                self._add_page(key, PlaceholderPage(_page_title(key), _placeholder_text(key)))
            self._add_page("details_ventes_recentes", PlaceholderPage(_page_title("details_ventes_recentes"), _placeholder_text("details_ventes_recentes")))

    def _add_page(self, key: str, page: QWidget) -> None:
        scroll = QScrollArea()
        scroll.setObjectName("pageScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        container.setObjectName("pageContainer")
        layout = QVBoxLayout(container)
        if key == "produits":
            layout.setContentsMargins(26, 18, 22, 18)
        else:
            layout.setContentsMargins(28, 26, 28, 26)
        layout.addWidget(page)
        scroll.setWidget(container)
        self._pages[key] = self.content_stack.addWidget(scroll)
        self._page_widgets[key] = page

    def set_theme(self, theme: str) -> None:
        self._theme = "dark" if theme == "dark" else "light"
        self.setProperty("theme", self._theme)
        self.style().unpolish(self)
        self.style().polish(self)

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
            QWidget#productsPage {
                background-color: #fbfdff;
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
            QRadioButton#themeChoice {
                color: #10243b;
                font-size: 14px;
                font-weight: 800;
                spacing: 10px;
                min-height: 32px;
            }
            QRadioButton#themeChoice::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid #9aa8b6;
                background-color: #ffffff;
            }
            QRadioButton#themeChoice::indicator:checked {
                border: 5px solid #0f8f3a;
                background-color: #ffffff;
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
            MainWindow[theme="dark"] QFrame#placeholderCard {
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
            MainWindow[theme="dark"] QPushButton#dateButton,
            MainWindow[theme="dark"] QPushButton#bellButton,
            MainWindow[theme="dark"] QPushButton#menuButton {
                background-color: #1f2937;
                border-color: #374151;
                color: #e5e7eb;
            }
            """
        )


class PlaceholderPage(QWidget):
    """Page neutre pour valider navigation et structure, sans logique metier."""

    def __init__(self, title: str, text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        card = QFrame()
        card.setObjectName("placeholderCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 22, 24, 22)
        card_layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setObjectName("placeholderTitle")
        text_label = QLabel(text)
        text_label.setObjectName("placeholderText")
        text_label.setWordWrap(True)
        card_layout.addWidget(title_label)
        card_layout.addWidget(text_label)
        layout.addWidget(card)
        layout.addStretch(1)


class SettingsPage(QWidget):
    """Parametres UI temporaires de Phase 10, sans persistance."""

    def __init__(self, set_theme_callback, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._set_theme_callback = set_theme_callback
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        card = QFrame()
        card.setObjectName("placeholderCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 22, 24, 22)
        card_layout.setSpacing(14)

        title = QLabel("Parametres")
        title.setObjectName("placeholderTitle")
        text = QLabel("Choisissez l'apparence de l'application. Ce reglage visuel n'est pas encore persiste.")
        text.setObjectName("placeholderText")
        text.setWordWrap(True)

        choices = QHBoxLayout()
        choices.setSpacing(24)
        self.light_radio = QRadioButton("Clair")
        self.light_radio.setObjectName("themeChoice")
        self.light_radio.setChecked(True)
        self.dark_radio = QRadioButton("Sombre")
        self.dark_radio.setObjectName("themeChoice")
        self.light_radio.toggled.connect(self._apply_choice)
        self.dark_radio.toggled.connect(self._apply_choice)
        choices.addWidget(self.light_radio)
        choices.addWidget(self.dark_radio)
        choices.addStretch(1)

        card_layout.addWidget(title)
        card_layout.addWidget(text)
        card_layout.addLayout(choices)
        layout.addWidget(card)
        layout.addStretch(1)

    def _apply_choice(self) -> None:
        if self.dark_radio.isChecked():
            self._set_theme_callback("dark")
        else:
            self._set_theme_callback("light")


class ProfilePage(QWidget):
    """Page profil locale pour choisir une photo, sans ecriture base."""

    photo_changee = Signal(QPixmap)

    def __init__(self, session_utilisateur: SessionUtilisateur, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session_utilisateur = session_utilisateur
        self.photo_label = QLabel("o")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        card = QFrame()
        card.setObjectName("placeholderCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 22, 24, 22)
        card_layout.setSpacing(14)

        title = QLabel("Profil utilisateur")
        title.setObjectName("placeholderTitle")
        subtitle = QLabel(f"{self.session_utilisateur.nom} - {self.session_utilisateur.role}")
        subtitle.setObjectName("placeholderText")

        self.photo_label.setObjectName("profilePhoto")
        self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_label.setFixedSize(120, 120)

        photo_button = QPushButton("Choisir une photo de profil")
        photo_button.setObjectName("photoButton")
        photo_button.clicked.connect(self._choose_photo)

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(self.photo_label, alignment=Qt.AlignmentFlag.AlignLeft)
        card_layout.addWidget(photo_button, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(card)
        layout.addStretch(1)

    def _choose_photo(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choisir une photo de profil",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)",
        )
        if not file_path:
            return

        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            return
        self.photo_label.setText("")
        self.photo_label.setPixmap(_circular_pixmap(pixmap, 120))
        self.photo_changee.emit(pixmap)


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
        "profil": "Profil utilisateur",
        "details_top_produits": "Top produits vendus",
        "details_vendeurs": "Synthese par vendeur",
        "details_activites": "Activites recentes",
        "details_alertes": "Alertes rapides",
        "details_ventes_recentes": "Ventes recentes",
    }
    return titles.get(key, "SALMOSPHARM")


def _placeholder_text(key: str) -> str:
    texts = {
        "produits": "Gestion du catalogue a venir. Cette page n'accede pas encore aux donnees.",
        "stock": "Suivi des lots et mouvements a brancher dans les phases metier suivantes.",
        "ventes": "Consultation des ventes validees a venir. Aucune annulation ne sera proposee.",
        "factures": "Placeholder de consultation des recus. Aucune table factures n'est creee.",
        "rapports": "Placeholder de rapports calcules plus tard. Aucune table rapports n'est creee.",
        "vendeurs": "Gestion des comptes vendeurs reservee au gerant dans une phase suivante.",
        "historique": "Historique systeme a connecter plus tard via les services autorises.",
        "alertes": "Alertes stock et expiration a connecter plus tard.",
        "parametres": "Parametres gerant a venir. Devise CDF et paiement especes resteront fixes.",
        "nouvelle_vente": "Ecran de vente a venir. La validation passera par vente_service.",
        "historique_ventes": "Historique personnel du vendeur a connecter plus tard.",
        "details_top_produits": "Interface detaillee placeholder pour consulter tous les produits les plus vendus.",
        "details_vendeurs": "Interface detaillee placeholder pour consulter toute la synthese par vendeur.",
        "details_activites": "Interface detaillee placeholder pour consulter toutes les activites recentes.",
        "details_alertes": "Interface detaillee placeholder pour consulter toutes les alertes rapides.",
        "details_ventes_recentes": "Interface detaillee placeholder pour consulter toutes les ventes recentes.",
    }
    return texts.get(key, "Page placeholder de la Phase 10.")


def _asset_path(file_name: str) -> Path:
    return Path(__file__).resolve().parents[2] / "assets" / file_name


def _circular_pixmap(source: QPixmap, size: int) -> QPixmap:
    scaled = source.scaled(
        size,
        size,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    result = QPixmap(size, size)
    result.fill(Qt.GlobalColor.transparent)

    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    x = int((size - scaled.width()) / 2)
    y = int((size - scaled.height()) / 2)
    painter.drawPixmap(x, y, scaled)
    painter.end()
    return result
