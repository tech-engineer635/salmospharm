import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.first_run.manager_account_window import FirstRunWindow


class _AuthServiceFactice:
    pass


def test_first_run_link_demande_ecran_connexion():
    app = QApplication.instance() or QApplication([])
    window = FirstRunWindow(auth_service=_AuthServiceFactice())
    appels = []

    window.connexion_demandee.connect(lambda: appels.append(True))
    window._request_login()

    assert appels == [True]

    window.close()
    app.processEvents()
