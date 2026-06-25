import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

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
    assert window.remember_checkbox.isChecked()

    window.close()
    app.processEvents()
