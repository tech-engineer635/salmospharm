"""Panneaux de parametres generaux et de securite."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.core.exceptions import SalmospharmError
from app.services.auth_service import AuthService, SessionUtilisateur
from app.services.parametre_service import ParametreService, ParametresGeneraux


class GeneralSettingsPanel(QFrame):
    def __init__(
        self,
        session_utilisateur: SessionUtilisateur,
        service: ParametreService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("backupPanel")
        self.session_utilisateur = session_utilisateur
        self._service = service or ParametreService()
        layout = QVBoxLayout(self)
        title = QLabel("Pharmacie et impression")
        title.setObjectName("backupTitle")
        layout.addWidget(title)
        form = QFormLayout()
        self.name_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.address_input = QLineEdit()
        self.expiry_input = QSpinBox()
        self.expiry_input.setRange(1, 365)
        self.printer_input = QLineEdit()
        self.name_input.setPlaceholderText("Ex : SALMOSPHARM 133")
        self.phone_input.setPlaceholderText("Ex : +243 000 000 000")
        self.address_input.setPlaceholderText("Ex : Goma, Nord-Kivu")
        self.printer_input.setPlaceholderText("Nom exact dans les imprimantes Windows")
        self.width_combo = QComboBox()
        self.width_combo.addItem("58 mm", 58)
        self.width_combo.addItem("80 mm", 80)
        self.auto_print = QCheckBox("Imprimer automatiquement apres la vente")
        fields = (
            ("Nom de la pharmacie *", self.name_input),
            ("Telephone", self.phone_input),
            ("Adresse", self.address_input),
            ("Alerte expiration (jours)", self.expiry_input),
            ("Nom de l'imprimante Windows", self.printer_input),
            ("Largeur du ticket", self.width_combo),
        )
        for label, field in fields:
            field.setAccessibleName(label.replace(" *", ""))
            field.setMinimumHeight(36)
            form.addRow(_field_label(label, field), field)
        layout.addLayout(form)
        self.auto_print.setAccessibleName("Activer l'impression automatique")
        layout.addWidget(self.auto_print)
        save = QPushButton("Enregistrer les parametres")
        save.setObjectName("backupPrimaryButton")
        save.setDefault(False)
        save.clicked.connect(self._save)
        layout.addWidget(save)
        self._load()

    def _load(self) -> None:
        try:
            data = self._service.obtenir(self.session_utilisateur)
        except SalmospharmError as exc:
            QMessageBox.warning(self, "Parametres", str(exc))
            return
        self.name_input.setText(data.nom_pharmacie)
        self.phone_input.setText(data.telephone)
        self.address_input.setText(data.adresse)
        self.expiry_input.setValue(data.seuil_expiration_jours)
        self.printer_input.setText(data.nom_imprimante)
        self.width_combo.setCurrentIndex(
            self.width_combo.findData(data.largeur_ticket)
        )
        self.auto_print.setChecked(data.impression_auto)

    def _save(self) -> None:
        try:
            self._service.enregistrer(
                self.session_utilisateur,
                ParametresGeneraux(
                    nom_pharmacie=self.name_input.text(),
                    telephone=self.phone_input.text(),
                    adresse=self.address_input.text(),
                    seuil_expiration_jours=self.expiry_input.value(),
                    nom_imprimante=self.printer_input.text(),
                    largeur_ticket=int(self.width_combo.currentData()),
                    impression_auto=self.auto_print.isChecked(),
                ),
            )
            QMessageBox.information(self, "Parametres", "Parametres enregistres.")
        except SalmospharmError as exc:
            QMessageBox.warning(self, "Parametres", str(exc))


class SecuritySettingsPanel(QFrame):
    def __init__(
        self,
        session_utilisateur: SessionUtilisateur,
        auth_service: AuthService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("backupPanel")
        self.session_utilisateur = session_utilisateur
        self._service = auth_service or AuthService()
        layout = QVBoxLayout(self)
        title = QLabel("Securite du compte")
        title.setObjectName("backupTitle")
        layout.addWidget(title)
        form = QFormLayout()
        self.current_input = QLineEdit()
        self.new_input = QLineEdit()
        self.confirm_input = QLineEdit()
        self.current_input.setPlaceholderText("Mot de passe actuel")
        self.new_input.setPlaceholderText("Au moins 5 caracteres")
        self.confirm_input.setPlaceholderText("Retapez le nouveau mot de passe")
        for label, field in (
            ("Mot de passe actuel", self.current_input),
            ("Nouveau mot de passe", self.new_input),
            ("Confirmation", self.confirm_input),
        ):
            field.setEchoMode(QLineEdit.EchoMode.Password)
            field.setAccessibleName(label)
            field.setMinimumHeight(36)
            form.addRow(_field_label(label, field), field)
        layout.addLayout(form)
        actions = QHBoxLayout()
        change = QPushButton("Changer le mot de passe")
        change.setObjectName("backupPrimaryButton")
        change.clicked.connect(self._change_password)
        regenerate = QPushButton("Regenerer le code de recuperation")
        regenerate.setObjectName("backupSecondaryButton")
        regenerate.clicked.connect(self._regenerate)
        self.confirm_input.returnPressed.connect(self._change_password)
        actions.addWidget(change)
        actions.addWidget(regenerate)
        layout.addLayout(actions)

    def _change_password(self) -> None:
        try:
            self._service.changer_mot_de_passe(
                self.session_utilisateur,
                mot_de_passe_actuel=self.current_input.text(),
                nouveau_mot_de_passe=self.new_input.text(),
                confirmation=self.confirm_input.text(),
            )
            self.current_input.clear()
            self.new_input.clear()
            self.confirm_input.clear()
            QMessageBox.information(self, "Securite", "Mot de passe modifie.")
        except SalmospharmError as exc:
            QMessageBox.warning(self, "Securite", str(exc))

    def _regenerate(self) -> None:
        try:
            code = self._service.regenerer_code_recuperation(
                self.session_utilisateur, mot_de_passe=self.current_input.text()
            )
            QMessageBox.information(
                self,
                "Nouveau code de recuperation",
                "Conservez ce code, il ne sera plus affiche :\n\n" + code,
            )
            self.current_input.clear()
        except SalmospharmError as exc:
            QMessageBox.warning(self, "Securite", str(exc))


def _field_label(text: str, field: QWidget) -> QLabel:
    label = QLabel(text)
    label.setObjectName("settingsFieldLabel")
    label.setBuddy(field)
    return label
