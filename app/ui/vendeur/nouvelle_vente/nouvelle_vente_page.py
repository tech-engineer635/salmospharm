"""Interface point de vente vendeur, connectee au service de vente."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.core.exceptions import ImprimanteIndisponibleError, SalmospharmError
from app.database.models import Categorie
from app.services.auth_service import SessionUtilisateur
from app.services.impression_service import ImpressionService
from app.services.produit_service import ProduitService
from app.services.ticket_service import TicketService
from app.services.vente_service import LignePanierPayload, ProduitVendable, VentePayload, VenteService
from app.ui.components.icons import ui_icon


@dataclass
class CartLine:
    produit: ProduitVendable
    quantite: int

    @property
    def sous_total(self) -> int:
        return self.produit.prix_vente * self.quantite


class NouvelleVentePage(QWidget):
    """Ecran vendeur pour composer un panier puis valider une vente definitive."""

    ticket_genere = Signal(object, str)

    def __init__(
        self,
        session_utilisateur: SessionUtilisateur,
        vente_service: VenteService | None = None,
        produit_service: ProduitService | None = None,
        ticket_service: TicketService | None = None,
        impression_service: ImpressionService | None = None,
        autoload: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("salePage")
        self.session_utilisateur = session_utilisateur
        self._vente_service = vente_service or VenteService()
        self._produit_service = produit_service or ProduitService()
        self._ticket_service = ticket_service or TicketService()
        self._impression_service = impression_service or ImpressionService()
        self._categories: list[Categorie] = []
        self._produits: list[ProduitVendable] = []
        self._categorie_active: int | None = None
        self._cart: dict[int, CartLine] = {}
        self._category_buttons: list[QPushButton] = []
        self._build_ui()
        if autoload:
            self.on_show()

    def on_show(self) -> None:
        self._charger_categories()
        self._charger_produits()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addLayout(self._build_header())
        layout.addWidget(self._build_catalog_panel())

        bottom = QHBoxLayout()
        bottom.setSpacing(16)
        bottom.addWidget(self._build_cart_panel(), 1)
        bottom.addWidget(self._build_summary_panel(), 0)
        layout.addLayout(bottom, 1)

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        text = QVBoxLayout()
        text.setSpacing(4)
        title = QLabel("Nouvelle vente")
        title.setObjectName("saleTitle")
        subtitle = QLabel("Point de vente")
        subtitle.setObjectName("saleSubtitle")
        text.addWidget(title)
        text.addWidget(subtitle)
        header.addLayout(text, 1)
        return header

    def _build_catalog_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("salePanel")
        panel.setMinimumHeight(248)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("saleSearch")
        self.search_input.setPlaceholderText("Rechercher un produit (nom, principe actif...)")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.addAction(ui_icon("search", "#506b92", 18), QLineEdit.ActionPosition.LeadingPosition)
        self.search_input.textChanged.connect(self._charger_produits)
        layout.addWidget(self.search_input, alignment=Qt.AlignmentFlag.AlignLeft)

        self.categories_row = QHBoxLayout()
        self.categories_row.setSpacing(12)
        layout.addLayout(self.categories_row)

        self.products_grid = QGridLayout()
        self.products_grid.setHorizontalSpacing(18)
        self.products_grid.setVerticalSpacing(14)
        layout.addLayout(self.products_grid)
        return panel

    def _build_cart_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("salePanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(8)

        title = QLabel("Panier de vente")
        title.setObjectName("salePanelTitle")
        layout.addWidget(title)

        header = QGridLayout()
        header.setColumnStretch(0, 3)
        header.setColumnStretch(1, 1)
        header.setColumnStretch(2, 1)
        header.setColumnStretch(3, 1)
        header.setColumnStretch(4, 0)
        for column, text in enumerate(("Produit", "Prix unitaire (CDF)", "Quantite", "Total (CDF)", "Action")):
            label = QLabel(text)
            label.setObjectName("cartHeader")
            header.addWidget(label, 0, column)
        layout.addLayout(header)

        self.cart_rows = QVBoxLayout()
        self.cart_rows.setSpacing(0)
        layout.addLayout(self.cart_rows)

        footer = QHBoxLayout()
        self.clear_button = QPushButton("Vider le panier")
        self.clear_button.setObjectName("dangerButton")
        self.clear_button.setIcon(ui_icon("trash", "#d21f32", 17))
        self.clear_button.clicked.connect(self._vider_panier)
        self.items_count_label = QLabel("0 article(s)")
        self.items_count_label.setObjectName("cartCount")
        footer.addWidget(self.clear_button)
        footer.addStretch(1)
        footer.addWidget(self.items_count_label)
        layout.addLayout(footer)
        layout.addStretch(1)
        return panel

    def _build_summary_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("salePanel")
        panel.setFixedWidth(340)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(6)

        title_row = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(ui_icon("receipt", "#0b3567", 22).pixmap(22, 22))
        title = QLabel("Recapitulatif")
        title.setObjectName("salePanelTitle")
        title_row.addWidget(title_icon)
        title_row.addWidget(title)
        title_row.addStretch(1)
        layout.addLayout(title_row)

        self.subtotal_label = _summary_value("0 CDF")
        layout.addLayout(_summary_row("Sous-total", self.subtotal_label))

        self.discount_input = QLineEdit("0")
        self.discount_input.setObjectName("saleAmountInput")
        self.discount_input.setEnabled(False)
        self.discount_input.setToolTip("Remise non activee en version 1.0 : total recalcule sans remise.")
        discount_suffix = QLabel("CDF")
        discount_suffix.setObjectName("summaryCurrency")
        discount_row = QHBoxLayout()
        discount_row.addWidget(_summary_label("Remise"))
        discount_row.addWidget(self.discount_input)
        discount_row.addWidget(discount_suffix)
        layout.addLayout(discount_row)

        separator = QFrame()
        separator.setObjectName("summarySeparator")
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        self.total_label = QLabel("0 CDF")
        self.total_label.setObjectName("totalAmount")
        layout.addLayout(_summary_row("Total a payer", self.total_label))

        self.received_input = QSpinBox()
        self.received_input.setObjectName("saleAmountInput")
        self.received_input.setRange(0, 999_999_999)
        self.received_input.setSuffix(" CDF")
        self.received_input.valueChanged.connect(self._maj_resume)
        layout.addLayout(_field_group("Montant recu *", self.received_input))
        self.payment_hint_label = QLabel("Ajoutez un produit au panier pour encaisser.")
        self.payment_hint_label.setObjectName("paymentHint")
        self.payment_hint_label.setWordWrap(True)
        layout.addWidget(self.payment_hint_label)

        self.change_label = _summary_value("0 CDF")
        layout.addLayout(_summary_row("Monnaie", self.change_label))
        layout.addLayout(_summary_row("Devise", _summary_value("CDF")))

        info = QLabel("Paiement en especes uniquement")
        info.setObjectName("cashInfo")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)

        self.cash_button = QPushButton("Encaisser")
        self.cash_button.setObjectName("primaryButton")
        self.cash_button.setIcon(ui_icon("money", "#ffffff", 18))
        self.cash_button.clicked.connect(self._encaisser)
        layout.addWidget(self.cash_button)

        self.print_button = QPushButton("Imprimer facture")
        self.print_button.setObjectName("outlineButton")
        self.print_button.setIcon(ui_icon("ticket", "#0b3567", 18))
        self.print_button.setEnabled(False)
        self.print_button.setToolTip("L'impression sera branchee a la phase ticket/impression.")
        layout.addWidget(self.print_button)
        layout.addStretch(1)
        return panel

    def _charger_categories(self) -> None:
        try:
            self._categories = self._produit_service.lister_categories(self.session_utilisateur)
        except SalmospharmError as exc:
            self._afficher_erreur(str(exc))
            self._categories = []
        self._remplir_categories()

    def _remplir_categories(self) -> None:
        _clear_layout(self.categories_row)
        self._category_buttons = []
        all_button = self._category_button("Tous", None)
        self.categories_row.addWidget(all_button)
        for categorie in self._categories[:6]:
            self.categories_row.addWidget(self._category_button(categorie.nom, categorie.id))
        self.categories_row.addStretch(1)
        self._sync_category_buttons()

    def _category_button(self, label: str, categorie_id: int | None) -> QPushButton:
        button = QPushButton(label)
        button.setObjectName("categoryChip")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(lambda checked=False, value=categorie_id: self._changer_categorie(value))
        self._category_buttons.append(button)
        return button

    def _changer_categorie(self, categorie_id: int | None) -> None:
        self._categorie_active = categorie_id
        self._sync_category_buttons()
        self._charger_produits()

    def _sync_category_buttons(self) -> None:
        for button in self._category_buttons:
            active = (button.text() == "Tous" and self._categorie_active is None) or any(
                categorie.id == self._categorie_active and categorie.nom == button.text()
                for categorie in self._categories
            )
            button.setProperty("active", active)
            button.style().unpolish(button)
            button.style().polish(button)

    def _charger_produits(self) -> None:
        try:
            self._produits = self._vente_service.lister_produits_vendables(
                self.session_utilisateur,
                terme=self.search_input.text(),
                categorie_id=self._categorie_active,
            )
        except SalmospharmError as exc:
            self._afficher_erreur(str(exc))
            self._produits = []
        self._remplir_produits()

    def _remplir_produits(self) -> None:
        _clear_layout(self.products_grid)
        if not self._produits:
            empty = QLabel("Aucun produit vendable trouve. Verifiez que le produit est actif et qu'un lot non expire contient du stock.")
            empty.setObjectName("saleEmpty")
            empty.setWordWrap(True)
            self.products_grid.addWidget(empty, 0, 0)
            return
        for index, produit in enumerate(self._produits[:8]):
            card = ProductCard(produit)
            card.add_button.clicked.connect(lambda checked=False, p=produit: self._ajouter_au_panier(p))
            self.products_grid.addWidget(card, index // 4, index % 4)

    def _ajouter_au_panier(self, produit: ProduitVendable) -> None:
        line = self._cart.get(produit.produit_id)
        quantite_actuelle = line.quantite if line is not None else 0
        if quantite_actuelle >= produit.stock_disponible:
            self._afficher_erreur("Stock insuffisant pour ce produit.")
            return
        self._cart[produit.produit_id] = CartLine(produit=produit, quantite=quantite_actuelle + 1)
        self._remplir_panier()

    def _changer_quantite(self, produit_id: int, quantite: int) -> None:
        line = self._cart.get(produit_id)
        if line is None:
            return
        if quantite <= 0:
            self._cart.pop(produit_id, None)
        elif quantite <= line.produit.stock_disponible:
            line.quantite = quantite
        else:
            self._afficher_erreur("Stock insuffisant pour ce produit.")
        self._remplir_panier()

    def _retirer_ligne(self, produit_id: int) -> None:
        self._cart.pop(produit_id, None)
        self._remplir_panier()

    def _vider_panier(self) -> None:
        self._cart.clear()
        self._remplir_panier()

    def _remplir_panier(self) -> None:
        _clear_layout(self.cart_rows)
        previous_total = int(self.total_label.text().replace(" CDF", "").replace(" ", "")) if hasattr(self, "total_label") else 0
        for line in self._cart.values():
            row = CartRow(line)
            row.minus_button.clicked.connect(lambda checked=False, item=line: self._changer_quantite(item.produit.produit_id, item.quantite - 1))
            row.plus_button.clicked.connect(lambda checked=False, item=line: self._changer_quantite(item.produit.produit_id, item.quantite + 1))
            row.remove_button.clicked.connect(lambda checked=False, item=line: self._retirer_ligne(item.produit.produit_id))
            self.cart_rows.addWidget(row)
        if not self._cart:
            empty = QLabel("Le panier est vide.")
            empty.setObjectName("saleEmpty")
            self.cart_rows.addWidget(empty)
        total = sum(line.sous_total for line in self._cart.values())
        if total > 0 and self.received_input.value() <= previous_total:
            self.received_input.setValue(total)
        self._maj_resume()

    def _maj_resume(self) -> None:
        total = sum(line.sous_total for line in self._cart.values())
        count = sum(line.quantite for line in self._cart.values())
        self.subtotal_label.setText(_format_cdf(total))
        self.total_label.setText(_format_cdf(total))
        self.items_count_label.setText(f"{count} article(s)")
        self.change_label.setText(_format_cdf(max(0, self.received_input.value() - total)))
        if total <= 0:
            self.payment_hint_label.setText("Ajoutez un produit au panier pour encaisser.")
        elif self.received_input.value() < total:
            self.payment_hint_label.setText("Le montant recu est inferieur au total a payer.")
        else:
            self.payment_hint_label.setText("Pret a encaisser en especes.")
        self.cash_button.setEnabled(total > 0)
        self.clear_button.setEnabled(bool(self._cart))

    def _encaisser(self) -> None:
        total = sum(line.sous_total for line in self._cart.values())
        if total <= 0:
            self._afficher_erreur("Le panier est vide.")
            return
        if self.received_input.value() < total:
            self.received_input.setFocus()
            self._afficher_erreur("Le montant recu est insuffisant.")
            return
        try:
            result = self._vente_service.valider_vente(
                self.session_utilisateur,
                VentePayload(
                    lignes=[
                        LignePanierPayload(produit_id=line.produit.produit_id, quantite=line.quantite)
                        for line in self._cart.values()
                    ],
                    montant_recu=self.received_input.value(),
                ),
            )
            ticket = self._ticket_service.generer_ticket(self.session_utilisateur, result.vente_id)
            impression_message = self._gerer_impression_auto(ticket)
            self._cart.clear()
            self.received_input.setValue(0)
            self._charger_produits()
            self._remplir_panier()
            self.print_button.setEnabled(True)
            self.ticket_genere.emit(ticket, impression_message)
        except SalmospharmError as exc:
            self._afficher_erreur(str(exc))

    def _gerer_impression_auto(self, ticket) -> str:
        if not ticket.impression_auto:
            return f"Vente {ticket.numero_vente} validee. Apercu du ticket genere."
        try:
            self._impression_service.imprimer_ticket(ticket)
            self._ticket_service.journaliser_impression(self.session_utilisateur, ticket)
            return f"Vente {ticket.numero_vente} validee. Ticket envoye a l'imprimante."
        except ImprimanteIndisponibleError as exc:
            self._ticket_service.journaliser_erreur_impression(self.session_utilisateur, ticket, str(exc))
            return f"Vente {ticket.numero_vente} validee. {exc}"

    def _afficher_info(self, message: str) -> None:
        QMessageBox.information(self, "SALMOSPHARM", message)

    def _afficher_erreur(self, message: str) -> None:
        QMessageBox.warning(self, "SALMOSPHARM", message)


class ProductCard(QFrame):
    def __init__(self, produit: ProduitVendable) -> None:
        super().__init__()
        self.setObjectName("productSaleCard")
        self.setMinimumSize(206, 164)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 10)
        layout.setSpacing(5)

        top = QHBoxLayout()
        thumbnail = QLabel()
        thumbnail.setObjectName("productThumbnail")
        thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumbnail.setText("SALMO")
        thumbnail.setFixedSize(64, 42)
        name = QLabel(produit.nom)
        name.setObjectName("productCardName")
        name.setWordWrap(True)
        top.addWidget(thumbnail)
        top.addWidget(name, 1)
        top.addWidget(QLabel("*"))
        layout.addLayout(top)

        desc = QLabel(produit.description or produit.categorie_nom or "Boite de 20 comprimes")
        desc.setObjectName("productCardDesc")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addStretch(1)

        price = QLabel(_format_cdf(produit.prix_vente))
        price.setObjectName("productCardPrice")
        stock = QLabel(f"En stock ({produit.stock_disponible})")
        stock.setObjectName("productCardStock")
        self.add_button = QPushButton("Ajouter")
        self.add_button.setObjectName("successButton")
        self.add_button.setIcon(ui_icon("plus", "#0a7f31", 17))
        layout.addWidget(price)
        layout.addWidget(stock)
        layout.addWidget(self.add_button)


class CartRow(QFrame):
    def __init__(self, line: CartLine) -> None:
        super().__init__()
        self.setObjectName("cartRow")
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setHorizontalSpacing(12)
        layout.setColumnStretch(0, 3)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)
        layout.setColumnStretch(3, 1)

        product_box = QHBoxLayout()
        thumbnail = QLabel("SALMO")
        thumbnail.setObjectName("cartThumb")
        thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumbnail.setFixedSize(48, 34)
        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        name = QLabel(line.produit.nom)
        name.setObjectName("cartProductName")
        desc = QLabel(line.produit.description or line.produit.categorie_nom or "Boite de 20 comprimes")
        desc.setObjectName("cartProductDesc")
        text_box.addWidget(name)
        text_box.addWidget(desc)
        product_box.addWidget(thumbnail)
        product_box.addLayout(text_box, 1)
        layout.addLayout(product_box, 0, 0)

        price = QLabel(_format_number(line.produit.prix_vente))
        price.setObjectName("cartValue")
        layout.addWidget(price, 0, 1, alignment=Qt.AlignmentFlag.AlignCenter)

        qty = QHBoxLayout()
        qty.setSpacing(0)
        self.minus_button = _quantity_button("-")
        qty_value = QLabel(str(line.quantite))
        qty_value.setObjectName("quantityValue")
        qty_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qty_value.setFixedSize(42, 32)
        self.plus_button = _quantity_button("+")
        qty.addWidget(self.minus_button)
        qty.addWidget(qty_value)
        qty.addWidget(self.plus_button)
        layout.addLayout(qty, 0, 2, alignment=Qt.AlignmentFlag.AlignCenter)

        total = QLabel(_format_number(line.sous_total))
        total.setObjectName("cartValue")
        layout.addWidget(total, 0, 3, alignment=Qt.AlignmentFlag.AlignCenter)

        self.remove_button = QPushButton()
        self.remove_button.setObjectName("iconDangerButton")
        self.remove_button.setIcon(ui_icon("trash", "#e11d2e", 18))
        self.remove_button.setFixedSize(34, 34)
        layout.addWidget(self.remove_button, 0, 4, alignment=Qt.AlignmentFlag.AlignCenter)


def _quantity_button(text: str) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("quantityButton")
    button.setFixedSize(34, 32)
    return button


def _field_group(label_text: str, field: QWidget) -> QVBoxLayout:
    group = QVBoxLayout()
    group.setSpacing(6)
    label = _summary_label(label_text)
    group.addWidget(label)
    group.addWidget(field)
    return group


def _summary_row(label_text: str, value: QLabel) -> QHBoxLayout:
    row = QHBoxLayout()
    row.addWidget(_summary_label(label_text))
    row.addStretch(1)
    row.addWidget(value)
    return row


def _summary_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("summaryLabel")
    return label


def _summary_value(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("summaryValue")
    return label


def _format_number(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def _format_cdf(value: int) -> str:
    return f"{_format_number(value)} CDF"


def _clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        child = item.widget()
        if child is not None:
            child.setParent(None)
            child.deleteLater()
        nested = item.layout()
        if nested is not None:
            _clear_layout(nested)
