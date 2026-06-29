"""Interface gerant de gestion des comptes vendeurs."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.exceptions import SalmospharmError
from app.services.auth_service import SessionUtilisateur
from app.services.utilisateur_service import (
    ModificationVendeurPayload,
    ReinitialisationMotDePasseVendeurPayload,
    UtilisateurService,
    VendeurDashboardData,
    VendeurPayload,
)
from app.ui.components.icons import ui_icon


class VendeursPage(QWidget):
    """Page gerant connectee au service utilisateur, sans acces direct a SQLite."""

    def __init__(
        self,
        session_utilisateur: SessionUtilisateur,
        utilisateur_service: UtilisateurService | None = None,
        autoload: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("vendorsPage")
        self.session_utilisateur = session_utilisateur
        self._utilisateur_service = utilisateur_service or UtilisateurService()
        self._data: VendeurDashboardData | None = None
        self._selected_vendor_id: int | None = None
        self._build_ui()
        if autoload:
            self.on_show()

    def on_show(self) -> None:
        self._charger()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addLayout(self._build_header())
        layout.addLayout(self._build_metrics())

        body = QHBoxLayout()
        body.setSpacing(18)
        body.addWidget(self._build_table_panel(), 1)
        body.addWidget(self._build_form_panel())
        layout.addLayout(body, 1)

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        text = QVBoxLayout()
        text.setSpacing(4)
        title = QLabel("Gestion des vendeurs")
        title.setObjectName("vendorsTitle")
        subtitle = QLabel("Gerez les comptes et les performances de votre equipe commerciale")
        subtitle.setObjectName("vendorsSubtitle")
        subtitle.setWordWrap(True)
        subtitle.setMaximumWidth(380)
        text.addWidget(title)
        text.addWidget(subtitle)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("vendorsSearch")
        self.search_input.setPlaceholderText("Rechercher un vendeur...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMaximumWidth(260)
        self.search_input.addAction(ui_icon("search", "#506b92", 18), QLineEdit.ActionPosition.LeadingPosition)
        self.search_input.textChanged.connect(self._charger)

        add_button = QPushButton("Ajouter un vendeur")
        add_button.setObjectName("blueButton")
        add_button.setIcon(ui_icon("plus", "#ffffff", 18))
        add_button.clicked.connect(self._focus_form)

        header.addLayout(text, 1)
        header.addWidget(self.search_input)
        header.addWidget(add_button)
        return header

    def _build_metrics(self) -> QGridLayout:
        self.metrics_grid = QGridLayout()
        self.metrics_grid.setSpacing(18)
        self.total_metric = VendorMetricCard("Nombre de vendeurs", "0", "Total des comptes", "vendeurs", "green")
        self.active_metric = VendorMetricCard("Actifs aujourd'hui", "0", "Comptes actifs", "vendeurs", "blue")
        self.sales_metric = VendorMetricCard("Ventes du jour", "0 CDF", "CDF uniquement", "cart", "green")
        self.inactive_metric = VendorMetricCard("Comptes desactives", "0", "Comptes bloques", "vendeurs", "red")
        self.metric_cards = (
            self.total_metric,
            self.active_metric,
            self.sales_metric,
            self.inactive_metric,
        )
        for index, card in enumerate(self.metric_cards):
            self.metrics_grid.addWidget(card, 0, index)
        return self.metrics_grid

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.set_compact(self.window().width() < 1200)

    def set_compact(self, compact: bool) -> None:
        for index, card in enumerate(self.metric_cards):
            self.metrics_grid.addWidget(
                card, index // 2 if compact else 0, index % 2 if compact else index
            )

    def _build_table_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("vendorsPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("Liste des vendeurs")
        title.setObjectName("vendorsPanelTitle")
        title.setContentsMargins(20, 18, 20, 14)
        layout.addWidget(title)

        self.vendors_table = QTableWidget(0, 6)
        self.vendors_table.setObjectName("vendorsTable")
        self.vendors_table.setHorizontalHeaderLabels(
            ["Nom", "Identifiant", "Statut", "Derniere connexion", "Ventes du jour", "Actions"]
        )
        header = self.vendors_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.vendors_table.verticalHeader().setVisible(False)
        self.vendors_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.vendors_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.vendors_table.itemSelectionChanged.connect(self._charger_selection)
        self.vendors_table.setMinimumHeight(430)
        layout.addWidget(self.vendors_table)

        footer = QHBoxLayout()
        footer.setContentsMargins(20, 12, 20, 12)
        self.footer_label = QLabel("Affichage de 0 vendeur")
        self.footer_label.setObjectName("vendorsFooter")
        footer.addWidget(self.footer_label)
        footer.addStretch(1)
        layout.addLayout(footer)
        return panel

    def _build_form_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("vendorsPanel")
        panel.setFixedWidth(320)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        title_row = QHBoxLayout()
        title = QLabel("Ajouter un vendeur")
        title.setObjectName("vendorsPanelTitle")
        clear = QPushButton("x")
        clear.setObjectName("linkButton")
        clear.clicked.connect(self._vider_formulaire)
        title_row.addWidget(title)
        title_row.addStretch(1)
        title_row.addWidget(clear)
        layout.addLayout(title_row)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Entrez le nom complet")
        self.identifier_input = QLineEdit()
        self.identifier_input.setPlaceholderText("Entrez l'email ou l'identifiant")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Entrez le mot de passe")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirmez le mot de passe")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        for field in (
            self.name_input,
            self.identifier_input,
            self.password_input,
            self.confirm_password_input,
        ):
            field.setObjectName("vendorFormInput")
        self.name_input.setAccessibleName("Nom complet du vendeur")
        self.identifier_input.setAccessibleName("Identifiant du vendeur")
        self.password_input.setAccessibleName("Mot de passe du vendeur")
        self.confirm_password_input.setAccessibleName(
            "Confirmation du mot de passe du vendeur"
        )

        layout.addLayout(_field_group("Nom complet *", self.name_input))
        layout.addLayout(_field_group("Email ou identifiant *", self.identifier_input))
        layout.addLayout(_field_group("Mot de passe *", self.password_input))
        layout.addLayout(
            _field_group("Confirmer le mot de passe *", self.confirm_password_input)
        )

        note = QLabel(
            "Le mot de passe est sensible aux majuscules. En cas d'oubli, "
            "le gerant devra le reinitialiser."
        )
        note.setObjectName("vendorInfo")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch(1)

        buttons = QHBoxLayout()
        cancel = QPushButton("Annuler")
        cancel.setObjectName("outlineButton")
        cancel.clicked.connect(self._vider_formulaire)
        self.save_button = QPushButton("Creer le compte")
        self.save_button.setObjectName("primaryButton")
        self.save_button.setIcon(ui_icon("vendeurs", "#ffffff", 18))
        self.save_button.clicked.connect(self._creer_vendeur)
        self.save_button.setDefault(True)
        self.password_input.returnPressed.connect(self._creer_vendeur)
        self.confirm_password_input.returnPressed.connect(self._creer_vendeur)
        buttons.addWidget(cancel)
        buttons.addWidget(self.save_button)
        layout.addLayout(buttons)

        self.reset_password_button = QPushButton("Reinitialiser le mot de passe")
        self.reset_password_button.setObjectName("outlineButton")
        self.reset_password_button.clicked.connect(self._reinitialiser_mot_de_passe)
        self.reset_password_button.setVisible(False)
        layout.addWidget(self.reset_password_button)
        return panel

    def _charger(self) -> None:
        try:
            self._data = self._utilisateur_service.tableau_vendeurs(
                self.session_utilisateur,
                terme=self.search_input.text() if hasattr(self, "search_input") else "",
            )
            self._remplir_table()
            self._maj_metrics()
        except SalmospharmError as exc:
            self._afficher_erreur(str(exc))

    def _remplir_table(self) -> None:
        data = self._data
        if data is None:
            return
        self.vendors_table.setRowCount(0)
        for item in data.vendeurs:
            row = self.vendors_table.rowCount()
            self.vendors_table.insertRow(row)
            values = [
                item.nom,
                item.identifiant,
                "Actif" if item.actif else "Inactif",
                _format_datetime(item.derniere_connexion),
                _format_cdf(item.ventes_du_jour),
            ]
            for column, value in enumerate(values):
                table_item = QTableWidgetItem(value)
                table_item.setData(Qt.ItemDataRole.UserRole, item.utilisateur_id)
                table_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | (Qt.AlignmentFlag.AlignHCenter if column in {2, 4} else Qt.AlignmentFlag.AlignLeft))
                self.vendors_table.setItem(row, column, table_item)
            action = QPushButton("Reactiver" if not item.actif else "Desactiver")
            action.setObjectName("successButton" if not item.actif else "dangerButton")
            action.clicked.connect(lambda checked=False, vendeur_id=item.utilisateur_id, active=item.actif: self._toggle_vendeur(vendeur_id, active))
            self.vendors_table.setCellWidget(row, 5, action)
            self.vendors_table.setRowHeight(row, 44)
        self.footer_label.setText(f"Affichage de {len(data.vendeurs)} vendeur(s)")

    def _maj_metrics(self) -> None:
        data = self._data
        if data is None:
            return
        total = data.metrics.total_vendeurs
        active_percent = int((data.metrics.actifs / total) * 100) if total else 0
        inactive_percent = int((data.metrics.inactifs / total) * 100) if total else 0
        self.total_metric.set_value(str(total), "Total des comptes")
        self.active_metric.set_value(str(data.metrics.actifs), f"{active_percent}% des vendeurs")
        self.sales_metric.set_value(_format_cdf(data.metrics.ventes_du_jour), "Ventes validees")
        self.inactive_metric.set_value(str(data.metrics.inactifs), f"{inactive_percent}% du total")

    def _creer_vendeur(self) -> None:
        try:
            if self._selected_vendor_id is not None:
                self._utilisateur_service.modifier_vendeur(
                    self.session_utilisateur,
                    vendeur_id=self._selected_vendor_id,
                    payload=ModificationVendeurPayload(
                        nom_complet=self.name_input.text(),
                        identifiant=self.identifier_input.text(),
                    ),
                )
                self._vider_formulaire()
                self._charger()
                self._afficher_info("Compte vendeur modifie.")
                return
            result = self._utilisateur_service.creer_vendeur(
                self.session_utilisateur,
                VendeurPayload(
                    nom_complet=self.name_input.text(),
                    identifiant=self.identifier_input.text(),
                    mot_de_passe=self.password_input.text(),
                    confirmation_mot_de_passe=self.confirm_password_input.text(),
                ),
            )
            identifiant_cree = result.identifiant
            self._vider_formulaire()
            self._charger()
            IdentifiantVendeurDialog(identifiant_cree, self).exec()
        except SalmospharmError as exc:
            self._afficher_erreur(str(exc))

    def _reinitialiser_mot_de_passe(self) -> None:
        if self._selected_vendor_id is None:
            return
        try:
            self._utilisateur_service.reinitialiser_mot_de_passe_vendeur(
                self.session_utilisateur,
                vendeur_id=self._selected_vendor_id,
                payload=ReinitialisationMotDePasseVendeurPayload(
                    nouveau_mot_de_passe=self.password_input.text(),
                    confirmation_mot_de_passe=self.confirm_password_input.text(),
                ),
            )
            self.password_input.clear()
            self.confirm_password_input.clear()
            self._afficher_info("Mot de passe vendeur reinitialise.")
        except SalmospharmError as exc:
            self._afficher_erreur(str(exc))

    def _toggle_vendeur(self, vendeur_id: int, actif: bool) -> None:
        try:
            if actif:
                confirmation = QMessageBox.question(
                    self,
                    "Desactiver le vendeur",
                    "Ce vendeur ne pourra plus se connecter. Continuer ?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if confirmation != QMessageBox.StandardButton.Yes:
                    return
                self._utilisateur_service.desactiver_vendeur(self.session_utilisateur, vendeur_id=vendeur_id)
            else:
                self._utilisateur_service.reactiver_vendeur(self.session_utilisateur, vendeur_id=vendeur_id)
            self._charger()
        except SalmospharmError as exc:
            self._afficher_erreur(str(exc))

    def _vider_formulaire(self) -> None:
        self._selected_vendor_id = None
        self.name_input.clear()
        self.identifier_input.clear()
        self.password_input.clear()
        self.confirm_password_input.clear()
        self.password_input.setPlaceholderText("Entrez le mot de passe")
        self.confirm_password_input.setPlaceholderText("Confirmez le mot de passe")
        self.save_button.setText("Creer le compte")
        self.reset_password_button.setVisible(False)

    def _charger_selection(self) -> None:
        row = self.vendors_table.currentRow()
        if row < 0 or self._data is None:
            return
        identifiant_item = self.vendors_table.item(row, 1)
        if identifiant_item is None:
            return
        vendeur_id = identifiant_item.data(Qt.ItemDataRole.UserRole)
        vendeur = next(
            (
                item
                for item in self._data.vendeurs
                if item.utilisateur_id == vendeur_id
            ),
            None,
        )
        if vendeur is None:
            return
        self._selected_vendor_id = vendeur.utilisateur_id
        self.name_input.setText(vendeur.nom)
        self.identifier_input.setText(vendeur.identifiant)
        self.password_input.clear()
        self.confirm_password_input.clear()
        self.password_input.setPlaceholderText(
            "Nouveau mot de passe"
        )
        self.confirm_password_input.setPlaceholderText(
            "Confirmez le nouveau mot de passe"
        )
        self.save_button.setText("Enregistrer")
        self.reset_password_button.setVisible(True)

    def _focus_form(self) -> None:
        if hasattr(self, "name_input"):
            self.name_input.setFocus()

    def _afficher_info(self, message: str) -> None:
        QMessageBox.information(self, "SALMOSPHARM", message)

    def _afficher_erreur(self, message: str) -> None:
        QMessageBox.warning(self, "SALMOSPHARM", message)


class VendorMetricCard(QFrame):
    def __init__(self, title: str, value: str, subtitle: str, icon: str, color: str) -> None:
        super().__init__()
        self.setObjectName("vendorMetricCard")
        self.setFixedHeight(104)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)
        icon_label = QLabel()
        icon_label.setObjectName(f"vendorMetricIcon_{color}")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFixedSize(46, 46)
        icon_label.setPixmap(ui_icon(icon, "#ffffff", 22).pixmap(22, 22))
        text = QVBoxLayout()
        text.setSpacing(6)
        title_label = QLabel(title)
        title_label.setObjectName("vendorMetricTitle")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("vendorMetricValue")
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("vendorMetricSubtitle")
        text.addWidget(title_label)
        text.addWidget(self.value_label)
        text.addWidget(self.subtitle_label)
        layout.addWidget(icon_label)
        layout.addLayout(text, 1)

    def set_value(self, value: str, subtitle: str) -> None:
        self.value_label.setText(value)
        self.subtitle_label.setText(subtitle)


class IdentifiantVendeurDialog(QDialog):
    """Affiche l'identifiant normalise et permet au gerant de le copier."""

    def __init__(self, identifiant: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Compte vendeur cree")
        self.setModal(True)
        layout = QVBoxLayout(self)

        message = QLabel(
            "Le compte vendeur a ete cree. Transmettez exactement cet identifiant "
            "et rappelez que le mot de passe est sensible aux majuscules."
        )
        message.setWordWrap(True)
        layout.addWidget(message)

        self.identifiant_input = QLineEdit(identifiant)
        self.identifiant_input.setReadOnly(True)
        self.identifiant_input.setAccessibleName("Identifiant vendeur cree")
        layout.addWidget(self.identifiant_input)

        copy_button = QPushButton("Copier l'identifiant")
        copy_button.clicked.connect(
            lambda: QApplication.clipboard().setText(self.identifiant_input.text())
        )
        layout.addWidget(copy_button)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)


def _field_group(label_text: str, field: QWidget) -> QVBoxLayout:
    group = QVBoxLayout()
    group.setContentsMargins(0, 0, 0, 0)
    group.setSpacing(7)
    label = QLabel(label_text)
    label.setObjectName("vendorFormLabel")
    label.setBuddy(field)
    group.addWidget(label)
    group.addWidget(field)
    return group


def _format_number(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def _format_cdf(value: int) -> str:
    return f"{_format_number(value)} CDF"


def _format_datetime(value: str | None) -> str:
    if not value:
        return "-"
    return value.replace("T", " ")[:16]
