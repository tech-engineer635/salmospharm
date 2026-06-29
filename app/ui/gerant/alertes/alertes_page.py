"""Consultation visuelle des alertes stock et expiration."""

from __future__ import annotations

from math import ceil

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from app.core.exceptions import SalmospharmError
from app.services.alerte_service import AlertePageResult, AlerteService
from app.services.auth_service import SessionUtilisateur
from app.ui.components.icons import ui_icon


class AlertesPage(QWidget):
    """Liste paginee des alertes actives reservee au gerant."""

    compteur_change = Signal(int)
    produit_demande = Signal(int)
    navigation_demandee = Signal(str)

    def __init__(self, session_utilisateur: SessionUtilisateur, alerte_service: AlerteService | None = None, autoload: bool = True, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("alertsPage")
        self.session_utilisateur = session_utilisateur
        self._alerte_service = alerte_service or AlerteService()
        self._page = 0
        self._page_size = 10
        self._result: AlertePageResult | None = None
        self._build_ui()
        if autoload:
            self.on_show()

    def on_show(self) -> None:
        self._charger()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)
        filters = QHBoxLayout()
        filters.setSpacing(10)
        self.search_input = QLineEdit()
        self.search_input.setObjectName("alertsSearch")
        self.search_input.setPlaceholderText("Rechercher un produit ou une alerte...")
        self.search_input.addAction(ui_icon("search", "#526b8b", 17), QLineEdit.ActionPosition.TrailingPosition)
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._reset_and_load)
        self.type_combo = QComboBox()
        self.type_combo.setObjectName("alertsFilter")
        self.type_combo.addItem("Tous les types", "")
        self.type_combo.addItem("Stock faible ou rupture", "STOCK_FAIBLE")
        self.type_combo.addItem("Expiration proche", "EXPIRATION_PROCHE")
        self.type_combo.addItem("Produit expiré", "PRODUIT_EXPIRE")
        self.type_combo.currentIndexChanged.connect(self._reset_and_load)
        self.status_combo = QComboBox()
        self.status_combo.setObjectName("alertsFilter")
        self.status_combo.addItem("Tous les états", None)
        self.status_combo.addItem("Non lues", 0)
        self.status_combo.addItem("Lues", 1)
        self.status_combo.currentIndexChanged.connect(self._reset_and_load)
        filters.addWidget(self.search_input, 1)
        filters.addWidget(self.type_combo)
        filters.addWidget(self.status_combo)
        root.addLayout(filters)

        metrics = QHBoxLayout()
        metrics.setSpacing(14)
        self.stock_card = _AlertMetric("Stock faible ou rupture", "warning", "orange", "Produits à surveiller")
        self.expiry_card = _AlertMetric("Expirations proches", "calendar", "yellow", "Lots bientôt expirés")
        self.expired_card = _AlertMetric("Produits expirés", "warning", "red", "Vente interdite")
        self.unread_card = _AlertMetric("Alertes non lues", "bell", "violet", "À consulter")
        for card in (self.stock_card, self.expiry_card, self.expired_card, self.unread_card):
            metrics.addWidget(card, 1)
        root.addLayout(metrics)

        self.content_grid = QGridLayout()
        self.content_grid.setSpacing(16)
        self.list_panel = self._build_list_panel()
        self.watch_panel = self._build_watch_panel()
        self.content_grid.addWidget(self.list_panel, 0, 0)
        self.content_grid.addWidget(self.watch_panel, 0, 1)
        self.content_grid.setColumnStretch(0, 4)
        self.content_grid.setColumnStretch(1, 1)
        root.addLayout(self.content_grid, 1)

    def _build_list_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("alertsListPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 12)
        title = QLabel("Liste des alertes")
        title.setObjectName("alertsPanelTitle")
        layout.addWidget(title)
        self.table = QTableWidget(0, 7)
        self.table.setObjectName("alertsTable")
        self.table.setHorizontalHeaderLabels(["Type", "Produit", "Lot", "Message", "Détectée le", "Statut", "Action"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.cellDoubleClicked.connect(self._ouvrir_produit)
        layout.addWidget(self.table, 1)
        footer = QHBoxLayout()
        self.page_label = QLabel("Aucune alerte")
        self.page_label.setObjectName("alertsFooter")
        self.previous_button = QPushButton("‹")
        self.next_button = QPushButton("›")
        for button in (self.previous_button, self.next_button):
            button.setObjectName("alertsPageButton")
        self.previous_button.clicked.connect(lambda: self._changer_page(-1))
        self.next_button.clicked.connect(lambda: self._changer_page(1))
        footer.addWidget(self.page_label)
        footer.addStretch(1)
        footer.addWidget(self.previous_button)
        footer.addWidget(self.next_button)
        layout.addLayout(footer)
        return panel

    def _build_watch_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("alertsWatchPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 14)
        title = QLabel("À surveiller")
        title.setObjectName("alertsPanelTitle")
        layout.addWidget(title)
        self.unread_summary = QLabel("0 alerte non lue")
        self.unread_summary.setObjectName("alertsWatchSummary")
        layout.addWidget(self.unread_summary)
        distribution = QLabel("Répartition active")
        distribution.setObjectName("alertsWatchHeading")
        layout.addWidget(distribution)
        self.distribution_label = QLabel()
        self.distribution_label.setObjectName("alertsDistribution")
        self.distribution_label.setWordWrap(True)
        layout.addWidget(self.distribution_label)
        recent = QLabel("Alertes récentes")
        recent.setObjectName("alertsWatchHeading")
        layout.addWidget(recent)
        self.recent_layout = QVBoxLayout()
        layout.addLayout(self.recent_layout)
        layout.addStretch(1)
        stock = QPushButton("Ouvrir le stock")
        stock.setObjectName("alertsSecondaryButton")
        stock.setIcon(ui_icon("stock", "#15933a", 16))
        stock.clicked.connect(lambda: self.navigation_demandee.emit("stock"))
        products = QPushButton("Ouvrir les produits")
        products.setObjectName("alertsPrimaryButton")
        products.setIcon(ui_icon("produits", "#ffffff", 16))
        products.clicked.connect(lambda: self.navigation_demandee.emit("produits"))
        layout.addWidget(stock)
        layout.addWidget(products)
        return panel

    def _reset_and_load(self) -> None:
        self._page = 0
        self._charger()

    def _charger(self) -> None:
        try:
            self._result = self._alerte_service.rechercher_alertes(
                self.session_utilisateur,
                terme=self.search_input.text(),
                type_alerte=str(self.type_combo.currentData() or ""),
                est_lue=self.status_combo.currentData(),
                limit=self._page_size,
                offset=self._page * self._page_size,
            )
        except SalmospharmError as exc:
            QMessageBox.warning(self, "SALMOSPHARM", str(exc))
            return
        result = self._result
        self.compteur_change.emit(result.synthese.non_lues)
        self.stock_card.set_value(result.synthese.stock_faible)
        self.expiry_card.set_value(result.synthese.expiration_proche)
        self.expired_card.set_value(result.synthese.produit_expire)
        self.unread_card.set_value(result.synthese.non_lues)
        self._remplir_table(result)
        self._remplir_surveillance(result)

    def _remplir_table(self, result: AlertePageResult) -> None:
        self.table.setRowCount(0)
        for alerte in result.alertes:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setRowHeight(row, 46)
            self.table.setCellWidget(row, 0, _badge(_type_label(alerte.type_alerte), _type_tone(alerte.type_alerte)))
            values = (
                alerte.produit.nom if alerte.produit else "Produit",
                (alerte.lot.numero_lot or "—") if alerte.lot else "—",
                alerte.message or "Alerte active",
                alerte.derniere_detection_le or alerte.cree_le,
            )
            for column, value in enumerate(values, start=1):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.ItemDataRole.UserRole, alerte.id)
                item.setData(Qt.ItemDataRole.UserRole + 1, alerte.produit_id)
                self.table.setItem(row, column, item)
            self.table.setCellWidget(row, 5, _badge("Lue" if alerte.est_lue else "Non lue", "green" if alerte.est_lue else "orange"))
            action = QPushButton("Marquer lue")
            action.setObjectName("alertsRowButton")
            action.setEnabled(alerte.est_lue == 0)
            action.clicked.connect(lambda checked=False, alert_id=alerte.id: self._marquer_lue(alert_id))
            self.table.setCellWidget(row, 6, action)
        total_pages = max(1, ceil(result.total / self._page_size))
        start = self._page * self._page_size + 1 if result.total else 0
        end = min(result.total, (self._page + 1) * self._page_size)
        self.page_label.setText(f"Affichage de {start} à {end} sur {result.total} alertes" if result.total else "Aucune alerte pour ces filtres")
        self.previous_button.setEnabled(self._page > 0)
        self.next_button.setEnabled(self._page + 1 < total_pages)

    def _remplir_surveillance(self, result: AlertePageResult) -> None:
        summary = result.synthese
        self.unread_summary.setText(f"{summary.non_lues} alerte(s) non lue(s)")
        self.distribution_label.setText(
            f"Stock : {summary.stock_faible}\nExpirations proches : {summary.expiration_proche}\nProduits expirés : {summary.produit_expire}"
        )
        _clear_layout(self.recent_layout)
        for alerte in result.alertes[:3]:
            label = QLabel(f"• {alerte.produit.nom if alerte.produit else 'Produit'}\n  {_type_label(alerte.type_alerte)}")
            label.setObjectName("alertsRecentItem")
            self.recent_layout.addWidget(label)
        if not result.alertes:
            label = QLabel("Aucune alerte récente.")
            label.setObjectName("alertsEmpty")
            self.recent_layout.addWidget(label)

    def _changer_page(self, delta: int) -> None:
        self._page = max(0, self._page + delta)
        self._charger()

    def _ouvrir_produit(self, row: int, _column: int) -> None:
        item = self.table.item(row, 1)
        if item and item.data(Qt.ItemDataRole.UserRole + 1) is not None:
            self.produit_demande.emit(int(item.data(Qt.ItemDataRole.UserRole + 1)))

    def _marquer_lue(self, alerte_id: int) -> None:
        try:
            self._alerte_service.marquer_lue(self.session_utilisateur, alerte_id=alerte_id)
            self._charger()
        except SalmospharmError as exc:
            QMessageBox.warning(self, "SALMOSPHARM", str(exc))

    def set_compact(self, compact: bool) -> None:
        self.content_grid.addWidget(self.watch_panel, 1 if compact else 0, 0 if compact else 1)
        self.content_grid.setColumnStretch(0, 1 if compact else 4)
        self.content_grid.setColumnStretch(1, 0 if compact else 1)


class _AlertMetric(QFrame):
    def __init__(self, title: str, icon: str, tone: str, subtitle: str) -> None:
        super().__init__()
        self.setObjectName("alertsMetricCard")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        bubble = QLabel()
        bubble.setObjectName(f"alertsMetricIcon_{tone}")
        bubble.setFixedSize(46, 46)
        bubble.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bubble.setPixmap(ui_icon(icon, "#ffffff", 21).pixmap(21, 21))
        text = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("alertsMetricTitle")
        self.value_label = QLabel("0")
        self.value_label.setObjectName("alertsMetricValue")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("alertsMetricSubtitle")
        text.addWidget(title_label)
        text.addWidget(self.value_label)
        text.addWidget(subtitle_label)
        layout.addWidget(bubble)
        layout.addLayout(text, 1)

    def set_value(self, value: int) -> None:
        self.value_label.setText(str(value))


def _badge(text: str, tone: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("alertsBadge")
    label.setProperty("tone", tone)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return label


def _type_label(value: str) -> str:
    return {"STOCK_FAIBLE": "Stock faible", "EXPIRATION_PROCHE": "Expiration proche", "PRODUIT_EXPIRE": "Produit expiré"}.get(value, value)


def _type_tone(value: str) -> str:
    return {"STOCK_FAIBLE": "orange", "EXPIRATION_PROCHE": "yellow", "PRODUIT_EXPIRE": "red"}.get(value, "blue")


def _clear_layout(layout: QVBoxLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget:
            widget.setParent(None)
            widget.deleteLater()
