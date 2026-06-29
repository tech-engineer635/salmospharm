"""Consultation en lecture seule des produits vendables."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.exceptions import SalmospharmError
from app.services.auth_service import SessionUtilisateur
from app.services.vente_service import VenteService


class RechercheProduitPage(QWidget):
    def __init__(
        self,
        session_utilisateur: SessionUtilisateur,
        vente_service: VenteService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.session_utilisateur = session_utilisateur
        self._vente_service = vente_service or VenteService()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        title = QLabel("Recherche produit")
        title.setObjectName("reportsTitle")
        layout.addWidget(title)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nom ou code-barres")
        self.search_input.setAccessibleName("Rechercher un produit vendable")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._charger)
        layout.addWidget(self.search_input)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Produit", "Categorie", "Description", "Prix (CDF)", "Stock vendable"]
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setAccessibleName("Liste des produits vendables")
        layout.addWidget(self.table, 1)

    def on_show(self) -> None:
        self._charger()

    def appliquer_recherche(self, terme: str) -> None:
        self.search_input.setText(terme)
        self.search_input.setFocus()

    def _charger(self, *_args) -> None:
        try:
            produits = self._vente_service.lister_produits_vendables(
                self.session_utilisateur, terme=self.search_input.text().strip()
            )
            self.table.setRowCount(len(produits))
            for row, produit in enumerate(produits):
                values = (
                    produit.nom,
                    produit.categorie_nom or "Sans categorie",
                    produit.description or "",
                    f"{produit.prix_vente:,}".replace(",", " "),
                    str(produit.stock_disponible),
                )
                for column, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    if column in {3, 4}:
                        item.setTextAlignment(
                            Qt.AlignmentFlag.AlignRight
                            | Qt.AlignmentFlag.AlignVCenter
                        )
                    self.table.setItem(row, column, item)
        except SalmospharmError as exc:
            QMessageBox.warning(self, "Recherche impossible", str(exc))
