import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QRadioButton

from app.core.constants import ROLE_GERANT, ROLE_VENDEUR
from app.main import MainWindow
from app.services.auth_service import SessionUtilisateur
from app.services.produit_service import ProduitPayload
from app.ui.gerant.produits import ProduitsPage
from app.ui.layouts.sidebar import Sidebar


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _session(role: str) -> SessionUtilisateur:
    return SessionUtilisateur(
        utilisateur_id=1,
        nom="Utilisateur Test",
        identifiant="test",
        role=role,
    )


def _button_texts(window: MainWindow) -> list[str]:
    return [button.text().strip() for button in window.findChildren(QPushButton)]


def test_main_window_instancie_layout_gerant_et_conserve_session():
    app = _app()
    session = _session(ROLE_GERANT)

    window = MainWindow(session_utilisateur=session)

    assert window.session_utilisateur == session
    assert window.windowTitle() == "SALMOSPHARM 133"
    assert window.topbar.user_name_label.text() == "Utilisateur Test"
    assert window.topbar.user_role_label.text() == ROLE_GERANT
    assert window.content_stack.currentIndex() == window._pages["dashboard"]
    assert window.topbar.title_label.text() == "Tableau de bord"

    window.close()
    app.processEvents()


def test_main_window_instancie_layout_vendeur_et_conserve_session():
    app = _app()
    session = _session(ROLE_VENDEUR)

    window = MainWindow(session_utilisateur=session)

    assert window.session_utilisateur == session
    assert window.topbar.user_name_label.text() == "Utilisateur Test"
    assert window.topbar.user_role_label.text() == ROLE_VENDEUR

    window.close()
    app.processEvents()


def test_gerant_voit_uniquement_menus_gerant_demandes():
    app = _app()
    window = MainWindow(session_utilisateur=_session(ROLE_GERANT))

    labels = _button_texts(window)

    for label in (
        "Tableau de bord",
        "Produits",
        "Stock",
        "Ventes",
        "Factures",
        "Rapports",
        "Vendeurs",
        "Historique",
        "Alertes",
        "Parametres",
        "Deconnexion",
    ):
        assert label in labels
    assert "Nouvelle vente" not in labels
    assert "Historique des ventes" not in labels

    window.close()
    app.processEvents()


def test_menu_affiche_sidebar_puis_tableau_de_bord():
    app = _app()
    window = MainWindow(session_utilisateur=_session(ROLE_GERANT))

    window.navigate("dashboard")
    assert window.content_stack.currentIndex() == window._pages["dashboard"]
    assert window.topbar.title_label.text() == "Tableau de bord"

    window.close()
    app.processEvents()


def test_topbar_et_sidebar_affichent_des_icones():
    app = _app()
    window = MainWindow(session_utilisateur=_session(ROLE_GERANT))

    window.toggle_sidebar()
    dashboard_button = next(button for button in window.sidebar.findChildren(QPushButton) if button.text().strip() == "Tableau de bord")
    assert not dashboard_button.icon().isNull()
    assert window.topbar.findChild(QPushButton, "bellButton").icon().isNull() is False
    assert window.topbar.findChild(QPushButton, "dateButton").icon().isNull() is False

    window.close()
    app.processEvents()


def test_dashboard_gerant_aujourdhui_et_voir_tout_ouvre_detail():
    app = _app()
    window = MainWindow(session_utilisateur=_session(ROLE_GERANT))

    window.navigate("dashboard")
    buttons = [button for button in window.findChildren(QPushButton) if button.text().strip() == "Voir tout"]

    assert any(button.text().strip() == "Aujourd'hui   v" for button in window.findChildren(QPushButton))
    assert buttons
    buttons[0].click()
    assert window.content_stack.currentIndex() == window._pages["details_top_produits"]

    window.close()
    app.processEvents()


def test_navigation_gerant_produits_ouvre_page_catalogue():
    app = _app()
    window = MainWindow(session_utilisateur=_session(ROLE_GERANT))

    page = window._page_widgets["produits"]

    assert isinstance(page, ProduitsPage)
    assert window.content_stack.currentIndex() == window._pages["dashboard"]

    window.close()
    app.processEvents()


def test_page_produits_rend_reactivation_visible_pour_produit_desactive():
    app = _app()
    session = _session(ROLE_GERANT)
    page = ProduitsPage(session_utilisateur=session, produit_service=_FakeProduitService(), autoload=True)

    page.products_table.selectRow(0)
    app.processEvents()

    assert page.disable_button.text() == "Reactiver ce produit"
    assert page.disable_button.isEnabled()
    assert page.disable_button.objectName() == "successButton"
    assert "desactive" in page.product_status_hint.text()

    page.close()
    app.processEvents()


