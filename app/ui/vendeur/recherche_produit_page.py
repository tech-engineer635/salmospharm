"""Consultation en lecture seule du catalogue et du stock vendable."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QPushButton, QScrollArea, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from app.core.exceptions import SalmospharmError
from app.services.auth_service import SessionUtilisateur
from app.services.vente_service import ProduitConsultationStock, VenteService
from app.ui.components.icons import ui_icon


class RechercheProduitPage(QWidget):
    """Affiche les produits actifs, y compris ceux sans stock vendable."""

    def __init__(
        self,
        session_utilisateur: SessionUtilisateur,
        vente_service: VenteService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("productSearchPage")
        self.session_utilisateur = session_utilisateur
        self._vente_service = vente_service or VenteService()
        self._categorie_id: int | None = None
        self._category_buttons: list[QPushButton] = []
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)
        self.search_input = QLineEdit()
        self.search_input.setObjectName("productLookupSearch")
        self.search_input.setPlaceholderText("Rechercher par nom ou code-barres...")
        self.search_input.setAccessibleName("Rechercher un produit par nom ou code-barres")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.addAction(ui_icon("search", "#526b8b", 19), QLineEdit.ActionPosition.LeadingPosition)
        self.search_input.textChanged.connect(self._charger)
        root.addWidget(self.search_input)

        self.categories_scroll = QScrollArea()
        self.categories_scroll.setObjectName("productCategoriesScroll")
        self.categories_scroll.setWidgetResizable(True)
        self.categories_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.categories_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.categories_scroll.setFixedHeight(54)
        categories_host = QWidget()
        self.categories_layout = QHBoxLayout(categories_host)
        self.categories_layout.setContentsMargins(0, 4, 0, 4)
        self.categories_layout.setSpacing(10)
        self.categories_layout.addStretch(1)
        self.categories_scroll.setWidget(categories_host)
        root.addWidget(self.categories_scroll)

        panel = QFrame()
        panel.setObjectName("productLookupPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)
        self.table = QTableWidget(0, 6)
        self.table.setObjectName("productLookupTable")
        self.table.setHorizontalHeaderLabels(["Code-barres", "Produit", "Catégorie", "Prix (CDF)", "Stock vendable", "Statut"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for column in (0, 2, 3, 4, 5):
            self.table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAccessibleName("Liste des produits et de leur stock vendable")
        panel_layout.addWidget(self.table, 1)
        self.empty_label = QLabel("Aucun produit ne correspond à votre recherche.")
        self.empty_label.setObjectName("productLookupEmpty")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        panel_layout.addWidget(self.empty_label)
        root.addWidget(panel, 1)

        info = QFrame()
        info.setObjectName("productLookupInfo")
        info_layout = QHBoxLayout(info)
        info_layout.setContentsMargins(16, 10, 16, 10)
        icon = QLabel()
        icon.setPixmap(ui_icon("info", "#1269c7", 18).pixmap(18, 18))
        message = QLabel("Les produits en rupture ou sans lot vendable ne peuvent pas être vendus.")
        message.setObjectName("productLookupInfoText")
        info_layout.addWidget(icon)
        info_layout.addWidget(message, 1)
        root.addWidget(info)

    def on_show(self) -> None:
        self._charger_categories()
        self._charger()

    def appliquer_recherche(self, terme: str) -> None:
        self.search_input.setText(terme)
        self.search_input.setFocus()

    def _charger_categories(self) -> None:
        try:
            categories = self._vente_service.lister_categories_consultation(self.session_utilisateur)
        except SalmospharmError as exc:
            QMessageBox.warning(self, "Recherche impossible", str(exc))
            return
        while self.categories_layout.count() > 1:
            item = self.categories_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._category_buttons.clear()
        group = QButtonGroup(self)
        group.setExclusive(True)
        for title, category_id in [("Tous", None), *[(category.nom, category.id) for category in categories]]:
            button = QPushButton(title)
            button.setObjectName("productCategoryChip")
            button.setCheckable(True)
            button.setChecked(category_id is None and self._categorie_id is None)
            button.clicked.connect(lambda checked=False, value=category_id: self._choisir_categorie(value))
            group.addButton(button)
            self.categories_layout.insertWidget(self.categories_layout.count() - 1, button)
            self._category_buttons.append(button)

    def _choisir_categorie(self, category_id: int | None) -> None:
        self._categorie_id = category_id
        self._charger()

    def _charger(self, *_args) -> None:
        try:
            produits = self._vente_service.consulter_stock_produits(
                self.session_utilisateur,
                terme=self.search_input.text().strip(),
                categorie_id=self._categorie_id,
            )
        except SalmospharmError as exc:
            QMessageBox.warning(self, "Recherche impossible", str(exc))
            return
        self.table.setRowCount(len(produits))
        self.empty_label.setVisible(not produits)
        for row, produit in enumerate(produits):
            self.table.setRowHeight(row, 48)
            values = (
                produit.code_barres or "—",
                produit.nom,
                produit.categorie_nom or "Sans catégorie",
                _number(produit.prix_vente),
                str(produit.stock_disponible),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 1:
                    item.setIcon(ui_icon("product", "#526b8b", 18))
                    item.setToolTip(produit.description or produit.nom)
                if column in {3, 4}:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, column, item)
            status, tone = _stock_status(produit)
            self.table.setCellWidget(row, 5, _status_badge(status, tone))


def _stock_status(produit: ProduitConsultationStock) -> tuple[str, str]:
    if produit.stock_disponible <= 0:
        return "Rupture", "red"
    if produit.stock_disponible <= produit.stock_minimum:
        return "Stock faible", "orange"
    return "En stock", "green"


def _status_badge(text: str, tone: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("productStockBadge")
    label.setProperty("tone", tone)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return label


def _number(value: int) -> str:
    return f"{value:,}".replace(",", " ")
