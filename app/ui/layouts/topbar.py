"""Topbar principale de l'espace connecte."""

from __future__ import annotations

from PySide6.QtCore import QSize, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from app.services.auth_service import SessionUtilisateur
from app.ui.components.icons import ui_icon


class Topbar(QFrame):
    """Affiche le contexte utilisateur et une action de deconnexion."""

    deconnexion_demandee = Signal()
    menu_demande = Signal()

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
            self.subtitle_label.setText("Bienvenue, Jean K. ! Voici un apercu de vos activites aujourd'hui.")
        else:
            self.subtitle_label.setText("Bienvenue, Gerant")

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
        menu_button.clicked.connect(self.menu_demande.emit)
        title_block.addWidget(menu_button)
        self.title_label.setObjectName("topbarTitle")
        self.subtitle_label.setObjectName("topbarSubtitle")
        title_block.addWidget(self.title_label)
        title_block.addWidget(self.subtitle_label)
        layout.addLayout(title_block, 1)

        search = QLineEdit()
        search.setObjectName("topbarSearch")
        search.addAction(ui_icon("search"), QLineEdit.ActionPosition.TrailingPosition)
        search.setPlaceholderText(
            "Rechercher (produits, ventes, factures...)" if self.session_utilisateur.role == "GERANT"
            else "Rechercher (produits, clients...)"
        )
        search.setFixedWidth(350)
        layout.addWidget(search)

        date_button = QPushButton("24 mai 2024   >")
        date_button.setObjectName("dateButton")
        date_button.setIcon(ui_icon("calendar"))
        date_button.setIconSize(QSize(20, 20))
        date_button.setFixedWidth(178)
        layout.addWidget(date_button)

        bell = QPushButton("")
        bell.setObjectName("bellButton")
        bell.setIcon(ui_icon("bell", "#108d38"))
        bell.setIconSize(QSize(22, 22))
        bell.setFixedSize(46, 46)
        layout.addWidget(bell)
