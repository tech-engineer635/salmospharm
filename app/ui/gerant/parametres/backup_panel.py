"""Panneau gerant pour exporter et restaurer une sauvegarde locale."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.exceptions import SalmospharmError
from app.services.auth_service import SessionUtilisateur
from app.services.backup_service import BackupService
from app.ui.components.icons import ui_icon


class BackupPanel(QFrame):
    """Expose les commandes de phase 18 sans logique fichier dans l'UI."""

    restart_requested = Signal()

    def __init__(
        self,
        session_utilisateur: SessionUtilisateur,
        backup_service: BackupService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("backupPanel")
        self.session_utilisateur = session_utilisateur
        self._backup_service = backup_service or BackupService()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)
        title = QLabel("Sauvegarde et restauration")
        title.setObjectName("backupTitle")
        subtitle = QLabel(
            "Exportez toutes les donnees dans un fichier .spharm ou restaurez une installation."
        )
        subtitle.setObjectName("backupSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        settings_form = QFormLayout()
        settings_form.setContentsMargins(0, 2, 0, 2)
        settings_form.setHorizontalSpacing(18)
        settings_form.setVerticalSpacing(10)
        settings_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.auto_checkbox = QCheckBox("Activer les sauvegardes automatiques")
        self.auto_checkbox.setObjectName("backupAutoCheckbox")
        self.auto_checkbox.setAccessibleName("Activer les sauvegardes automatiques")
        self.auto_checkbox.toggled.connect(self._actualiser_etat_frequence)
        settings_form.addRow("Automatisation", self.auto_checkbox)

        self.frequency_combo = QComboBox()
        self.frequency_combo.setObjectName("backupFrequencyCombo")
        self.frequency_combo.addItem("Quotidienne et à la fermeture", "QUOTIDIENNE")
        self.frequency_combo.addItem("À la fermeture uniquement", "FERMETURE")
        self.frequency_combo.addItem("Manuelle uniquement", "MANUELLE")
        self.frequency_combo.setAccessibleName("Fréquence des sauvegardes automatiques")
        settings_form.addRow("Fréquence", self.frequency_combo)

        self.last_backup_label = QLabel("Jamais effectuée")
        self.last_backup_label.setObjectName("backupMetaValue")
        self.last_backup_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        settings_form.addRow("Dernière sauvegarde", self.last_backup_label)

        self.folder_label = QLabel()
        self.folder_label.setObjectName("backupMetaValue")
        self.folder_label.setWordWrap(True)
        self.folder_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        settings_form.addRow("Dossier local", self.folder_label)
        layout.addLayout(settings_form)

        self.save_settings_button = QPushButton("Enregistrer les réglages")
        self.save_settings_button.setObjectName("backupSettingsButton")
        self.save_settings_button.setIcon(ui_icon("save", "#0b3567", 16))
        self.save_settings_button.setAccessibleName("Enregistrer les réglages de sauvegarde")
        self.save_settings_button.clicked.connect(self._enregistrer_configuration)
        layout.addWidget(self.save_settings_button, 0, Qt.AlignmentFlag.AlignLeft)

        actions = QHBoxLayout()
        actions.setSpacing(12)
        self.export_button = QPushButton("Exporter les donnees")
        self.export_button.setObjectName("backupPrimaryButton")
        self.export_button.setIcon(ui_icon("download", "#ffffff", 17))
        self.export_button.setAccessibleName("Exporter une sauvegarde complete")
        self.export_button.clicked.connect(self._exporter)
        self.import_button = QPushButton("Importer une sauvegarde")
        self.import_button.setObjectName("backupSecondaryButton")
        self.import_button.setIcon(ui_icon("upload", "#0b3567", 17))
        self.import_button.setAccessibleName("Restaurer une sauvegarde complete")
        self.import_button.clicked.connect(self._importer)
        actions.addWidget(self.export_button)
        actions.addWidget(self.import_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.status_label = QLabel("Aucune operation effectuee pendant cette session.")
        self.status_label.setObjectName("backupStatus")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        self._charger_configuration()

    def _set_busy(self, busy: bool, message: str = "") -> None:
        self.export_button.setDisabled(busy)
        self.import_button.setDisabled(busy)
        self.save_settings_button.setDisabled(busy)
        if message:
            self.status_label.setText(message)
        QApplication.processEvents()

    def _charger_configuration(self) -> None:
        try:
            configuration = self._backup_service.obtenir_configuration(
                self.session_utilisateur
            )
        except SalmospharmError as exc:
            self.status_label.setText(str(exc))
            self.auto_checkbox.setDisabled(True)
            self.frequency_combo.setDisabled(True)
            self.save_settings_button.setDisabled(True)
            return
        self.auto_checkbox.setChecked(configuration.activee)
        index = self.frequency_combo.findData(configuration.frequence)
        self.frequency_combo.setCurrentIndex(max(0, index))
        self.last_backup_label.setText(
            _format_datetime(configuration.derniere_sauvegarde)
            if configuration.derniere_sauvegarde
            else "Jamais effectuée"
        )
        self.folder_label.setText(str(configuration.dossier))
        self.folder_label.setAccessibleName(
            f"Dossier des sauvegardes : {configuration.dossier}"
        )
        self._actualiser_etat_frequence(configuration.activee)

    def _actualiser_etat_frequence(self, activee: bool) -> None:
        self.frequency_combo.setEnabled(activee)

    def _enregistrer_configuration(self) -> None:
        self._set_busy(True, "Enregistrement des réglages...")
        try:
            configuration = self._backup_service.configurer_sauvegarde_automatique(
                self.session_utilisateur,
                activee=self.auto_checkbox.isChecked(),
                frequence=str(self.frequency_combo.currentData()),
            )
        except SalmospharmError as exc:
            self._set_busy(False, "Impossible d'enregistrer les réglages.")
            QMessageBox.warning(self, "SALMOSPHARM", str(exc))
            return
        self._set_busy(
            False,
            "Sauvegardes automatiques activées."
            if configuration.activee
            else "Sauvegardes automatiques désactivées.",
        )
        self._actualiser_etat_frequence(configuration.activee)

    def _exporter(self) -> None:
        destination, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter les donnees",
            "salmospharm_backup.spharm",
            "Sauvegarde SALMOSPHARM (*.spharm)",
        )
        if not destination:
            return
        self._set_busy(True, "Creation de la sauvegarde en cours...")
        try:
            result = self._backup_service.exporter_backup(
                self.session_utilisateur, Path(destination)
            )
        except SalmospharmError as exc:
            self._set_busy(False, "Echec de l'export.")
            QMessageBox.warning(self, "SALMOSPHARM", str(exc))
            return
        self._set_busy(False, f"Dernier export : {result.path.name} ({_format_size(result.size)}).")
        QMessageBox.information(self, "SALMOSPHARM", "Les donnees ont ete sauvegardees avec succes.")

    def _importer(self) -> None:
        source, _ = QFileDialog.getOpenFileName(
            self,
            "Importer une sauvegarde",
            "",
            "Sauvegarde SALMOSPHARM (*.spharm)",
        )
        if not source:
            return
        try:
            info = self._backup_service.inspecter_backup(
                self.session_utilisateur, Path(source)
            )
        except SalmospharmError as exc:
            QMessageBox.warning(self, "SALMOSPHARM", str(exc))
            return
        confirmation = QMessageBox.question(
            self,
            "Confirmer la restauration",
            "L'importation remplacera les donnees actuelles de cette installation.\n"
            "Une sauvegarde de securite sera creee avant le remplacement.\n\n"
            f"Sauvegarde du {info.created_at}.\nVoulez-vous continuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return
        self._set_busy(True, "Validation et restauration en cours...")
        try:
            result = self._backup_service.importer_backup(
                self.session_utilisateur, Path(source)
            )
        except SalmospharmError as exc:
            self._set_busy(False, "La restauration a echoue.")
            QMessageBox.warning(self, "SALMOSPHARM", str(exc))
            return
        self._set_busy(
            False,
            f"Restauration terminee. Sauvegarde de securite : {result.security_backup_path.name}.",
        )
        QMessageBox.information(
            self,
            "SALMOSPHARM",
            "Les donnees ont ete restaurees avec succes.\n"
            "L'application va redemarrer pour appliquer les changements.",
        )
        self.restart_requested.emit()


def _format_size(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} Mo"
    if size >= 1024:
        return f"{size / 1024:.1f} Ko"
    return f"{size} octets"


def _format_datetime(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value
    return parsed.strftime("%d/%m/%Y à %H:%M")
