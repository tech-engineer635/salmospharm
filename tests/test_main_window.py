import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel

from app.main import MainWindow
from app.services.auth_service import SessionUtilisateur


def test_main_window_recoit_et_affiche_la_session_connectee():
    app = QApplication.instance() or QApplication([])
    session = SessionUtilisateur(
        utilisateur_id=1,
        nom="Gerant Principal",
        identifiant="gerant",
        role="GERANT",
    )

    window = MainWindow(session_utilisateur=session)
    labels = [label.text() for label in window.findChildren(QLabel)]

    assert window.session_utilisateur == session
    assert "Connecte : Gerant Principal (GERANT)" in labels

    window.close()
    app.processEvents()
