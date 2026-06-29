import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QRadioButton

from app.core.constants import ROLE_GERANT, ROLE_VENDEUR
from app.main import MainWindow
from app.services.auth_service import SessionUtilisateur
from app.services.produit_service import ProduitPayload
from app.services.vente_service import ProduitVendable
from app.services.utilisateur_service import VendeurDashboardData, VendeurListItem, VendeurMetrics
from app.ui.gerant.produits import ProduitsPage
from app.ui.gerant.parametres import BackupPanel
from app.ui.gerant.rapports import RapportsPage
from app.ui.gerant.stock import StockPage
from app.ui.gerant.historique import HistoriqueVentesGerantPage
from app.ui.gerant.vendeurs import VendeursPage
from app.ui.layouts.sidebar import Sidebar
from app.ui.vendeur.nouvelle_vente import NouvelleVentePage
from app.ui.vendeur.historique_ventes import HistoriqueVentesVendeurPage


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
    assert "Nouvelle vente" in labels
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


def test_dashboard_gerant_structure_et_liens_ouvrent_pages_reelles():
    app = _app()
    window = MainWindow(session_utilisateur=_session(ROLE_GERANT))

    window.navigate("dashboard")
    dashboard = window._page_widgets["dashboard"]
    labels = {button.text().strip() for button in dashboard.findChildren(QPushButton)}
    assert "7 derniers jours" in labels
    texts = {label.text() for label in dashboard.findChildren(QLabel)}
    assert {
        "Ventes du jour",
        "Transactions",
        "Articles vendables",
        "Stock faible",
        "Expirations proches",
        "Évolution des ventes (CDF)",
        "Top produits vendus",
        "Synthèse par vendeur",
        "Activités récentes",
        "Alertes rapides",
    } <= texts
    rapports = next(
        button
        for button in dashboard.findChildren(QPushButton)
        if button.text().strip() == "Voir tout"
    )
    rapports.click()
    assert window.content_stack.currentIndex() == window._pages["rapports"]

    window.close()
    app.processEvents()


def test_dashboard_vendeur_affiche_structure_personnelle():
    app = _app()
    window = MainWindow(session_utilisateur=_session(ROLE_VENDEUR))
    dashboard = window._page_widgets["dashboard"]
    texts = {label.text() for label in dashboard.findChildren(QLabel)}

    assert window.topbar.title_label.text() == "Tableau de bord vendeur"
    assert {
        "Ventes du jour",
        "Transactions",
        "Total encaissé (CDF)",
        "Articles vendus",
        "Évolution des ventes (CDF)",
        "Ventes récentes",
        "Produits les plus vendus aujourd’hui",
        "Résumé du jour",
    } <= texts

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


def test_navigation_gerant_stock_ouvre_page_lots():
    app = _app()
    window = MainWindow(session_utilisateur=_session(ROLE_GERANT))

    page = window._page_widgets["stock"]

    assert isinstance(page, StockPage)
    assert window.content_stack.currentIndex() == window._pages["dashboard"]

    window.close()
    app.processEvents()


def test_navigation_gerant_vendeurs_ouvre_page_gestion_vendeurs():
    app = _app()
    window = MainWindow(session_utilisateur=_session(ROLE_GERANT))

    page = window._page_widgets["vendeurs"]

    assert isinstance(page, VendeursPage)
    assert window.content_stack.currentIndex() == window._pages["dashboard"]

    window.close()
    app.processEvents()


def test_navigation_phase17_pages_remplacent_placeholders():
    app = _app()
    gerant_window = MainWindow(session_utilisateur=_session(ROLE_GERANT))
    vendeur_window = MainWindow(session_utilisateur=_session(ROLE_VENDEUR))

    assert isinstance(gerant_window._page_widgets["rapports"], RapportsPage)
    assert gerant_window._page_widgets["alertes"].objectName() == "alertsPage"
    assert gerant_window._page_widgets["historique"].objectName() == "actionHistoryPage"
    assert isinstance(vendeur_window._page_widgets["historique_ventes"], HistoriqueVentesVendeurPage)

    gerant_window.close()
    vendeur_window.close()
    app.processEvents()


def test_page_vendeurs_formulaire_sans_champ_role_et_accessible_plein_ecran():
    app = _app()
    window = MainWindow(session_utilisateur=_session(ROLE_GERANT))
    page = window._page_widgets["vendeurs"]
    page._utilisateur_service = _FakeUtilisateurService()

    window.resize(1450, 900)
    window.show()
    window.navigate("vendeurs")
    app.processEvents()
    scroll = window.content_stack.currentWidget()
    labels = [label.text() for label in page.findChildren(QLabel)]
    button_bottom = page.save_button.mapTo(scroll.viewport(), page.save_button.rect().bottomRight()).y()

    assert "Rôle *" not in labels
    assert "Role *" not in labels
    assert scroll.verticalScrollBar().maximum() == 0
    assert button_bottom <= scroll.viewport().height()

    window.close()
    app.processEvents()


