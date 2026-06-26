"""Sidebar principale de SALMOSPHARM selon le role connecte."""

from __future__ import annotations

from dataclasses import dataclass

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from app.core.constants import ROLE_GERANT, ROLE_VENDEUR
from app.ui.components.icons import ui_icon


@dataclass(frozen=True)
class NavigationItem:
    key: str
    label: str


MENU_GERANT: tuple[NavigationItem, ...] = (
    NavigationItem("dashboard", "Tableau de bord"),
    NavigationItem("produits", "Produits"),
    NavigationItem("stock", "Stock"),
    NavigationItem("ventes", "Ventes"),
    NavigationItem("factures", "Factures"),
    NavigationItem("rapports", "Rapports"),
    NavigationItem("vendeurs", "Vendeurs"),
    NavigationItem("historique", "Historique"),
    NavigationItem("alertes", "Alertes"),
    NavigationItem("parametres", "Parametres"),
)

MENU_VENDEUR: tuple[NavigationItem, ...] = (
    NavigationItem("dashboard", "Tableau de bord"),
    NavigationItem("nouvelle_vente", "Nouvelle vente"),
    NavigationItem("historique_ventes", "Historique des ventes"),
    NavigationItem("produits", "Recherche produit"),
    NavigationItem("factures", "Factures"),
)


class Sidebar(QFrame):
    """Menu lateral adapte au role, sans decision metier critique."""

    navigation_demandee = Signal(str)
    deconnexion_demandee = Signal()
    profil_demande = Signal()

    def __init__(self, role: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.role = role
        self._buttons: dict[str, QPushButton] = {}
        self.avatar_label: QLabel | None = None
        self.setObjectName("sidebar")
        self.setFixedWidth(296)
        self._build_ui()

    @property
    def menu_labels(self) -> list[str]:
        return [button.text().strip() for button in self._buttons.values()]

    def set_active(self, key: str) -> None:
        for item_key, button in self._buttons.items():
            button.setProperty("active", item_key == key)
            button.style().unpolish(button)
            button.style().polish(button)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 24, 0, 18)
        layout.setSpacing(0)

        logo = QLabel()
        logo.setObjectName("sidebarLogo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(str(_asset_path("logo.png")))
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaled(190, 190, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(logo)
        layout.addSpacing(18)

        nav_scroll = QScrollArea()
        nav_scroll.setObjectName("sidebarNavScroll")
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setFrameShape(QFrame.Shape.NoFrame)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(4)
        for item in _menu_for_role(self.role):
            button = QPushButton(item.label)
            button.setObjectName("navButton")
            button.setIcon(ui_icon(item.key))
            button.setIconSize(QSize(22, 22))
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked=False, key=item.key: self.navigation_demandee.emit(key))
            self._buttons[item.key] = button
            nav_layout.addWidget(button)

        nav_layout.addStretch(1)
        nav_scroll.setWidget(nav_container)
        layout.addWidget(nav_scroll, 1)
        layout.addSpacing(14)
        layout.addWidget(self._user_card())

    def _user_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("userCard")
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.mousePressEvent = lambda event: self.profil_demande.emit()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 14)
        card_layout.setSpacing(12)

        user_row = QHBoxLayout()
        avatar = QLabel("o")
        avatar.setObjectName("userAvatar")
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFixedSize(48, 48)
        self.avatar_label = avatar
        user_row.addWidget(avatar)

        texts = QVBoxLayout()
        texts.setSpacing(3)
        role_label = QLabel("Gerant" if self.role == ROLE_GERANT else "Vendeur")
        role_label.setObjectName("userRoleTitle")
        name_label = QLabel("Administrateur" if self.role == ROLE_GERANT else "Jean K.")
        name_label.setObjectName("userName")
        texts.addWidget(role_label)
        texts.addWidget(name_label)
        user_row.addLayout(texts, 1)
        card_layout.addLayout(user_row)

        separator = QFrame()
        separator.setObjectName("userSeparator")
        separator.setFixedHeight(1)
        card_layout.addWidget(separator)

        logout_button = QPushButton("Deconnexion")
        logout_button.setObjectName("logoutButton")
        logout_button.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_button.clicked.connect(self.deconnexion_demandee.emit)
        card_layout.addWidget(logout_button)
        return card

    def set_profile_photo(self, pixmap: QPixmap) -> None:
        if self.avatar_label is None or pixmap.isNull():
            return
        self.avatar_label.setText("")
        self.avatar_label.setPixmap(_circular_pixmap(pixmap, 48))


def _menu_for_role(role: str) -> tuple[NavigationItem, ...]:
    if role == ROLE_GERANT:
        return MENU_GERANT
    if role == ROLE_VENDEUR:
        return MENU_VENDEUR
    return ()


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
