import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtTest import QTest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QCheckBox

from app.main import MainWindow
from app.services.auth_service import SessionUtilisateur
from app.ui.login import LoginWindow


class _AuthServiceSansConnexion:
    pass


def test_login_window_affiche_les_elements_principaux():
    app = QApplication.instance() or QApplication([])

    window = LoginWindow(auth_service=_AuthServiceSansConnexion())

    assert window.windowTitle() == "SALMOSPHARM 133"
    assert window.identifiant_input.placeholderText() == "Entrez votre nom d'utilisateur"
    assert window.password_input.placeholderText() == "Entrez votre mot de passe"
    assert window.login_button.text().strip() == "Se connecter"
    assert not any(
        checkbox.text() == "Se souvenir de moi"
        for checkbox in window.findChildren(QCheckBox)
    )
    assert window.login_button.isDefault()
    assert window.identifiant_input.accessibleName()
    assert window.password_input.accessibleName()

    window.close()
    app.processEvents()


class _AuthServiceAvecConnexion:
    def __init__(self, role: str = "GERANT") -> None:
        self.role = role

    def connecter(self, *, identifiant: str, mot_de_passe: str) -> SessionUtilisateur:
        return SessionUtilisateur(
            utilisateur_id=7,
            nom="Gerant Test" if self.role == "GERANT" else "Vendeur Test",
            identifiant=identifiant,
            role=self.role,
        )


def test_login_window_emet_session_apres_connexion_reussie():
    app = QApplication.instance() or QApplication([])
    window = LoginWindow(auth_service=_AuthServiceAvecConnexion())
    sessions = []

    window.connexion_reussie.connect(sessions.append)
    window.identifiant_input.setText("gerant")
    window.password_input.setText("abcde")
    window.login_button.click()

    assert len(sessions) == 1
    assert sessions[0].nom == "Gerant Test"
    assert sessions[0].role == "GERANT"

    window.close()
    app.processEvents()


def test_entree_depuis_mot_de_passe_valide_la_connexion():
    app = QApplication.instance() or QApplication([])
    window = LoginWindow(auth_service=_AuthServiceAvecConnexion())
    sessions = []
    window.connexion_reussie.connect(sessions.append)
    window.identifiant_input.setText("gerant")
    window.password_input.setText("abcde")
    window.password_input.setFocus()

    QTest.keyClick(window.password_input, Qt.Key.Key_Return)

    assert len(sessions) == 1
    window.close()
    app.processEvents()


def test_clic_se_connecter_ouvre_interface_selon_role():
    app = QApplication.instance() or QApplication([])

    for role, menu_attendu, menu_interdit in (
        ("GERANT", "Parametres", "Historique des ventes"),
        ("VENDEUR", "Nouvelle vente", "Parametres"),
    ):
        login = LoginWindow(auth_service=_AuthServiceAvecConnexion(role))
        opened_windows = []

        def ouvrir_interface(session: SessionUtilisateur) -> None:
            opened_windows.append(MainWindow(session_utilisateur=session))

        login.connexion_reussie.connect(ouvrir_interface)
        login.identifiant_input.setText(role.lower())
        login.password_input.setText("abcde")
        login.login_button.click()

        assert len(opened_windows) == 1
        main_window = opened_windows[0]
        assert main_window.session_utilisateur.role == role
        assert menu_attendu in main_window.sidebar.menu_labels
        assert menu_interdit not in main_window.sidebar.menu_labels

        main_window.close()
        login.close()
        app.processEvents()