def test_navigation_vendeur_nouvelle_vente_ouvre_page_point_de_vente():
    app = _app()
    window = MainWindow(session_utilisateur=_session(ROLE_VENDEUR))

    page = window._page_widgets["nouvelle_vente"]

    assert isinstance(page, NouvelleVentePage)
    assert window.content_stack.currentIndex() == window._pages["dashboard"]

    window.close()
    app.processEvents()


def test_page_nouvelle_vente_panier_total_et_accessibilite_encaissement():
    app = _app()
    page = NouvelleVentePage(
        session_utilisateur=_session(ROLE_VENDEUR),
        vente_service=_FakeVenteService(),
        produit_service=_FakeProduitService(),
        autoload=True,
    )

    produit = page._produits[0]
    page._ajouter_au_panier(produit)
    app.processEvents()

    assert page.total_label.text() == "1 000 CDF"
    assert page.items_count_label.text() == "1 article(s)"
    assert page.received_input.value() == 1000
    assert page.cash_button.isEnabled()
    assert "Pret a encaisser" in page.payment_hint_label.text()

    page.received_input.setValue(500)
    app.processEvents()

    assert page.cash_button.isEnabled()
    assert "inferieur" in page.payment_hint_label.text()

    page.close()
    app.processEvents()


def test_page_nouvelle_vente_ne_scrolle_pas_en_plein_ecran():
    app = _app()
    window = MainWindow(session_utilisateur=_session(ROLE_VENDEUR))
    page = window._page_widgets["nouvelle_vente"]
    page._vente_service = _FakeVenteService()
    page._produit_service = _FakeProduitService()

    window.resize(1450, 900)
    window.show()
    window.navigate("nouvelle_vente")
    app.processEvents()
    scroll = window.content_stack.currentWidget()
    cash_bottom = page.cash_button.mapTo(scroll.viewport(), page.cash_button.rect().bottomRight()).y()

    assert scroll.verticalScrollBar().maximum() == 0
    assert cash_bottom <= scroll.viewport().height()

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


def test_page_stock_ne_scrolle_pas_en_plein_ecran():
    app = _app()
    window = MainWindow(session_utilisateur=_session(ROLE_GERANT))
    page = window._page_widgets["stock"]

    window.resize(1450, 900)
    window.show()
    window.navigate("stock")
    app.processEvents()
    scroll = window.content_stack.currentWidget()
    price_bottom = page.entry_price_input.geometry().bottom()
    checkbox_top = page.entry_expiration_known.geometry().top()
    checkbox_right = page.entry_expiration_known.geometry().right()
    date_left = page.entry_expiration_input.geometry().left()
    submit_bottom = page.entry_submit_button.mapTo(page.side_scroll.viewport(), page.entry_submit_button.rect().bottomRight()).y()

    assert scroll.verticalScrollBar().maximum() == 0
    assert page.entry_quantity_input.height() >= 36
    assert page.entry_price_input.height() >= 36
    assert price_bottom + 12 <= checkbox_top
    assert checkbox_right + 8 <= date_left
    assert submit_bottom <= page.side_scroll.viewport().height()

    window.close()
    app.processEvents()


def test_bloc_utilisateur_affiche_identite_reelle_sans_page_profil():
    app = _app()
    window = MainWindow(session_utilisateur=_session(ROLE_GERANT))

    labels = [label.text() for label in window.findChildren(QLabel)]
    assert "Utilisateur Test" in labels
    assert "profil" not in window._pages

    window.close()
    app.processEvents()


def test_photo_profil_non_persistante_est_retiree():
    app = _app()
    window = MainWindow(session_utilisateur=_session(ROLE_GERANT))

    assert not window.findChildren(QPushButton, "profileButton")
    assert "Choisir une photo de profil" not in _button_texts(window)

    window.close()
    app.processEvents()


def test_parametres_ne_propose_plus_de_changement_de_theme():
    app = _app()
    window = MainWindow(session_utilisateur=_session(ROLE_GERANT))

    window.navigate("parametres")
    radios = {radio.text().strip() for radio in window.findChildren(QRadioButton)}

    assert "Clair" not in radios
    assert "Sombre" not in radios
    assert window.findChild(BackupPanel) is not None
    field_labels = {
        label.text()
        for label in window._page_widgets["parametres"].findChildren(QLabel)
        if label.objectName() == "settingsFieldLabel"
    }
    assert {
        "Nom de la pharmacie *",
        "Telephone",
        "Adresse",
        "Mot de passe actuel",
        "Automatisation",
    } <= field_labels

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
        "Recherche produit",
        "Factures",
        "Deconnexion",
    ):
        assert label in labels
    for forbidden in ("Stock", "Ventes", "Rapports", "Vendeurs", "Historique", "Alertes", "Parametres"):
        assert forbidden not in labels

    window.navigate("produits")
    assert window.topbar.title_label.text() == "Recherche produit"

    window.close()
    app.processEvents()


