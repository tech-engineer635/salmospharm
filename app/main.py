"""Point d'entree de SALMOSPHARM 133."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import QProcess
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox

from app.core.paths import ensure_app_directories, get_logs_dir
from app.database.init_db import init_database
from app.services.auth_service import AuthService, SessionUtilisateur
from app.services.backup_service import AutomaticBackupManager, BackupService
from app.services.alert_coordinator import AlertCoordinator
from app.ui.first_run.manager_account_window import FirstRunWindow
from app.ui.layouts import MainWindow
from app.ui.login import LoginWindow


def apply_style(app: QApplication) -> None:
    app.setStyleSheet("")


def configure_logging() -> None:
    """Conserve les erreurs techniques dans AppData sans les exposer à l'utilisateur."""

    logging.basicConfig(
        filename=get_logs_dir() / "salmospharm.log",
        level=logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        encoding="utf-8",
    )


def main() -> int:
    ensure_app_directories()
    configure_logging()
    init_database()

    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    apply_style(app)

    auth_service = AuthService()
    automatic_backup_manager = AutomaticBackupManager()
    app.aboutToQuit.connect(automatic_backup_manager.fermer_application)

    try:
        BackupService().finaliser_import_apres_redemarrage()
    except Exception:
        QMessageBox.warning(
            None,
            "SALMOSPHARM",
            "La restauration est terminee, mais sa journalisation n'a pas pu etre finalisee.",
        )

    def restart_application() -> None:
        arguments = [] if getattr(sys, "frozen", False) else [str(Path(__file__).resolve())]
        QProcess.startDetached(sys.executable, arguments)
        app.quit()

    def show_login_window() -> None:
        login_window = LoginWindow(auth_service=auth_service)

        def show_main_window_after_login(utilisateur_connecte: SessionUtilisateur) -> None:
            automatic_backup_manager.enregistrer_utilisation()
            alert_coordinator = AlertCoordinator()
            main_window = MainWindow(
                session_utilisateur=utilisateur_connecte,
                alert_coordinator=alert_coordinator,
            )
            app.main_window = main_window
            app.alert_coordinator = alert_coordinator
            alert_coordinator.demarrer()
            main_window.deconnexion_demandee.connect(alert_coordinator.arreter)
            main_window.deconnexion_demandee.connect(main_window.close)
            main_window.deconnexion_demandee.connect(show_login_window)
            main_window.redemarrage_demande.connect(restart_application)
            main_window.show()
            login_window.close()

        login_window.connexion_reussie.connect(show_main_window_after_login)
        app.login_window = login_window
        login_window.show()

    if auth_service.existe_utilisateur():
        show_login_window()
    else:
        first_run_window = FirstRunWindow(auth_service=auth_service)
        first_run_window.compte_cree.connect(show_login_window)
        first_run_window.connexion_demandee.connect(show_login_window)
        first_run_window.connexion_demandee.connect(first_run_window.close)
        first_run_window.show()
        app.first_run_window = first_run_window

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
