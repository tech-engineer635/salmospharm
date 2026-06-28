"""Ecran de connexion PySide6 de SALMOSPHARM 133."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.core.exceptions import AuthentificationError, UtilisateurInactifError, ValidationError
from app.services.auth_service import AuthService
from app.ui.components.icons import ui_icon


class LoginWindow(QMainWindow):
    """Fenetre de connexion visuelle, sans logique metier d'authentification embarquee."""

    connexion_reussie = Signal(object)

    def __init__(self, auth_service: AuthService | None = None) -> None:
        super().__init__()
        self._auth_service = auth_service or AuthService()
        self._password_visible = False

        self.setWindowTitle("SALMOSPHARM 133")
        self.setMinimumSize(1024, 640)
        self.resize(1280, 760)
        self.setFont(QFont("Segoe UI", 10))

        self._build_ui()
        self._apply_style()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("loginRoot")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        content = QWidget()
        content.setObjectName("contentArea")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self._build_brand_panel(), 49)
        content_layout.addWidget(self._build_login_area(), 51)

        root_layout.addWidget(content, 1)
        self.setCentralWidget(root)

    def _build_brand_panel(self) -> QWidget:
        panel = BrandPanel()
        panel.setObjectName("brandPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(50, 54, 50, 30)
        layout.setSpacing(0)

        layout.addStretch(2)

        logo = QLabel()
        logo.setObjectName("mainLogo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(str(_asset_path("logo.png")))
        if not pixmap.isNull():
            logo.setPixmap(
                pixmap.scaled(
                    300,
                    250,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            logo.setText("SALMOSPHARM")
        layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel("SALMOSPHARM")
        title.setObjectName("brandTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        badge_row = QHBoxLayout()
        badge_row.setContentsMargins(0, 0, 0, 0)
        badge_row.setSpacing(10)
        badge_row.addStretch(1)
        badge_row.addWidget(_divider())
        badge = QLabel("133")
        badge.setObjectName("brandBadge")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_row.addWidget(badge)
        badge_row.addWidget(_divider())
        badge_row.addStretch(1)
        layout.addLayout(badge_row)

        subtitle = QLabel("Votre sante, notre priorite")
        subtitle.setObjectName("brandSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        layout.addStretch(4)
        layout.addWidget(self._build_features())
        return panel

    def _build_features(self) -> QWidget:
        container = QWidget()
        container.setObjectName("featureRow")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(26)
        layout.addWidget(self._feature("shield", "Securite", "Vos donnees sont\nprotegees"))
        layout.addWidget(self._feature("team", "Fiable", "Gestion efficace de\nvotre pharmacie"))
        layout.addWidget(self._feature("leaf", "Performant", "Concu pour simplifier\nvotre quotidien"))
        return container

    def _feature(self, icon_name: str, title: str, body: str) -> QWidget:
        wrapper = QWidget()
        wrapper.setObjectName("featureItem")
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        icon = IconBubble(icon_name)
        icon.setFixedSize(44, 44)
        layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignTop)

        texts = QVBoxLayout()
        texts.setContentsMargins(0, 0, 0, 0)
        texts.setSpacing(4)
        title_label = QLabel(title)
        title_label.setObjectName("featureTitle")
        body_label = QLabel(body)
        body_label.setObjectName("featureBody")
        texts.addWidget(title_label)
        texts.addWidget(body_label)
        layout.addLayout(texts)
        return wrapper

    def _build_login_area(self) -> QWidget:
        area = LoginBackground()
        area.setObjectName("loginArea")
        layout = QVBoxLayout(area)
        layout.setContentsMargins(54, 36, 64, 36)
        layout.setSpacing(0)
        layout.addStretch(1)
        layout.addWidget(self._build_login_card(), alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)
        return area

    def _build_login_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedWidth(520)
        card.setMinimumHeight(568)

        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(34)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor("#dbe4ee"))
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(42, 34, 42, 34)
        layout.setSpacing(0)

        avatar = QLabel()
        avatar.setObjectName("avatar")
        avatar.setFixedSize(78, 78)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setPixmap(ui_icon("user", "#073a63", 46).pixmap(46, 46))
        layout.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Bienvenue")
        title.setObjectName("loginTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(16)
        layout.addWidget(title)

        subtitle = QLabel("Connectez-vous a votre espace SALMOSPHARM 133")
        subtitle.setObjectName("loginSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(8)
        layout.addWidget(subtitle)

        layout.addSpacing(24)
        self.identifiant_input = self._field(layout, "Nom d'utilisateur", "Entrez votre nom d'utilisateur")
        layout.addSpacing(14)
        self.password_input = self._field(layout, "Mot de passe", "Entrez votre mot de passe", password=True)

        layout.addSpacing(18)
        options = QHBoxLayout()
        options.setContentsMargins(0, 0, 0, 0)
        options.setSpacing(0)
        self.remember_checkbox = QCheckBox("Se souvenir de moi")
        self.remember_checkbox.setObjectName("rememberCheck")
        self.remember_checkbox.setChecked(True)
        options.addWidget(self.remember_checkbox)
        options.addStretch(1)
        forgot_button = QPushButton("Mot de passe oublie ?")
        forgot_button.setObjectName("linkButton")
        forgot_button.clicked.connect(self._show_recovery_unavailable)
        options.addWidget(forgot_button)
        layout.addLayout(options)

        layout.addSpacing(24)
        self.login_button = QPushButton("Se connecter")
        self.login_button.setObjectName("loginButton")
        self.login_button.setIcon(ui_icon("lock", "#ffffff", 24))
        self.login_button.clicked.connect(self._submit)
        layout.addWidget(self.login_button)

        layout.addSpacing(30)
        layout.addWidget(self._build_security_notice())
        return card

    def _field(self, parent_layout: QVBoxLayout, label_text: str, placeholder: str, password: bool = False) -> QLineEdit:
        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        parent_layout.addWidget(label)
        parent_layout.addSpacing(8)

        frame = QFrame()
        frame.setObjectName("inputFrame")
        frame_layout = QHBoxLayout(frame)
        frame_layout.setContentsMargins(14, 0, 12, 0)
        frame_layout.setSpacing(12)

        icon = QLabel()
        icon.setObjectName("inputIcon")
        icon.setFixedSize(22, 22)
        pixmap = ui_icon("lock" if password else "user", "#657282", 20).pixmap(20, 20)
        icon.setPixmap(pixmap)
        frame_layout.addWidget(icon)

        line_edit = QLineEdit()
        line_edit.setObjectName("authInput")
        line_edit.setPlaceholderText(placeholder)
        line_edit.setFrame(False)
        if password:
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)
        frame_layout.addWidget(line_edit, 1)

        if password:
            toggle = QToolButton()
            toggle.setObjectName("passwordToggle")
            toggle.setIcon(ui_icon("eye", "#657282", 20))
            toggle.clicked.connect(self._toggle_password_visibility)
            frame_layout.addWidget(toggle)

        parent_layout.addWidget(frame)
        return line_edit

    def _build_security_notice(self) -> QWidget:
        notice = QFrame()
        notice.setObjectName("securityNotice")
        notice.setFixedHeight(64)
        layout = QHBoxLayout(notice)
        layout.setContentsMargins(18, 10, 18, 10)
        layout.setSpacing(14)

        icon = IconBubble("access")
        icon.setFixedSize(34, 34)
        layout.addWidget(icon)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)
        first = QLabel("Acces reserve au personnel autorise.")
        first.setObjectName("noticeText")
        second = QLabel("Gerant et Vendeur uniquement.")
        second.setObjectName("noticeStrong")
        text_layout.addWidget(first)
        text_layout.addWidget(second)
        layout.addLayout(text_layout, 1)
        return notice

    def _toggle_password_visibility(self) -> None:
        self._password_visible = not self._password_visible
        mode = QLineEdit.EchoMode.Normal if self._password_visible else QLineEdit.EchoMode.Password
        self.password_input.setEchoMode(mode)

    def _submit(self) -> None:
        identifiant = self.identifiant_input.text().strip()
        mot_de_passe = self.password_input.text()

        if not identifiant or not mot_de_passe:
            QMessageBox.warning(self, "Validation", "Veuillez saisir votre identifiant et votre mot de passe.")
            return

        connecter = getattr(self._auth_service, "connecter", None)
        if not callable(connecter):
            QMessageBox.information(
                self,
                "Connexion",
                "L'ecran de connexion est pret. Le service de connexion doit encore etre branche.",
            )
            return

        try:
            utilisateur_connecte = connecter(identifiant=identifiant, mot_de_passe=mot_de_passe)
        except (AuthentificationError, UtilisateurInactifError, ValidationError) as exc:
            QMessageBox.warning(self, "Connexion impossible", str(exc))
            return
        except Exception:
            QMessageBox.critical(
                self,
                "Connexion impossible",
                "Impossible de se connecter pour le moment. Veuillez reessayer.",
            )
            return

        self.connexion_reussie.emit(utilisateur_connecte)

    def _show_recovery_unavailable(self) -> None:
        QMessageBox.information(
            self,
            "Mot de passe oublie",
            "La recuperation par code sera disponible dans une prochaine etape.",
        )

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QWidget#loginRoot,
            QWidget#contentArea {
                background-color: #f7fafc;
            }
            BrandPanel#brandPanel {
                background-color: #eef6fb;
            }
            QLabel#mainLogo {
                min-height: 238px;
            }
            QLabel#brandTitle {
                color: #0b6f22;
                font-size: 52px;
                font-weight: 900;
            }
            QLabel#brandBadge {
                background-color: #073a63;
                border-radius: 17px;
                color: white;
                font-size: 23px;
                font-weight: 900;
                padding: 0 18px;
                min-height: 30px;
            }
            QFrame#brandLine {
                background-color: #0b426c;
                max-height: 2px;
                min-width: 102px;
            }
            QLabel#brandSubtitle {
                color: #3d4754;
                font-size: 22px;
                padding-top: 8px;
            }
            QLabel#featureTitle {
                color: #0b1f35;
                font-size: 14px;
                font-weight: 800;
            }
            QLabel#featureBody {
                color: #536273;
                font-size: 12px;
                line-height: 16px;
            }
            LoginBackground#loginArea {
                background-color: #fbfcfe;
            }
            QFrame#loginCard {
                background-color: rgba(255, 255, 255, 245);
                border: 1px solid #e8edf3;
                border-radius: 18px;
            }
            QLabel#avatar {
                background-color: #ffffff;
                border: 1px solid #e1e7ef;
                border-radius: 50px;
            }
            QLabel#loginTitle {
                color: #083056;
                font-size: 36px;
                font-weight: 900;
            }
            QLabel#loginSubtitle {
                color: #4c5868;
                font-size: 14px;
            }
            QLabel#fieldLabel {
                color: #10243b;
                font-size: 15px;
                font-weight: 800;
            }
            QFrame#inputFrame {
                background-color: #ffffff;
                border: 1px solid #dce3eb;
                border-radius: 7px;
                min-height: 52px;
            }
            QFrame#inputFrame:focus-within {
                border: 1px solid #0c5f8d;
            }
            QLineEdit#authInput {
                background: transparent;
                color: #12263a;
                font-size: 15px;
                selection-background-color: #d8edf8;
            }
            QLineEdit#authInput::placeholder {
                color: #9aa5b1;
            }
            QLabel#inputIcon {
                color: #6b7684;
            }
            QToolButton#passwordToggle {
                background: transparent;
                border: none;
                padding: 4px;
            }
            QCheckBox#rememberCheck {
                color: #152536;
                font-size: 14px;
                font-weight: 700;
                spacing: 12px;
            }
            QCheckBox#rememberCheck::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 1px solid #2f8f33;
                background-color: #ffffff;
            }
            QCheckBox#rememberCheck::indicator:checked {
                background-color: #2f9a3a;
                image: url(__CHECK_ICON__);
            }
            QPushButton#linkButton {
                background: transparent;
                border: none;
                color: #0a4570;
                font-size: 14px;
                font-weight: 700;
                text-decoration: underline;
                padding: 0;
            }
            QPushButton#loginButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #35a72f, stop:1 #003e68);
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 16px;
                font-weight: 800;
                min-height: 50px;
            }
            QPushButton#loginButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2c9629, stop:1 #003558);
            }
            QFrame#securityNotice {
                background-color: #f1fbf3;
                border: 1px solid #cce8d0;
                border-radius: 8px;
            }
            QLabel#noticeText {
                color: #16682d;
                font-size: 13px;
            }
            QLabel#noticeStrong {
                color: #0d6126;
                font-size: 13px;
                font-weight: 800;
            }
            """
            .replace("__CHECK_ICON__", _asset_path("check.svg").as_posix())
        )


class BrandPanel(QFrame):
    """Panneau gauche peint pour rappeler la maquette de connexion."""

    def paintEvent(self, event: Any) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#f2f8fc"))
        painter.drawRect(self.rect())

        painter.setOpacity(0.42)
        _draw_cross(painter, 70, 66, 82, "#dcecf4")
        _draw_cross(painter, 54, 225, 118, "#dcecf4")
        _draw_cross(painter, 468, 72, 28, "#d5e8f1")
        painter.setOpacity(1)

        logo_pixmap = QPixmap(str(_asset_path("logo.png")))
        if not logo_pixmap.isNull():
            soft_logo = logo_pixmap.scaled(
                int(self.width() * 0.58),
                int(self.height() * 0.42),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = int((self.width() - soft_logo.width()) / 2)
            y = int(self.height() * 0.17)
            painter.setOpacity(0.16)
            painter.drawPixmap(x - 4, y + 6, soft_logo)
            painter.setOpacity(0.10)
            painter.drawPixmap(x + 9, y - 2, soft_logo)
            painter.setOpacity(1)

        separator_y = self.height() - 182
        blue_curve = QPainterPath()
        blue_curve.moveTo(0, separator_y - 32)
        blue_curve.cubicTo(
            self.width() * 0.32,
            separator_y + 4,
            self.width() * 0.72,
            separator_y + 12,
            self.width(),
            separator_y - 64,
        )
        blue_curve.lineTo(self.width(), separator_y - 38)
        blue_curve.cubicTo(
            self.width() * 0.72,
            separator_y + 34,
            self.width() * 0.30,
            separator_y + 30,
            0,
            separator_y - 2,
        )
        blue_curve.closeSubpath()
        painter.setBrush(QColor("#1f78a7"))
        painter.drawPath(blue_curve)

        green_curve = QPainterPath()
        green_curve.moveTo(0, separator_y - 4)
        green_curve.cubicTo(
            self.width() * 0.34,
            separator_y + 24,
            self.width() * 0.72,
            separator_y + 30,
            self.width(),
            separator_y - 34,
        )
        green_curve.lineTo(self.width(), separator_y + 2)
        green_curve.cubicTo(
            self.width() * 0.72,
            separator_y + 56,
            self.width() * 0.30,
            separator_y + 48,
            0,
            separator_y + 24,
        )
        green_curve.closeSubpath()
        painter.setBrush(QColor("#47a52a"))
        painter.drawPath(green_curve)


class LoginBackground(QFrame):
    """Fond droit avec motifs medicaux tres discrets."""

    def paintEvent(self, event: Any) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(0.2)
        _draw_cross(painter, self.width() - 90, 52, 62, "#d8e4ec")
        _draw_cross(painter, self.width() - 62, 20, 30, "#d8e4ec")
        _draw_cross(painter, self.width() - 72, self.height() - 108, 76, "#d8e4ec")
        painter.setOpacity(1)


class IconBubble(QWidget):
    """Petit pictogramme dessine en QPainter pour eviter les assets externes."""

    def __init__(self, icon_name: str) -> None:
        super().__init__()
        self._icon_name = icon_name

    def paintEvent(self, event: Any) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = "#1c8b35" if self._icon_name != "team" else "#073a63"
        painter.setPen(QColor(color))

        width = self.width()
        height = self.height()
        if self._icon_name == "shield":
            path = QPainterPath()
            path.moveTo(width * 0.50, height * 0.08)
            path.lineTo(width * 0.86, height * 0.22)
            path.lineTo(width * 0.80, height * 0.58)
            path.cubicTo(width * 0.76, height * 0.76, width * 0.62, height * 0.88, width * 0.50, height * 0.94)
            path.cubicTo(width * 0.38, height * 0.88, width * 0.24, height * 0.76, width * 0.20, height * 0.58)
            path.lineTo(width * 0.14, height * 0.22)
            path.closeSubpath()
            painter.setBrush(QColor("#e6f6e9"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(path)
            painter.setPen(QColor(color))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)
        elif self._icon_name == "team":
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QColor("#073a63"))
            painter.drawEllipse(width * 0.30, height * 0.08, width * 0.32, height * 0.32)
            painter.drawArc(width * 0.18, height * 0.42, width * 0.50, height * 0.44, 0, 180 * 16)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#111827"))
            painter.drawEllipse(width * 0.63, height * 0.38, width * 0.22, height * 0.22)
            painter.drawRoundedRect(width * 0.56, height * 0.66, width * 0.34, height * 0.20, 6, 6)
        elif self._icon_name == "leaf":
            path = QPainterPath()
            path.moveTo(width * 0.16, height * 0.78)
            path.cubicTo(width * 0.30, height * 0.22, width * 0.78, height * 0.22, width * 0.86, height * 0.08)
            path.cubicTo(width * 0.88, height * 0.58, width * 0.56, height * 0.84, width * 0.16, height * 0.78)
            painter.drawPath(path)
            painter.drawLine(width * 0.16, height * 0.78, width * 0.66, height * 0.42)
        else:
            painter.drawEllipse(width * 0.22, height * 0.18, width * 0.38, height * 0.38)
            painter.drawRect(width * 0.22, height * 0.52, width * 0.48, height * 0.34)
            painter.drawEllipse(width * 0.58, height * 0.56, width * 0.24, height * 0.24)


def _asset_path(file_name: str) -> Path:
    return Path(__file__).resolve().parents[2] / "assets" / file_name


def _divider() -> QFrame:
    frame = QFrame()
    frame.setObjectName("brandLine")
    frame.setFixedHeight(2)
    return frame


def _user_icon(color: str, size: int = 24) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor(color), max(1.8, size * 0.085), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(size * 0.36, size * 0.16, size * 0.28, size * 0.28)
    painter.drawArc(size * 0.22, size * 0.48, size * 0.56, size * 0.34, 0, 180 * 16)
    painter.end()
    return QIcon(pixmap)


def _lock_icon(color: str, size: int = 24) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    scale = size / 24
    painter.setPen(QPen(QColor(color), 2.3 * scale, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(6 * scale, 10 * scale, 12 * scale, 10 * scale, 2.5 * scale, 2.5 * scale)
    painter.drawArc(8 * scale, 4 * scale, 8 * scale, 10 * scale, 0, 180 * 16)
    painter.setBrush(QColor(color))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(11 * scale, 14 * scale, 2.6 * scale, 2.6 * scale)
    painter.end()
    return QIcon(pixmap)


def _eye_icon(color: str) -> QIcon:
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor(color), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(3, 12)
    path.cubicTo(6, 7, 18, 7, 21, 12)
    path.cubicTo(18, 17, 6, 17, 3, 12)
    painter.drawPath(path)
    painter.drawEllipse(9, 9, 6, 6)
    painter.end()
    return QIcon(pixmap)




def _draw_cross(painter: QPainter, x: int, y: int, size: int, color: str) -> None:
    painter.setBrush(QColor(color))
    painter.setPen(Qt.PenStyle.NoPen)
    thickness = max(8, int(size * 0.34))
    offset = int((size - thickness) / 2)
    painter.drawRoundedRect(x + offset, y, thickness, size, 4, 4)
    painter.drawRoundedRect(x, y + offset, size, thickness, 4, 4)
