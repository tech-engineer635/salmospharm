"""Page gerant de gestion du catalogue produits."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.exceptions import SalmospharmError
from app.core.paths import get_exports_dir
from app.services.auth_service import SessionUtilisateur
from app.services.produit_service import ProduitPayload, ProduitService
from app.ui.components.icons import ui_icon


class ProduitsPage(QWidget):
    """Interface catalogue qui delegue toutes les ecritures au service produit."""

    def __init__(
        self,
        session_utilisateur: SessionUtilisateur,
        produit_service: ProduitService | None = None,
        autoload: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.session_utilisateur = session_utilisateur
        self._produit_service = produit_service or ProduitService()
        self._categories: dict[int, str] = {}
        self._produits_affiches: list = []
        self._selected_product_id: int | None = None
        self._build_ui()
        if autoload:
            self.on_show()

    def on_show(self) -> None:
        """Recharge les donnees quand la page devient visible."""
        self._charger_categories()
        self._charger_produits()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        layout.addLayout(self._build_page_header())
        layout.addLayout(self._build_metrics_row())

        body = QHBoxLayout()
        body.setSpacing(18)

        main_column = QVBoxLayout()
        main_column.setSpacing(10)
        main_column.addLayout(self._build_toolbar())
        main_column.addWidget(self._build_list_panel(), 1)

        side_column = QVBoxLayout()
        side_column.setSpacing(8)
        side_column.addWidget(self._build_filters_panel())
        side_column.addWidget(self._build_product_panel(), 1)

        body.addLayout(main_column, 1)
        body.addLayout(side_column)
        layout.addLayout(body, 1)

    def _build_page_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setSpacing(18)

        text = QVBoxLayout()
        text.setSpacing(4)
        title = QLabel("Gestion des produits")
        title.setObjectName("productsPageTitle")
        subtitle = QLabel("Gerez et maintenez le catalogue de produits de la pharmacie.")
        subtitle.setObjectName("productsPageSubtitle")
        text.addWidget(title)
        text.addWidget(subtitle)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("productsHeroSearch")
        self.search_input.setPlaceholderText("Rechercher (nom du produit, code-barres...)")
        self.search_input.addAction(ui_icon("search", "#0b3567", 18), QLineEdit.ActionPosition.TrailingPosition)
        self.search_input.textChanged.connect(self._charger_produits)
        self.search_input.setMaximumWidth(380)

        header.addLayout(text, 1)
        header.addWidget(self.search_input)
        return header

    def _build_metrics_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)
        self.total_metric = ProductMetricCard("Total produits", "0", "+0% vs hier", "product", "green")
        self.category_metric = ProductMetricCard("Categories", "0", "+0 vs hier", "tag", "blue")
        self.low_stock_metric = ProductMetricCard("Stock faible", "0", "Phase 12", "warning", "orange")
        self.expiry_metric = ProductMetricCard("Expirations proches", "0", "Phase 12", "calendar", "purple")
        for card in (self.total_metric, self.category_metric, self.low_stock_metric, self.expiry_metric):
            row.addWidget(card, 1)
        return row

    def _build_toolbar(self) -> QHBoxLayout:
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        new_button = QPushButton("Nouveau produit")
        new_button.setObjectName("primaryButton")
        new_button.setIcon(ui_icon("plus", "#ffffff", 18))
        new_button.clicked.connect(self._vider_formulaire_produit)

        import_button = QPushButton("Importer")
        import_button.setObjectName("outlineButton")
        import_button.setIcon(ui_icon("upload", "#0b3567", 17))
        import_button.setEnabled(False)
        import_button.setToolTip("Import catalogue a traiter dans un workflow dedie.")

        self.export_button = QPushButton("Export Excel")
        self.export_button.setObjectName("outlineButton")
        self.export_button.setIcon(ui_icon("download", "#108d38", 17))
        self.export_button.setAccessibleName("Exporter la liste des produits en Excel")
        self.export_button.clicked.connect(self._exporter_excel)

        filter_button = QPushButton("Filtres")
        filter_button.setObjectName("outlineButton")
        filter_button.setIcon(ui_icon("filter", "#0b3567", 17))
        filter_button.clicked.connect(lambda: self.filter_category_combo.setFocus())

        toolbar.addWidget(new_button)
        toolbar.addWidget(import_button)
        toolbar.addWidget(self.export_button)
        toolbar.addStretch(1)
        toolbar.addWidget(filter_button)
        return toolbar

    def _build_category_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("contentPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        title = QLabel("Categories")
        title.setObjectName("panelTitle")
        self.category_name_input = QLineEdit()
        self.category_name_input.setPlaceholderText("Nom de la categorie")
        self.category_description_input = QLineEdit()
        self.category_description_input.setPlaceholderText("Description")
        create_button = QPushButton("Ajouter la categorie")
        create_button.setObjectName("primaryButton")
        create_button.clicked.connect(self._creer_categorie)

        layout.addWidget(title)
        layout.addWidget(self.category_name_input)
        layout.addWidget(self.category_description_input)
        layout.addWidget(create_button)
        layout.addStretch(1)
        return panel

    def _build_product_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("contentPanel")
        panel.setFixedWidth(300)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        title = QLabel("Ajouter un produit")
        title.setObjectName("sidePanelTitle")

        self.product_name_input = QLineEdit()
        self.product_name_input.setPlaceholderText("Ex : Paracetamol 500mg")
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Ex : PRD-00001")
        self.price_input = QSpinBox()
        self.price_input.setRange(0, 999_999_999)
        self.price_input.setSuffix(" CDF")
        self.stock_minimum_input = QSpinBox()
        self.stock_minimum_input.setRange(0, 999_999)
        self.category_combo = QComboBox()
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Description courte")
        self.description_input.setVisible(False)
        self.active_hint = QCheckBox("Produit actif")
        self.active_hint.setChecked(True)
        self.active_hint.setEnabled(False)
        self.active_hint.setVisible(False)
        self.product_status_hint = QLabel("Selectionnez un produit pour modifier son statut.")
        self.product_status_hint.setObjectName("productStatusHint")
        self.product_status_hint.setWordWrap(True)
        self.product_status_hint.setVisible(False)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(4)
        grid.addWidget(_field_label("Prix (CDF) *"), 0, 0)
        grid.addWidget(_field_label("Stock minimum *"), 0, 1)
        grid.addWidget(self.price_input, 1, 0)
        grid.addWidget(self.stock_minimum_input, 1, 1)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.save_button = QPushButton("Ajouter le produit")
        self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self._enregistrer_produit)
        self.clear_button = QPushButton("Annuler")
        self.clear_button.setObjectName("outlineButton")
        self.clear_button.clicked.connect(self._vider_formulaire_produit)
        self.disable_button = QPushButton("Desactiver")
        self.disable_button.setObjectName("dangerButton")
        self.disable_button.clicked.connect(self._basculer_statut_produit)
        self.disable_button.setEnabled(False)
        self.disable_button.setVisible(False)
        actions.addWidget(self.clear_button, 1)
        actions.addWidget(self.save_button, 1)

        layout.addWidget(title)
        layout.addWidget(_field_label("Nom du produit *"))
        layout.addWidget(self.product_name_input)
        layout.addWidget(_field_label("Categorie *"))
        layout.addWidget(self.category_combo)
        layout.addWidget(_field_label("Code-barres"))
        layout.addWidget(self.barcode_input)
        layout.addLayout(grid)
        layout.addWidget(self.active_hint)
        layout.addWidget(self.product_status_hint)
        layout.addWidget(self.disable_button)
        layout.addStretch(1)
        layout.addLayout(actions)
        return panel

    def _build_list_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("contentPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.products_table = QTableWidget(0, 7)
        self.products_table.setObjectName("productsTable")
        self.products_table.setHorizontalHeaderLabels(
            ["Code", "Nom du produit", "Categorie", "Prix (CDF)", "Stock min.", "Statut", "Actions"]
        )
        header = self.products_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.products_table.verticalHeader().setVisible(False)
        self.products_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.products_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.products_table.itemSelectionChanged.connect(self._charger_selection)
        self.products_table.setMinimumHeight(300)
        self.products_table.setMinimumWidth(0)

        layout.addWidget(self.products_table)
        layout.addLayout(self._build_table_footer())
        return panel

    def _build_table_footer(self) -> QHBoxLayout:
        footer = QHBoxLayout()
        footer.setContentsMargins(18, 10, 18, 12)
        footer.setSpacing(10)
        self.table_footer_label = QLabel("Affichage de 0 produit")
        self.table_footer_label.setObjectName("productsFooterText")
        footer.addWidget(self.table_footer_label)
        footer.addStretch(1)
        for label in ("<", "1", "2", "3", "..."):
            button = QPushButton(label)
            button.setObjectName("paginationButtonActive" if label == "1" else "paginationButton")
            button.setEnabled(label == "1")
            footer.addWidget(button)
        self.page_size_combo = QComboBox()
        self.page_size_combo.setObjectName("pageSizeCombo")
        self.page_size_combo.addItems(["10 / page", "25 / page", "50 / page"])
        footer.addWidget(self.page_size_combo)
        return footer

    def _build_filters_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("contentPanel")
        panel.setFixedWidth(300)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(3)

        header = QHBoxLayout()
        title = QLabel("Filtres rapides")
        title.setObjectName("sidePanelTitle")
        reset = QPushButton("Reinitialiser")
        reset.setObjectName("linkButton")
        reset.clicked.connect(self._reinitialiser_filtres)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(reset)

        self.filter_category_combo = QComboBox()
        self.status_filter_combo = QComboBox()
        self.stock_filter_combo = QComboBox()
        self.active_only_checkbox = QCheckBox("Actifs seulement")
        self.active_only_checkbox.setVisible(False)
        self.status_filter_combo.addItems(["Tous les statuts", "Actifs", "Desactives"])
        self.stock_filter_combo.addItems(["Tous", "Stock minimum positif"])
        self.filter_category_combo.currentIndexChanged.connect(self._charger_produits)
        self.status_filter_combo.currentIndexChanged.connect(self._charger_produits)
        self.stock_filter_combo.currentIndexChanged.connect(self._charger_produits)

        apply_button = QPushButton("Appliquer les filtres")
        apply_button.setObjectName("blueButton")
        apply_button.setIcon(ui_icon("filter", "#ffffff", 17))
        apply_button.clicked.connect(self._charger_produits)

        layout.addLayout(header)
        layout.addWidget(_field_label("Categorie"))
        layout.addWidget(self.filter_category_combo)
        layout.addWidget(_field_label("Statut"))
        layout.addWidget(self.status_filter_combo)
        layout.addWidget(_field_label("Stock"))
        layout.addWidget(self.stock_filter_combo)
        layout.addWidget(apply_button)
        return panel

    def _charger_categories(self) -> None:
        self._categories = {
            categorie.id: categorie.nom
            for categorie in self._produit_service.lister_categories(self.session_utilisateur)
        }
        self.category_combo.clear()
        self.filter_category_combo.clear()
        self.category_combo.addItem("Sans categorie", None)
        self.filter_category_combo.addItem("Toutes categories", None)
        for categorie_id, nom in self._categories.items():
            self.category_combo.addItem(nom, categorie_id)
            self.filter_category_combo.addItem(nom, categorie_id)

    def _charger_produits(self) -> None:
        categorie_id = self.filter_category_combo.currentData() if hasattr(self, "filter_category_combo") else None
        produits = self._produit_service.rechercher_produits(
            self.session_utilisateur,
            terme=self.search_input.text() if hasattr(self, "search_input") else "",
            categorie_id=categorie_id,
            actifs_seulement=self.status_filter_combo.currentIndex() == 1 if hasattr(self, "status_filter_combo") else False,
        )
        if hasattr(self, "status_filter_combo") and self.status_filter_combo.currentIndex() == 2:
            produits = [produit for produit in produits if produit.actif != 1]
        if hasattr(self, "stock_filter_combo") and self.stock_filter_combo.currentIndex() == 1:
            produits = [produit for produit in produits if produit.stock_minimum > 0]

        self._produits_affiches = produits
        self._maj_compteurs(produits)
        self.products_table.setRowCount(0)
        for produit in produits:
            row = self.products_table.rowCount()
            self.products_table.insertRow(row)
            values = [
                f"PRD-{produit.id:05d}",
                produit.nom,
                self._categories.get(produit.categorie_id or 0, "Sans categorie"),
                f"{produit.prix_vente:,}".replace(",", " "),
                str(produit.stock_minimum),
                "Actif" if produit.actif == 1 else "Desactive",
                "...",
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, produit.id)
                alignment = Qt.AlignmentFlag.AlignVCenter
                if column in {3, 4, 5, 6}:
                    alignment |= Qt.AlignmentFlag.AlignHCenter
                item.setTextAlignment(alignment)
                self.products_table.setItem(row, column, item)
            self.products_table.setRowHeight(row, 40)

        count = len(produits)
        self.table_footer_label.setText(
            f"Affichage de 1 a {count} sur {count} produits" if count else "Aucun produit a afficher"
        )

    def _maj_compteurs(self, produits: list) -> None:
        self.total_metric.set_value(str(len(produits)), "+0% vs hier")
        self.category_metric.set_value(str(len(self._categories)), "+0 vs hier")
        self.low_stock_metric.set_value("0", "Phase 12")
        self.expiry_metric.set_value("0", "Phase 12")

    def _reinitialiser_filtres(self) -> None:
        self.search_input.clear()
        self.filter_category_combo.setCurrentIndex(0)
        self.status_filter_combo.setCurrentIndex(0)
        self.stock_filter_combo.setCurrentIndex(0)
        self._charger_produits()

    def _exporter_excel(self) -> None:
        destination, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter les produits",
            str(get_exports_dir() / f"produits_{date.today().isoformat()}.xlsx"),
            "Classeur Excel (*.xlsx)",
        )
        if not destination:
            return
        status = ("ACTIFS", "INACTIFS")[self.status_filter_combo.currentIndex() - 1] if self.status_filter_combo.currentIndex() in {1, 2} else "TOUS"
        self.export_button.setDisabled(True)
        try:
            path = self._produit_service.exporter_excel(
                self.session_utilisateur,
                destination=Path(destination),
                terme=self.search_input.text(),
                categorie_id=self.filter_category_combo.currentData(),
                statut=status,
                stock_minimum_positif=self.stock_filter_combo.currentIndex() == 1,
            )
        except SalmospharmError as exc:
            QMessageBox.warning(self, "SALMOSPHARM", str(exc))
            return
        finally:
            self.export_button.setEnabled(True)
        QMessageBox.information(self, "SALMOSPHARM", f"Produits exportes avec succes :\n{path}")

    def _creer_categorie(self) -> None:
        try:
            self._produit_service.creer_categorie(
                self.session_utilisateur,
                nom=self.category_name_input.text(),
                description=self.category_description_input.text(),
            )
            self.category_name_input.clear()
            self.category_description_input.clear()
            self._charger_categories()
            self._afficher_info("Categorie ajoutee.")
        except SalmospharmError as exc:
            self._afficher_erreur(str(exc))

    def _enregistrer_produit(self) -> None:
        payload = ProduitPayload(
            nom=self.product_name_input.text(),
            code_barres=self.barcode_input.text(),
            categorie_id=self.category_combo.currentData(),
            prix_vente=self.price_input.value(),
            stock_minimum=self.stock_minimum_input.value(),
            description=self.description_input.text(),
        )
        try:
            if self._selected_product_id is None:
                self._produit_service.creer_produit(self.session_utilisateur, payload)
                self._afficher_info("Produit ajoute.")
            else:
                self._produit_service.modifier_produit(
                    self.session_utilisateur,
                    produit_id=self._selected_product_id,
                    payload=payload,
                )
                self._afficher_info("Produit modifie.")
            self._vider_formulaire_produit()
            self._charger_produits()
        except SalmospharmError as exc:
            self._afficher_erreur(str(exc))

    def _basculer_statut_produit(self) -> None:
        if self._selected_product_id is None:
            return
        try:
            produit = self._produit_par_id(self._selected_product_id)
            if produit is not None and produit.actif == 1:
                self._produit_service.desactiver_produit(
                    self.session_utilisateur,
                    produit_id=self._selected_product_id,
                )
                message = "Produit desactive."
            else:
                self._produit_service.reactiver_produit(
                    self.session_utilisateur,
                    produit_id=self._selected_product_id,
                )
                message = "Produit reactive."
            self._vider_formulaire_produit()
            self._charger_produits()
            self._afficher_info(message)
        except SalmospharmError as exc:
            self._afficher_erreur(str(exc))

    def _charger_selection(self) -> None:
        selected_items = self.products_table.selectedItems()
        if not selected_items:
            return
        row = selected_items[0].row()
        self._selected_product_id = self.products_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        produit = self._produit_par_id(self._selected_product_id)
        if produit is None:
            return
        self.product_name_input.setText(produit.nom)
        self.barcode_input.setText(produit.code_barres or "")
        self.price_input.setValue(produit.prix_vente)
        self.stock_minimum_input.setValue(int(self.products_table.item(row, 4).text()))
        self.description_input.setText(produit.description or "")
        self._select_combo_data(self.category_combo, produit.categorie_id)
        self.save_button.setText("Modifier")
        if produit.actif == 1:
            self.disable_button.setText("Desactiver ce produit")
            self.disable_button.setObjectName("dangerButton")
            self.disable_button.setToolTip("Desactiver le produit selectionne sans le supprimer.")
            self.product_status_hint.setText("Ce produit est actif. Vous pouvez le desactiver sans supprimer son historique.")
        else:
            self.disable_button.setText("Reactiver ce produit")
            self.disable_button.setObjectName("successButton")
            self.disable_button.setToolTip("Remettre ce produit dans le catalogue actif.")
            self.product_status_hint.setText("Ce produit est desactive. Utilisez le bouton de reactivation pour le rendre de nouveau disponible.")
        self.disable_button.setEnabled(True)
        self.disable_button.setVisible(True)
        self.active_hint.setVisible(True)
        self.product_status_hint.setVisible(True)
        self.disable_button.style().unpolish(self.disable_button)
        self.disable_button.style().polish(self.disable_button)
        self.active_hint.setChecked(produit.actif == 1)

    def _vider_formulaire_produit(self) -> None:
        self._selected_product_id = None
        self.products_table.clearSelection()
        self.product_name_input.clear()
        self.barcode_input.clear()
        self.price_input.setValue(0)
        self.stock_minimum_input.setValue(0)
        self.description_input.clear()
        self.category_combo.setCurrentIndex(0)
        self.save_button.setText("Enregistrer")
        self.disable_button.setText("Desactiver")
        self.disable_button.setObjectName("dangerButton")
        self.disable_button.setToolTip("")
        self.disable_button.setEnabled(False)
        self.disable_button.setVisible(False)
        self.active_hint.setVisible(False)
        self.product_status_hint.setVisible(False)
        self.disable_button.style().unpolish(self.disable_button)
        self.disable_button.style().polish(self.disable_button)
        self.active_hint.setChecked(True)
        self.product_status_hint.setText("Selectionnez un produit pour modifier son statut.")

    def _produit_par_id(self, produit_id: int) -> object | None:
        return next((produit for produit in self._produits_affiches if produit.id == produit_id), None)

    @staticmethod
    def _select_combo_data(combo: QComboBox, data: int | None) -> None:
        for index in range(combo.count()):
            if combo.itemData(index) == data:
                combo.setCurrentIndex(index)
                return

    def _afficher_info(self, message: str) -> None:
        QMessageBox.information(self, "SALMOSPHARM", message)

    def _afficher_erreur(self, message: str) -> None:
        QMessageBox.warning(self, "SALMOSPHARM", message)


class ProductMetricCard(QFrame):
    """Carte de synthese compacte, proche de la maquette fournie."""

    def __init__(self, title: str, value: str, trend: str, icon: str, color: str) -> None:
        super().__init__()
        self.setObjectName("productMetricCard")
        self.setFixedHeight(74)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        icon_label = QLabel()
        icon_label.setObjectName(f"productMetricIcon_{color}")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFixedSize(40, 40)
        icon_label.setPixmap(ui_icon(icon, "#ffffff", 20).pixmap(20, 20))

        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)
        title_label = QLabel(title)
        title_label.setObjectName("productMetricTitle")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("productMetricValue")
        self.trend_label = QLabel(trend)
        self.trend_label.setObjectName(f"productMetricTrend_{color}")
        text_layout.addWidget(title_label)
        text_layout.addWidget(self.value_label)
        text_layout.addWidget(self.trend_label)

        layout.addWidget(icon_label)
        layout.addLayout(text_layout, 1)

    def set_value(self, value: str, trend: str) -> None:
        self.value_label.setText(value)
        self.trend_label.setText(trend)


def _field_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("formFieldLabel")
    return label
