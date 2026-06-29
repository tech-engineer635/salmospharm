"""Topbar principale de l'espace connecte."""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from app.services.auth_service import SessionUtilisateur
from app.ui.components.icons import ui_icon


class Topbar(QFrame):
    """Affiche le contexte utilisateur et une action de deconnexion."""

    deconnexion_demandee = Signal()
    menu_demande = Signal()
    recherche_demandee = Signal(str)
    alertes_demandees = Signal()

    def __init__(self, session_utilisateur: SessionUtilisateur, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session_utilisateur = session_utilisateur
        self.title_label = QLabel("")
        self.subtitle_label = QLabel("")
        self.user_name_label = QLabel(session_utilisateur.nom)
        self.user_role_label = QLabel(session_utilisateur.role)
        self.setObjectName("topbar")
        self.setFixedHeight(154)
        self._build_ui()

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)
        if not title:
            self.subtitle_label.setText("")
        elif self.session_utilisateur.role == "VENDEUR":
            self.subtitle_label.setText(
                f"Bienvenue, {self.session_utilisateur.nom} ! Voici vos activites."
            )
        else:
            self.subtitle_label.setText(f"Bienvenue, {self.session_utilisateur.nom}")

    def set_reports_mode(self, enabled: bool) -> None:
        """Compacte la topbar quand la page possede son propre en-tete complet."""

        self.setFixedHeight(62 if enabled else 154)
        self.title_label.setVisible(not enabled)
        self.subtitle_label.setVisible(not enabled)
        self.search_input.setVisible(not enabled)
        self.date_button.setVisible(not enabled)
        self.bell_button.setVisible(not enabled)

    def set_alert_count(self, count: int) -> None:
        self.bell_button.setText(str(count) if count > 0 else "")
        self.bell_button.setToolTip(
            f"{count} alerte(s) non lue(s)" if count else "Aucune alerte non lue"
        )

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(32, 22, 32, 16)
        layout.setSpacing(18)

        title_block = QVBoxLayout()
        title_block.setContentsMargins(0, 0, 0, 0)
        title_block.setSpacing(10)
        menu_button = QPushButton("")
        menu_button.setObjectName("menuButton")
        menu_button.setIcon(ui_icon("menu"))
        menu_button.setIconSize(QSize(22, 22))
        menu_button.setFixedSize(38, 38)
        menu_button.setAccessibleName("Afficher ou masquer le menu")
        menu_button.clicked.connect(self.menu_demande.emit)
        title_block.addWidget(menu_button, alignment=Qt.AlignmentFlag.AlignLeft)
        self.title_label.setObjectName("topbarTitle")
        self.subtitle_label.setObjectName("topbarSubtitle")
        title_block.addWidget(self.title_label)
        title_block.addWidget(self.subtitle_label)
        layout.addLayout(title_block, 1)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("topbarSearch")
        self.search_input.addAction(ui_icon("search"), QLineEdit.ActionPosition.TrailingPosition)
        self.search_input.setPlaceholderText(
            "Rechercher un produit (nom ou code-barres)"
        )
        self.search_input.setAccessibleName("Recherche globale de produits")
        self.search_input.returnPressed.connect(
            lambda: self.recherche_demandee.emit(self.search_input.text().strip())
        )
        self.search_input.setFixedWidth(350)
        layout.addWidget(self.search_input)

        self.date_button = QPushButton(date.today().strftime("%d/%m/%Y"))
        self.date_button.setObjectName("dateButton")
        self.date_button.setIcon(ui_icon("calendar"))
        self.date_button.setIconSize(QSize(20, 20))
        self.date_button.setFixedWidth(178)
        self.date_button.setEnabled(False)
        self.date_button.setAccessibleName("Date actuelle")
        layout.addWidget(self.date_button)

        self.bell_button = QPushButton("")
        self.bell_button.setObjectName("bellButton")
        self.bell_button.setIcon(ui_icon("bell", "#108d38"))
        self.bell_button.setIconSize(QSize(22, 22))
        self.bell_button.setFixedSize(46, 46)
        self.bell_button.setAccessibleName("Ouvrir les alertes")
        self.bell_button.clicked.connect(self.alertes_demandees.emit)
        layout.addWidget(self.bell_button)
