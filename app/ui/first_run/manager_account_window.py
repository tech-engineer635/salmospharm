"""Ecran de creation du premier compte gerant."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.core.exceptions import ValidationError
from app.services.auth_service import AuthService
from app.ui.components.icons import ui_icon


class FirstRunWindow(QMainWindow):
    """Fenetre de premier lancement inspiree de la maquette fournie."""

    compte_cree = Signal()
    connexion_demandee = Signal()

    def __init__(self, auth_service: AuthService | None = None) -> None:
        super().__init__()
        self._auth_service = auth_service or AuthService()
        self.setWindowTitle("SALMOSPHARM 133")
        self.setMinimumSize(980, 620)
        self.resize(1440, 900)
        self.setFont(QFont("Segoe UI", 10))

        self._build_ui()
        self._apply_style()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_brand_panel(), 5)
        root_layout.addWidget(self._build_form_area(), 8)
        self.setCentralWidget(root)

    def _build_brand_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("brandPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(56, 54, 56, 54)
        layout.setSpacing(18)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo = QLabel()
        logo.setObjectName("brandLogo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = Path(__file__).resolve().parents[2] / "assets" / "logo.png"
        pixmap = QPixmap(str(logo_path))
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaled(270, 270, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            logo.setText("+")

        title = QLabel("SALMOSPHARM")
        title.setObjectName("brandTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        badge = QLabel("133")
        badge.setObjectName("brandBadge")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Votre sante, notre priorite")
        subtitle.setObjectName("brandSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addStretch(1)
        layout.addWidget(logo)
        layout.addWidget(title)
        layout.addWidget(badge, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        layout.addStretch(2)
        return panel

    def _build_form_area(self) -> QWidget:
        area = QWidget()
        area.setObjectName("formArea")
        area_layout = QVBoxLayout(area)
        area_layout.setContentsMargins(24, 32, 28, 32)

        scroll_area = QScrollArea()
        scroll_area.setObjectName("formScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.viewport().setAutoFillBackground(False)

        scroll_content = QWidget()
        scroll_content.setObjectName("formScrollContent")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("formCard")
        card.setMinimumWidth(660)
        card.setMinimumHeight(720)
        card.setMaximumWidth(780)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(50, 46, 50, 30)
        card_layout.setSpacing(24)

        title = QLabel("Creation du compte du gerant")
        title.setObjectName("formTitle")
        title.setMinimumHeight(48)
        card_layout.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(36)
        grid.setVerticalSpacing(28)
        for row in range(2):
            grid.setRowMinimumHeight(row, 92)

        self.nom_input = self._create_input("Entrez le nom complet")
        self.identifiant_input = self._create_input("Choisissez un nom d'utilisateur")
        self.password_input = self._create_input("Entrez un mot de passe securise", password=True)
        self.confirm_password_input = self._create_input("Confirmez le mot de passe", password=True)

        grid.addWidget(self._field("Nom complet *", self.nom_input), 0, 0)
        grid.addWidget(self._field("Nom d'utilisateur *", self.identifiant_input), 0, 1)
        grid.addWidget(self._field("Mot de passe *", self.password_input), 1, 0)
        grid.addWidget(self._field("Confirmer le mot de passe *", self.confirm_password_input), 1, 1)
        card_layout.addLayout(grid)

        options_container = QWidget()
        options_container.setMinimumHeight(68)
        options_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        options = QHBoxLayout(options_container)
        options.setSpacing(40)
        options.setContentsMargins(0, 10, 0, 6)
        self.accept_checkbox = QCheckBox("J'accepte de creer ce compte comme\nadministrateur principal.")
        self.accept_checkbox.setObjectName("acceptCheck")
        self.accept_checkbox.setChecked(True)
        self.show_password_checkbox = QCheckBox("Afficher le mot de passe")
        self.show_password_checkbox.stateChanged.connect(self._toggle_password_visibility)
        options.addWidget(self.accept_checkbox)
        options.addStretch(1)
        options.addWidget(self.show_password_checkbox)
        card_layout.addWidget(options_container)

        card_layout.addWidget(self._build_notice("shield", "Acces complet accorde", "Ce compte aura un acces total a toutes les fonctionnalites : produits, stock, ventes, vendeurs, rapports, alertes et parametres de l'application.", "success"))

        actions = QHBoxLayout()
        actions.setSpacing(26)
        cancel_button = QPushButton("Annuler")
        cancel_button.setObjectName("secondaryButton")
        cancel_button.clicked.connect(self.close)

        submit_button = QPushButton("Creer le compte du gerant")
        submit_button.setObjectName("primaryButton")
        submit_button.clicked.connect(self._submit)
        actions.addWidget(cancel_button, 1)
        actions.addStretch(1)
        actions.addWidget(submit_button, 3)
        card_layout.addLayout(actions)

        login_link = QLabel("<a href='#'>J'ai deja un compte</a>")
        login_link.setObjectName("loginLink")
        login_link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        login_link.setMinimumHeight(26)
        login_link.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        login_link.setOpenExternalLinks(False)
        login_link.linkActivated.connect(self._request_login)
        card_layout.addWidget(login_link)

        scroll_layout.addWidget(card)
        scroll_area.setWidget(scroll_content)
        area_layout.addWidget(scroll_area)
        return area

    def _field(self, label_text: str, input_widget: QLineEdit) -> QWidget:
        wrapper = QWidget()
        wrapper.setMinimumHeight(88)
        wrapper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        label.setMinimumHeight(20)
        layout.addWidget(label)
        layout.addWidget(input_widget)
        return wrapper

    def _create_input(self, placeholder: str, password: bool = False) -> QLineEdit:
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        line_edit.setFixedHeight(52)
        line_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if password:
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)
        return line_edit

    def _build_recovery_box(self) -> QWidget:
        box = QFrame()
        box.setObjectName("recoveryBox")
        box.setMinimumHeight(172)
        box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(16, 14, 16, 12)
        layout.setSpacing(10)

        title = QLabel("Code de recuperation")
        title.setObjectName("recoveryTitle")
        helper = QLabel("Le code de recuperation sera genere automatiquement apres la creation du compte.")
        helper.setObjectName("helperText")
        self.recovery_preview = QLineEdit("Code genere automatiquement par l'application")
        self.recovery_preview.setEnabled(False)
        self.recovery_preview.setFixedHeight(50)
        footer = QLabel("Conservez bien ce code apres la creation. Il vous permettra de recuperer l'acces a votre compte en cas d'oubli de mot de passe.")
        footer.setObjectName("smallText")
        footer.setWordWrap(True)
        footer.setMinimumHeight(38)

        layout.addWidget(title)
        layout.addWidget(helper)
        layout.addWidget(self.recovery_preview)
        layout.addWidget(footer)
        return box

    def _build_notice(self, icon: str, title: str, body: str, variant: str) -> QWidget:
        notice = QFrame()
        notice.setObjectName(f"{variant}Notice")
        notice.setMinimumHeight(78 if body else 54)
        notice.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QHBoxLayout(notice)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        icon_label = QLabel()
        icon_label.setObjectName(f"{variant}Icon")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFixedSize(36, 36)
        icon_color = "#126ce0" if icon == "info" else "#1f8f2e"
        icon_label.setPixmap(ui_icon("info" if icon == "info" else "shield", icon_color, 20).pixmap(20, 20))
        layout.addWidget(icon_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        title_label = QLabel(title)
        title_label.setObjectName(f"{variant}Title")
        title_label.setWordWrap(True)
        text_layout.addWidget(title_label)
        if body:
            body_label = QLabel(body)
            body_label.setObjectName(f"{variant}Body")
            body_label.setWordWrap(True)
            text_layout.addWidget(body_label)
        layout.addLayout(text_layout, 1)
        return notice

    def _toggle_password_visibility(self) -> None:
        mode = QLineEdit.EchoMode.Normal if self.show_password_checkbox.isChecked() else QLineEdit.EchoMode.Password
        self.password_input.setEchoMode(mode)
        self.confirm_password_input.setEchoMode(mode)

    def _request_login(self) -> None:
        """Demande au point d'entree d'afficher l'ecran de connexion."""
        self.connexion_demandee.emit()

    def _submit(self) -> None:
        if not self.accept_checkbox.isChecked():
            QMessageBox.warning(self, "Validation", "Vous devez accepter de creer ce compte comme administrateur principal.")
            return

        try:
            result = self._auth_service.creer_premier_gerant(
                nom_complet=self.nom_input.text(),
                identifiant=self.identifiant_input.text(),
                mot_de_passe=self.password_input.text(),
                confirmation_mot_de_passe=self.confirm_password_input.text(),
            )
        except ValidationError as exc:
            QMessageBox.warning(self, "Validation", str(exc))
            return

        dialog = RecoveryCodeDialog(result.code_recuperation, self)
        dialog.exec()
        self.compte_cree.emit()
        self.close()

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QWidget#root {
                background: #f5f8fb;
                color: #0b2d5c;
            }
            QFrame#brandPanel {
                background-color: #eef7ff;
                border-right: 1px solid #e4edf7;
            }
            QLabel#brandTitle {
                color: #14751f;
                font-size: 45px;
                font-weight: 800;
            }
            QLabel#brandBadge {
                color: white;
                background-color: #103f78;
                border-radius: 18px;
                font-size: 28px;
                font-weight: 800;
                padding: 2px 28px;
            }
            QLabel#brandSubtitle {
                color: #1f2940;
                font-size: 23px;
            }
            QWidget#formArea {
                background-color: #fbfdff;
            }
            QScrollArea#formScrollArea,
            QScrollArea#formScrollArea QWidget#qt_scrollarea_viewport,
            QWidget#formScrollContent {
                background-color: #fbfdff;
                border: none;
            }
            QFrame#formCard {
                background: white;
                border: 1px solid #e6edf5;
                border-radius: 26px;
            }
            QLabel#formTitle {
                color: #0b356d;
                font-size: 34px;
                font-weight: 800;
                margin-bottom: 12px;
            }
            QLabel#fieldLabel,
            QLabel#recoveryTitle {
                color: #0f3265;
                font-size: 15px;
                font-weight: 700;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #cfdbe9;
                border-radius: 8px;
                color: #0f3265;
                font-size: 15px;
                padding: 0 16px;
            }
            QLineEdit:focus {
                border: 1px solid #2f80ed;
            }
            QLineEdit:disabled {
                background-color: #f7f9fc;
                color: #60749a;
            }
            QFrame#recoveryBox {
                background-color: #eef7ff;
                border: 1px solid #b8d9ff;
                border-radius: 8px;
            }
            QLabel#helperText {
                color: #0d61d8;
                font-size: 13px;
            }
            QLabel#smallText {
                color: #365176;
                font-size: 12px;
            }
            QCheckBox {
                color: #0f3265;
                font-size: 15px;
                font-weight: 700;
                spacing: 12px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            QFrame#successNotice {
                background-color: #f0fbf3;
                border: 1px solid #b6e2bd;
                border-radius: 8px;
            }
            QFrame#infoNotice {
                background-color: #edf6ff;
                border: 1px solid #b7d8ff;
                border-radius: 8px;
            }
            QLabel#successIcon {
                background-color: #e6f8ea;
                border: 2px solid #1f8f2e;
                border-radius: 18px;
                color: #1f8f2e;
                font-size: 20px;
                font-weight: 900;
            }
            QLabel#infoIcon {
                background-color: #eef6ff;
                border: 2px solid #126ce0;
                border-radius: 18px;
                color: #126ce0;
                font-size: 20px;
                font-weight: 900;
            }
            QLabel#successTitle,
            QLabel#successBody {
                color: #0c5c21;
                font-size: 15px;
            }
            QLabel#successTitle {
                font-weight: 800;
            }
            QLabel#infoTitle {
                color: #0d61d8;
                font-size: 15px;
            }
            QPushButton {
                border-radius: 8px;
                font-size: 15px;
                font-weight: 700;
                min-height: 58px;
            }
            QPushButton#primaryButton {
                background-color: #168025;
                color: white;
                border: none;
            }
            QPushButton#primaryButton:hover {
                background-color: #0f6f1b;
            }
            QPushButton#secondaryButton {
                background-color: white;
                color: #0f3265;
                border: 1px solid #cfdbe9;
            }
            QLabel#loginLink {
                color: #0d61d8;
                font-size: 15px;
                font-weight: 700;
            }
            """
        )


class RecoveryCodeDialog(QDialog):
    def __init__(self, code_recuperation: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Code de recuperation")
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("Conservez ce code de recuperation")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #0b356d;")

        message = QLabel(
            "Ce code est affiche une seule fois. Il ne sera pas stocke en clair dans la base de donnees."
        )
        message.setWordWrap(True)

        code = QLineEdit(code_recuperation)
        code.setReadOnly(True)
        code.setAlignment(Qt.AlignmentFlag.AlignCenter)
        code.setMinimumHeight(52)
        code.setStyleSheet(
            "QLineEdit { font-size: 20px; font-weight: 800; color: #0b356d; background: #eef7ff; border: 1px solid #b8d9ff; border-radius: 8px; }"
        )

        close_button = QPushButton("J'ai conserve le code")
        close_button.setMinimumHeight(46)
        close_button.clicked.connect(self.accept)

        layout.addWidget(title)
        layout.addWidget(message) 
        layout.addWidget(code)
        layout.addWidget(close_button)
