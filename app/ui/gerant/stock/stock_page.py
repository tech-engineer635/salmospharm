"""Page gerant de gestion des lots et mouvements de stock."""

from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.exceptions import SalmospharmError
from app.database.models import LotProduit
from app.services.auth_service import SessionUtilisateur
from app.services.produit_service import ProduitService
from app.services.stock_service import AjustementStockPayload, EntreeStockPayload, StockService
from app.ui.components.icons import ui_icon


class StockPage(QWidget):
    """Interface stock par lots, connectee uniquement aux services metier."""

    def __init__(
        self,
        session_utilisateur: SessionUtilisateur,
        stock_service: StockService | None = None,
        produit_service: ProduitService | None = None,
        autoload: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("stockPage")
        self.session_utilisateur = session_utilisateur
        self._stock_service = stock_service or StockService()
        self._produit_service = produit_service or ProduitService()
        self._produits = {}
        self._lots: list[LotProduit] = []
        self._build_ui()
        if autoload:
            self.on_show()

    def on_show(self) -> None:
        self._charger_produits()
        self._charger_lots()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addLayout(self._build_header())
        layout.addLayout(self._build_metrics())

        body = QHBoxLayout()
        body.setSpacing(18)
        main = QVBoxLayout()
        main.setSpacing(8)
        main.addWidget(self._build_lots_panel(), 2)
        main.addWidget(self._build_movements_panel(), 1)

        side_container = QWidget()
        side_container.setObjectName("stockSideContainer")
        side = QVBoxLayout()
        side.setContentsMargins(0, 0, 0, 0)
        side.setSpacing(14)
        side.addWidget(self._build_entry_panel())
        side.addWidget(self._build_adjustment_panel())
        side.addStretch(1)
        side_container.setLayout(side)

        self.side_scroll = QScrollArea()
        self.side_scroll.setObjectName("stockSideScroll")
        self.side_scroll.setWidgetResizable(True)
        self.side_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.side_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.side_scroll.setFixedWidth(392)
        self.side_scroll.setWidget(side_container)

        body.addLayout(main, 1)
        body.addWidget(self.side_scroll)
        layout.addLayout(body, 1)

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        text = QVBoxLayout()
        text.setSpacing(4)
        title = QLabel("Gestion du stock")
        title.setObjectName("productsPageTitle")
        subtitle = QLabel("Gerez les lots, les entrees et les ajustements de quantite.")
        subtitle.setObjectName("productsPageSubtitle")
        text.addWidget(title)
        text.addWidget(subtitle)
        refresh = QPushButton("Actualiser")
        refresh.setObjectName("outlineButton")
        refresh.setIcon(ui_icon("refresh", "#0b3567", 17))
        refresh.clicked.connect(self.on_show)
        header.addLayout(text, 1)
        header.addWidget(refresh)
        return header

    def _build_metrics(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)
        self.lots_metric = StockMetricCard("Lots suivis", "0", "Lots physiques", "stock", "blue")
        self.units_metric = StockMetricCard("Unites en lots", "0", "Quantite totale", "product", "green")
        self.expiry_metric = StockMetricCard("Expirations proches", "0", "Selon seuil", "calendar", "orange")
        self.empty_metric = StockMetricCard("Lots vides", "0", "Quantite 0", "warning", "purple")
        for card in (self.lots_metric, self.units_metric, self.expiry_metric, self.empty_metric):
            row.addWidget(card, 1)
        return row

    def _build_lots_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("contentPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.lots_table = QTableWidget(0, 6)
        self.lots_table.setObjectName("productsTable")
        self.lots_table.setHorizontalHeaderLabels(["Produit", "Lot", "Quantite", "Prix achat", "Expiration", "Statut"])
        header = self.lots_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.lots_table.verticalHeader().setVisible(False)
        self.lots_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.lots_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.lots_table.itemSelectionChanged.connect(self._charger_lot_selectionne)
        self.lots_table.setMinimumHeight(260)
        layout.addWidget(self.lots_table)
        return panel

    def _build_movements_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("contentPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        title = QLabel("Mouvements recents")
        title.setObjectName("sidePanelTitle")
        self.movements_table = QTableWidget(0, 4)
        self.movements_table.setObjectName("productsTable")
        self.movements_table.setHorizontalHeaderLabels(["Type", "Produit", "Quantite", "Motif"])
        self.movements_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.movements_table.verticalHeader().setVisible(False)
        self.movements_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.movements_table.setMaximumHeight(135)
        layout.addWidget(title)
        layout.addWidget(self.movements_table)
        return panel

    def _build_entry_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("contentPanel")
        panel.setFixedWidth(372)
        panel.setMinimumHeight(408)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        title = QLabel("Entree de stock")
        title.setObjectName("sidePanelTitle")
        self.entry_product_combo = QComboBox()
        self.entry_lot_input = QLineEdit()
        self.entry_lot_input.setPlaceholderText("Ex : LOT-2026-A")
        self.entry_quantity_input = QSpinBox()
        self.entry_quantity_input.setRange(1, 999_999)
        self.entry_price_input = QSpinBox()
        self.entry_price_input.setRange(0, 999_999_999)
        self.entry_price_input.setSuffix(" CDF")
        self.entry_expiration_known = QCheckBox("Date d'expiration connue")
        self.entry_expiration_known.setChecked(True)
        self.entry_expiration_input = QDateEdit()
        self.entry_expiration_input.setCalendarPopup(True)
        self.entry_expiration_input.setDisplayFormat("yyyy-MM-dd")
        self.entry_expiration_input.setDate(QDate.currentDate().addMonths(12))
        self.entry_expiration_known.toggled.connect(self.entry_expiration_input.setEnabled)
        self.entry_motif_input = QLineEdit()
        self.entry_motif_input.setPlaceholderText("Reception fournisseur")
        self.entry_submit_button = QPushButton("Enregistrer l'entree")
        self.entry_submit_button.setObjectName("primaryButton")
        self.entry_submit_button.clicked.connect(self._enregistrer_entree)
        for field in (
            self.entry_product_combo,
            self.entry_lot_input,
            self.entry_quantity_input,
            self.entry_price_input,
            self.entry_expiration_input,
            self.entry_motif_input,
        ):
            _configure_form_field(field)
        self.entry_expiration_known.setMinimumHeight(30)

        layout.addWidget(title)
        layout.addLayout(_field_group("Produit *", self.entry_product_combo))
        layout.addLayout(_field_group("Numero de lot", self.entry_lot_input))
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(0)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.addLayout(_field_group("Quantite *", self.entry_quantity_input), 0, 0)
        grid.addLayout(_field_group("Prix achat *", self.entry_price_input), 0, 1)
        layout.addLayout(grid)
        expiration_row = QHBoxLayout()
        expiration_row.setSpacing(12)
        expiration_row.addWidget(self.entry_expiration_known, 0)
        expiration_row.addWidget(self.entry_expiration_input, 1)
        layout.addLayout(expiration_row)
        layout.addLayout(_field_group("Motif", self.entry_motif_input))
        layout.addWidget(self.entry_submit_button)
        return panel

    def _build_adjustment_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("contentPanel")
        panel.setFixedWidth(372)
        panel.setMinimumHeight(286)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        title = QLabel("Ajustement")
        title.setObjectName("sidePanelTitle")
        self.adjust_lot_combo = QComboBox()
        self.adjust_quantity_input = QSpinBox()
        self.adjust_quantity_input.setRange(0, 999_999)
        self.adjust_motif_input = QLineEdit()
        self.adjust_motif_input.setPlaceholderText("Correction inventaire")
        self.adjust_submit_button = QPushButton("Ajuster le lot")
        self.adjust_submit_button.setObjectName("blueButton")
        self.adjust_submit_button.clicked.connect(self._ajuster_lot)
        hint = QLabel("Le motif est obligatoire pour tracer l'ajustement.")
        hint.setObjectName("productStatusHint")
        hint.setWordWrap(True)
        for field in (self.adjust_lot_combo, self.adjust_quantity_input, self.adjust_motif_input):
            _configure_form_field(field)
        layout.addWidget(title)
        layout.addLayout(_field_group("Lot *", self.adjust_lot_combo))
        layout.addLayout(_field_group("Nouvelle quantite *", self.adjust_quantity_input))
        layout.addLayout(_field_group("Motif *", self.adjust_motif_input))
        layout.addWidget(hint)
        layout.addWidget(self.adjust_submit_button)
        return panel

    def _charger_produits(self) -> None:
        produits = self._produit_service.rechercher_produits(
            self.session_utilisateur,
            terme="",
            actifs_seulement=True,
        )
        self._produits = {produit.id: produit for produit in produits}
        self.entry_product_combo.clear()
        for produit in produits:
            self.entry_product_combo.addItem(produit.nom, produit.id)

    def _charger_lots(self) -> None:
        self._lots = self._stock_service.lister_lots(self.session_utilisateur)
        self._remplir_table_lots()
        self._remplir_combo_ajustement()
        self._charger_mouvements()
        self._maj_metriques()

    def _remplir_table_lots(self) -> None:
        self.lots_table.setRowCount(0)
        today = date.today().isoformat()
        for lot in self._lots:
            produit = self._produits.get(lot.produit_id)
            row = self.lots_table.rowCount()
            self.lots_table.insertRow(row)
            statut = "Expire" if lot.date_expiration and lot.date_expiration < today else ("Vide" if lot.quantite == 0 else "Disponible")
            values = [
                produit.nom if produit is not None else f"Produit #{lot.produit_id}",
                lot.numero_lot or f"LOT-{lot.id:05d}",
                str(lot.quantite),
                f"{lot.prix_achat:,} CDF".replace(",", " "),
                lot.date_expiration or "Non renseignee",
                statut,
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, lot.id)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | (Qt.AlignmentFlag.AlignHCenter if column in {2, 3, 5} else Qt.AlignmentFlag.AlignLeft))
                self.lots_table.setItem(row, column, item)
            self.lots_table.setRowHeight(row, 38)

    def _remplir_combo_ajustement(self) -> None:
        current = self.adjust_lot_combo.currentData()
        self.adjust_lot_combo.clear()
        for lot in self._lots:
            produit = self._produits.get(lot.produit_id)
            label = f"{produit.nom if produit else 'Produit'} - {lot.numero_lot or lot.id} ({lot.quantite})"
            self.adjust_lot_combo.addItem(label, lot.id)
        _select_combo_data(self.adjust_lot_combo, current)

    def _charger_mouvements(self) -> None:
        mouvements = self._stock_service.lister_mouvements_recents(self.session_utilisateur, limit=8)
        self.movements_table.setRowCount(0)
        for mouvement in mouvements:
            produit = self._produits.get(mouvement.produit_id)
            row = self.movements_table.rowCount()
            self.movements_table.insertRow(row)
            values = [
                mouvement.type_mouvement,
                produit.nom if produit else f"Produit #{mouvement.produit_id}",
                str(mouvement.quantite),
                mouvement.motif or "",
            ]
            for column, value in enumerate(values):
                self.movements_table.setItem(row, column, QTableWidgetItem(value))
            self.movements_table.setRowHeight(row, 34)

    def _maj_metriques(self) -> None:
        today = date.today()
        near_limit = today + timedelta(days=30)
        expirations = 0
        for lot in self._lots:
            if not lot.date_expiration:
                continue
            try:
                expiration = date.fromisoformat(lot.date_expiration)
            except ValueError:
                continue
            if today <= expiration <= near_limit:
                expirations += 1
        self.lots_metric.set_value(str(len(self._lots)), "Lots physiques")
        self.units_metric.set_value(str(sum(lot.quantite for lot in self._lots)), "Quantite totale")
        self.expiry_metric.set_value(str(expirations), "30 prochains jours")
        self.empty_metric.set_value(str(sum(1 for lot in self._lots if lot.quantite == 0)), "Quantite 0")

    def _enregistrer_entree(self) -> None:
        produit_id = self.entry_product_combo.currentData()
        if produit_id is None:
            self._afficher_erreur("Selectionnez un produit.")
            return
        expiration = self.entry_expiration_input.date().toString("yyyy-MM-dd") if self.entry_expiration_known.isChecked() else None
        try:
            self._stock_service.entrer_stock(
                self.session_utilisateur,
                EntreeStockPayload(
                    produit_id=produit_id,
                    numero_lot=self.entry_lot_input.text(),
                    quantite=self.entry_quantity_input.value(),
                    prix_achat=self.entry_price_input.value(),
                    date_expiration=expiration,
                    motif=self.entry_motif_input.text(),
                ),
            )
            self.entry_lot_input.clear()
            self.entry_quantity_input.setValue(1)
            self.entry_price_input.setValue(0)
            self.entry_motif_input.clear()
            self._charger_lots()
            self._afficher_info("Entree de stock enregistree.")
        except SalmospharmError as exc:
            self._afficher_erreur(str(exc))

    def _ajuster_lot(self) -> None:
        lot_id = self.adjust_lot_combo.currentData()
        if lot_id is None:
            self._afficher_erreur("Selectionnez un lot.")
            return
        try:
            self._stock_service.ajuster_stock(
                self.session_utilisateur,
                AjustementStockPayload(
                    lot_id=lot_id,
                    nouvelle_quantite=self.adjust_quantity_input.value(),
                    motif=self.adjust_motif_input.text(),
                ),
            )
            self.adjust_motif_input.clear()
            self._charger_lots()
            self._afficher_info("Ajustement enregistre.")
        except SalmospharmError as exc:
            self._afficher_erreur(str(exc))

    def _charger_lot_selectionne(self) -> None:
        items = self.lots_table.selectedItems()
        if not items:
            return
        lot_id = items[0].data(Qt.ItemDataRole.UserRole)
        lot = next((lot for lot in self._lots if lot.id == lot_id), None)
        if lot is None:
            return
        _select_combo_data(self.adjust_lot_combo, lot.id)
        self.adjust_quantity_input.setValue(lot.quantite)

    def _afficher_info(self, message: str) -> None:
        QMessageBox.information(self, "SALMOSPHARM", message)

    def _afficher_erreur(self, message: str) -> None:
        QMessageBox.warning(self, "SALMOSPHARM", message)


class StockMetricCard(QFrame):
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
        text = QVBoxLayout()
        text.setSpacing(3)
        title_label = QLabel(title)
        title_label.setObjectName("productMetricTitle")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("productMetricValue")
        self.trend_label = QLabel(trend)
        self.trend_label.setObjectName(f"productMetricTrend_{color}")
        text.addWidget(title_label)
        text.addWidget(self.value_label)
        text.addWidget(self.trend_label)
        layout.addWidget(icon_label)
        layout.addLayout(text, 1)

    def set_value(self, value: str, trend: str) -> None:
        self.value_label.setText(value)
        self.trend_label.setText(trend)


def _field_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("formFieldLabel")
    label.setMinimumHeight(16)
    return label


def _field_group(label_text: str, field: QWidget) -> QVBoxLayout:
    group = QVBoxLayout()
    group.setContentsMargins(0, 0, 0, 0)
    group.setSpacing(6)
    group.addWidget(_field_label(label_text))
    group.addWidget(field)
    return group


def _configure_form_field(field: QWidget) -> None:
    field.setMinimumHeight(36)
    field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


def _select_combo_data(combo: QComboBox, data: int | None) -> None:
    for index in range(combo.count()):
        if combo.itemData(index) == data:
            combo.setCurrentIndex(index)
            return