def test_parametres_gerant_affiche_backup_sans_exposer_au_vendeur():
    app = _app()
    gerant_window = MainWindow(session_utilisateur=_session(ROLE_GERANT))
    vendeur_window = MainWindow(session_utilisateur=_session(ROLE_VENDEUR))

    gerant_window.navigate("parametres")
    panel = gerant_window.findChild(BackupPanel)
    button_labels = {
        button.text().strip() for button in panel.findChildren(QPushButton)
    }

    assert panel is not None
    assert "Exporter les donnees" in button_labels
    assert "Importer une sauvegarde" in button_labels
    assert "Enregistrer les réglages" in button_labels
    assert panel.auto_checkbox.accessibleName() == "Activer les sauvegardes automatiques"
    assert panel.frequency_combo.accessibleName() == "Fréquence des sauvegardes automatiques"
    assert vendeur_window.findChild(BackupPanel) is None

    gerant_window.close()
    vendeur_window.close()
    app.processEvents()


def test_ecrans_gerant_exposent_les_exports_excel_accessibles():
    app = _app()
    window = MainWindow(session_utilisateur=_session(ROLE_GERANT))

    pages = (
        window._page_widgets["produits"],
        window._page_widgets["stock"],
        window._page_widgets["ventes"],
        window._page_widgets["rapports"],
    )
    accessible_names = {
        page.export_button.accessibleName()
        for page in pages
    }

    assert isinstance(pages[0], ProduitsPage)
    assert isinstance(pages[1], StockPage)
    assert isinstance(pages[2], HistoriqueVentesGerantPage)
    assert isinstance(pages[3], RapportsPage)
    assert accessible_names == {
        "Exporter la liste des produits en Excel",
        "Exporter le stock en Excel",
        "Exporter l'historique des ventes en Excel",
        "Exporter le rapport en Excel",
    }

    window.close()
    app.processEvents()


def test_navigation_affiche_ecran_factures_complet():
    app = _app()
    window = MainWindow(session_utilisateur=_session(ROLE_VENDEUR))

    window.navigate("factures")
    labels = [label.text() for label in window.findChildren(QLabel)]

    assert "Factures" in labels
    assert "Aperçu de la facture" in labels
    assert "Factures du jour" in labels
    assert "Montant total encaissé" in labels
    assert "Sélectionnez une facture dans la liste." in labels

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


class _FakeCategorie:
    def __init__(self, categorie_id: int, nom: str) -> None:
        self.id = categorie_id
        self.nom = nom


class _FakeVenteService:
    def __init__(self) -> None:
        self.produits = [
            ProduitVendable(
                produit_id=1,
                nom="Paracetamol 500mg",
                prix_vente=1000,
                stock_disponible=150,
                categorie_id=1,
                categorie_nom="Analgesiques",
                description="Boite de 20 comprimes",
            )
        ]

    def lister_produits_vendables(self, utilisateur, *, terme="", categorie_id=None, date_reference=None):
        return self.produits

    def valider_vente(self, utilisateur, payload, *, date_reference=None):
        raise AssertionError("Non utilise")


class _FakeUtilisateurService:
    def tableau_vendeurs(self, utilisateur, *, terme="", date_reference=None):
        return VendeurDashboardData(
            vendeurs=[
                VendeurListItem(
                    utilisateur_id=1,
                    nom="Jean K.",
                    identifiant="jean",
                    actif=True,
                    derniere_connexion="2026-06-26 10:42:00",
                    ventes_du_jour=562_300,
                ),
                VendeurListItem(
                    utilisateur_id=2,
                    nom="David N.",
                    identifiant="david",
                    actif=False,
                    derniere_connexion=None,
                    ventes_du_jour=0,
                ),
            ],
            metrics=VendeurMetrics(total_vendeurs=2, actifs=1, inactifs=1, ventes_du_jour=562_300),
        )

    def creer_vendeur(self, utilisateur, payload):
        raise AssertionError("Non utilise")

    def desactiver_vendeur(self, utilisateur, *, vendeur_id: int):
        raise AssertionError("Non utilise")

    def reactiver_vendeur(self, utilisateur, *, vendeur_id: int):
        raise AssertionError("Non utilise")