def test_page_produits_ne_scrolle_pas_en_plein_ecran():
    app = _app()
    window = MainWindow(session_utilisateur=_session(ROLE_GERANT))
    page = window._page_widgets["produits"]
    page._produit_service = _FakeProduitService()

    window.resize(1450, 900)
    window.show()
    window.navigate("produits")
    app.processEvents()
    scroll = window.content_stack.currentWidget()
    button_bottom = page.save_button.mapTo(scroll.viewport(), page.save_button.rect().bottomRight()).y()

    assert scroll.verticalScrollBar().maximum() == 0
    assert button_bottom <= scroll.viewport().height()

    window.close()
    app.processEvents()


def test_bloc_utilisateur_ouvre_page_profil():
    app = _app()
    window = MainWindow(session_utilisateur=_session(ROLE_GERANT))

    window.toggle_sidebar()
    window.sidebar.profil_demande.emit()

    labels = [label.text() for label in window.findChildren(QLabel)]
    assert window.content_stack.currentIndex() == window._pages["profil"]
    assert "Profil utilisateur" in labels

    window.close()
    app.processEvents()


def test_photo_profil_se_montre_dans_sidebar_sans_petite_fleche():
    app = _app()
    window = MainWindow(session_utilisateur=_session(ROLE_GERANT))

    assert not window.findChildren(QPushButton, "profileButton")
    pixmap = QPixmap(80, 80)
    pixmap.fill(QColor("#16a33a"))
    window.sidebar.set_profile_photo(pixmap)

    assert window.sidebar.avatar_label is not None
    assert window.sidebar.avatar_label.pixmap() is not None
    assert window.sidebar.avatar_label.pixmap().width() == 48

    window.close()
    app.processEvents()


def test_parametres_permet_de_choisir_mode_sombre_ou_clair():
    app = _app()
    window = MainWindow(session_utilisateur=_session(ROLE_GERANT))

    window.navigate("parametres")
    radios = {radio.text().strip(): radio for radio in window.findChildren(QRadioButton)}

    assert "Clair" in radios
    assert "Sombre" in radios
    assert radios["Clair"].isChecked()
    assert window.property("theme") in (None, "")

    radios["Sombre"].setChecked(True)
    assert window.property("theme") == "dark"
    radios["Clair"].setChecked(True)
    assert window.property("theme") == "light"

    window.close()
    app.processEvents()


def test_vendeur_ne_voit_pas_menus_gerant_et_voit_menus_vendeur():
    app = _app()
    window = MainWindow(session_utilisateur=_session(ROLE_VENDEUR))

    labels = _button_texts(window)

    for label in (
        "Tableau de bord",
        "Nouvelle vente",
        "Historique des ventes",
        "Produits",
        "Factures",
        "Deconnexion",
    ):
        assert label in labels
    for forbidden in ("Stock", "Ventes", "Rapports", "Vendeurs", "Historique", "Alertes", "Parametres"):
        assert forbidden not in labels

    window.close()
    app.processEvents()


def test_navigation_affiche_page_placeholder_sans_acces_base():
    app = _app()
    window = MainWindow(session_utilisateur=_session(ROLE_VENDEUR))

    window.navigate("factures")
    labels = [label.text() for label in window.findChildren(QLabel)]

    assert "Factures" in labels
    assert "Placeholder de consultation des recus. Aucune table factures n'est creee." in labels

    window.close()
    app.processEvents()


def test_sidebar_deconnexion_emet_signal():
    app = _app()
    sidebar = Sidebar(ROLE_VENDEUR)
    emitted = []

    sidebar.deconnexion_demandee.connect(lambda: emitted.append(True))
    logout_button = next(button for button in sidebar.findChildren(QPushButton) if button.text().strip() == "Deconnexion")
    logout_button.click()

    assert emitted == [True]

    sidebar.close()
    app.processEvents()


class _FakeProduit:
    def __init__(self, *, produit_id: int, nom: str, actif: int) -> None:
        self.id = produit_id
        self.nom = nom
        self.code_barres = "FAKE-001"
        self.categorie_id = None
        self.prix_vente = 1000
        self.stock_minimum = 0
        self.description = ""
        self.actif = actif


class _FakeProduitService:
    def __init__(self) -> None:
        self.produits = [_FakeProduit(produit_id=1, nom="Produit desactive", actif=0)]

    def lister_categories(self, utilisateur):
        return []

    def rechercher_produits(self, utilisateur, *, terme="", categorie_id=None, actifs_seulement=False):
        return self.produits

    def creer_produit(self, utilisateur, payload: ProduitPayload):
        raise AssertionError("Non utilise")

    def modifier_produit(self, utilisateur, *, produit_id: int, payload: ProduitPayload):
        raise AssertionError("Non utilise")

    def desactiver_produit(self, utilisateur, *, produit_id: int):
        raise AssertionError("Non utilise")

    def reactiver_produit(self, utilisateur, *, produit_id: int):
        self.produits[0].actif = 1
        return self.produits[0]
