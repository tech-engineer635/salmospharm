"""Ecran Factures : historique des ventes et apercu du ticket selectionne."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
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

from app.core.exceptions import ImprimanteIndisponibleError, SalmospharmError
from app.services.auth_service import SessionUtilisateur
from app.services.impression_service import ImpressionService
from app.services.rapport_service import RapportService, VenteHistoriqueItem
from app.services.ticket_service import TicketDocument, TicketService
from app.ui.components.icons import ui_icon


class TicketPreviewPage(QWidget):
    """Consulte les factures derivees des ventes, sans table facture."""

    retour_demande = Signal()

    def __init__(
        self,
        session_utilisateur: SessionUtilisateur,
        ticket_service: TicketService | None = None,
        impression_service: ImpressionService | None = None,
        rapport_service: RapportService | None = None,
        autoload: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("ticketPage")
        self.session_utilisateur = session_utilisateur
        self._ticket_service = ticket_service or TicketService()
        self._impression_service = impression_service or ImpressionService()
        self._rapport_service = rapport_service or RapportService()
        self._ticket: TicketDocument | None = None
        self._ventes: list[VenteHistoriqueItem] = []
        self._build_ui()
        self._set_empty_state()
        if autoload:
            self.on_show()

    def on_show(self) -> None:
        self._charger_factures()

    def set_ticket(self, ticket: TicketDocument, message: str | None = None) -> None:
        self._ticket = ticket
        self._render_ticket(ticket)
        self.notice_label.setText(message or "")
        self.notice_label.setVisible(bool(message))

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(18)

        self.notice_label = QLabel()
        self.notice_label.setObjectName("ticketNotice")
        root.addWidget(self.notice_label)

        metrics = QHBoxLayout()
        metrics.setSpacing(16)
        self.count_metric = _MetricCard("receipt", "#16a33a", "Factures du jour", "0", "↗ activité du jour")
        self.total_metric = _MetricCard("money", "#2469c8", "Montant total encaissé", "0 CDF", "↗ ventes validées")
        self.printed_metric = _MetricCard("print", "#16a33a", "Factures disponibles", "0", "Tickets générables")
        self.pending_metric = _MetricCard("history", "#ff810a", "En attente", "0", "Impression non bloquante")
        for card in (self.count_metric, self.total_metric, self.printed_metric, self.pending_metric):
            metrics.addWidget(card, 1)
        root.addLayout(metrics)

        content = QHBoxLayout()
        content.setSpacing(20)
        content.addWidget(self._build_list_panel(), 49)
        content.addWidget(self._build_preview_panel(), 51)
        root.addLayout(content, 1)

    def _build_list_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("invoiceListPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(18, 14, 18, 14)
        self.search_input = QLineEdit()
        self.search_input.setObjectName("invoiceListSearch")
        self.search_input.setPlaceholderText("Rechercher une facture...")
        self.search_input.addAction(ui_icon("search", "#173b68", 17), QLineEdit.ActionPosition.TrailingPosition)
        self.search_input.textChanged.connect(self._charger_factures)
        filter_button = QPushButton("Filtres")
        filter_button.setObjectName("invoiceFilterButton")
        filter_button.setIcon(ui_icon("filter", "#173b68", 16))
        toolbar.addWidget(self.search_input, 1)
        toolbar.addWidget(filter_button)
        layout.addLayout(toolbar)

        self.table = QTableWidget(0, 5)
        self.table.setObjectName("invoiceListTable")
        self.table.setHorizontalHeaderLabels(["N° Facture", "Date", "Vendeur", "Montant (CDF)", "Statut"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self._ouvrir_selection)
        layout.addWidget(self.table, 1)

        footer = QHBoxLayout()
        footer.setContentsMargins(18, 10, 18, 12)
        self.footer_label = QLabel("Affichage de 0 facture")
        self.footer_label.setObjectName("invoiceFooter")
        footer.addWidget(self.footer_label)
        footer.addStretch(1)
        for label in ("‹", "1", "2", "3", "…", "›"):
            button = QPushButton(label)
            button.setObjectName("invoicePageActive" if label == "1" else "invoicePageButton")
            footer.addWidget(button)
        layout.addLayout(footer)
        return panel

    def _build_preview_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("invoicePreviewPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(14)
        top = QHBoxLayout()
        title = QLabel("Aperçu de la facture")
        title.setObjectName("invoicePreviewTitle")
        self.status_badge = QLabel("●  Imprimée")
        self.status_badge.setObjectName("invoiceStatusBadge")
        more = QPushButton("⋮")
        more.setObjectName("invoiceMoreButton")
        top.addWidget(title)
        top.addWidget(self.status_badge)
        top.addStretch(1)
        top.addWidget(more)
        layout.addLayout(top)

        invoice_head = QHBoxLayout()
        left = QVBoxLayout()
        self.invoice_word = QLabel("FACTURE")
        self.invoice_word.setObjectName("invoiceWord")
        self.date_label = QLabel("")
        self.date_label.setObjectName("ticketMeta")
        left.addWidget(self.invoice_word)
        left.addWidget(self.date_label)
        self.number_label = QLabel("N° —")
        self.number_label.setObjectName("invoiceNumber")
        invoice_head.addLayout(left)
        invoice_head.addStretch(1)
        invoice_head.addWidget(self.number_label, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(invoice_head)

        parties = QFrame()
        parties.setObjectName("invoiceParties")
        parties_layout = QHBoxLayout(parties)
        parties_layout.setContentsMargins(16, 12, 16, 12)
        self.vendor_box = _PartyBox("Vendeur", "user")
        self.client_box = _PartyBox("Client", "users")
        parties_layout.addWidget(self.vendor_box, 1)
        parties_layout.addWidget(self.client_box, 1)
        layout.addWidget(parties)

        self.lines_table = QTableWidget(0, 4)
        self.lines_table.setObjectName("invoiceLinesTable")
        self.lines_table.setHorizontalHeaderLabels(["Article", "Qté", "Prix unitaire", "Total (CDF)"])
        self.lines_table.verticalHeader().setVisible(False)
        self.lines_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.lines_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.lines_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in (1, 2, 3):
            self.lines_table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.lines_table, 1)

        totals = QGridLayout()
        self.subtotal_label = QLabel("0")
        self.received_label = QLabel("0")
        self.change_label = QLabel("0")
        self.total_label = QLabel("0 CDF")
        rows = (("Sous-total", self.subtotal_label), ("Montant reçu", self.received_label), ("Monnaie rendue", self.change_label), ("Total à payer", self.total_label))
        for row, (text, value) in enumerate(rows):
            name = QLabel(text)
            name.setObjectName("invoiceGrandTotal" if row == 3 else "invoiceTotalLabel")
            value.setObjectName("invoiceGrandTotal" if row == 3 else "invoiceTotalValue")
            totals.addWidget(name, row, 1)
            totals.addWidget(value, row, 2, Qt.AlignmentFlag.AlignRight)
        totals.setColumnStretch(0, 1)
        layout.addLayout(totals)

        actions = QHBoxLayout()
        actions.setSpacing(18)
        self.print_button = QPushButton("Imprimer")
        self.print_button.setObjectName("invoicePrintButton")
        self.print_button.setIcon(ui_icon("print", "#1254a0", 18))
        self.print_button.clicked.connect(self._imprimer)
        self.pdf_button = QPushButton("Télécharger")
        self.pdf_button.setObjectName("invoiceDownloadButton")
        self.pdf_button.setIcon(ui_icon("download", "#ffffff", 18))
        self.pdf_button.clicked.connect(self._exporter_pdf)
        actions.addWidget(self.print_button, 1)
        actions.addWidget(self.pdf_button, 1)
        layout.addLayout(actions)
        return panel

    def _charger_factures(self) -> None:
        terme = self.search_input.text() if hasattr(self, "search_input") else ""
        try:
            self._ventes = self._rapport_service.lister_ventes(
                self.session_utilisateur, terme=terme, limit=100
            )
        except SalmospharmError as exc:
            QMessageBox.warning(self, "SALMOSPHARM", str(exc))
            return
        self.table.setRowCount(0)
        total = 0
        for vente in self._ventes:
            row = self.table.rowCount()
            self.table.insertRow(row)
            total += vente.total
            values = (vente.numero_vente, vente.date_vente, vente.vendeur_nom, _format_number(vente.total), "Imprimée")
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, vente.vente_id)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | (Qt.AlignmentFlag.AlignRight if column == 3 else Qt.AlignmentFlag.AlignLeft))
                self.table.setItem(row, column, item)
            self.table.setRowHeight(row, 44)
        self.footer_label.setText(f"Affichage de 1 à {len(self._ventes)} sur {len(self._ventes)} factures" if self._ventes else "Aucune facture")
        today_count = sum(1 for item in self._ventes if item.date_vente.startswith(date.today().strftime("%d/%m/%Y")))
        self.count_metric.set_value(str(today_count))
        self.total_metric.set_value(f"{_format_number(total)} CDF")
        self.printed_metric.set_value(str(len(self._ventes)))
        self.pending_metric.set_value("0")
        if self._ventes and self._ticket is None:
            self.table.selectRow(0)

    def _ouvrir_selection(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        vente_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        try:
            self.set_ticket(self._ticket_service.generer_ticket(self.session_utilisateur, vente_id))
        except SalmospharmError as exc:
            QMessageBox.warning(self, "SALMOSPHARM", str(exc))

    def _set_empty_state(self) -> None:
        self.notice_label.hide()
        self.number_label.setText("N° —")
        self.date_label.setText("Sélectionnez une facture dans la liste.")
        self.vendor_box.value_label.setText("—")
        self.client_box.value_label.setText("Client comptoir")
        self.lines_table.setRowCount(0)
        for button in (self.print_button, self.pdf_button):
            button.setEnabled(False)

    def _render_ticket(self, ticket: TicketDocument) -> None:
        self.number_label.setText(f"N° {ticket.numero_vente}")
        self.date_label.setText(f"Date : {ticket.date_vente}")
        self.vendor_box.value_label.setText(ticket.vendeur_nom)
        self.vendor_box.sub_label.setText("Poste de vente")
        self.client_box.value_label.setText("Client comptoir")
        self.client_box.sub_label.setText(ticket.telephone or "")
        self.lines_table.setRowCount(0)
        for line in ticket.lignes:
            row = self.lines_table.rowCount()
            self.lines_table.insertRow(row)
            for column, value in enumerate((line.produit_nom, str(line.quantite), _format_number(line.prix_unitaire), _format_number(line.sous_total))):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | (Qt.AlignmentFlag.AlignRight if column else Qt.AlignmentFlag.AlignLeft))
                self.lines_table.setItem(row, column, item)
            self.lines_table.setRowHeight(row, 34)
        self.subtotal_label.setText(_format_number(ticket.total))
        self.received_label.setText(_format_number(ticket.montant_recu))
        self.change_label.setText(_format_number(ticket.monnaie_rendue))
        self.total_label.setText(_format_cdf(ticket.total))
        for button in (self.print_button, self.pdf_button):
            button.setEnabled(True)

    def _imprimer(self) -> None:
        if self._ticket is None:
            return
        try:
            self._impression_service.imprimer_ticket(self._ticket)
            self._ticket_service.journaliser_impression(self.session_utilisateur, self._ticket)
            QMessageBox.information(self, "SALMOSPHARM", "Ticket envoyé à l'imprimante.")
        except ImprimanteIndisponibleError as exc:
            self._ticket_service.journaliser_erreur_impression(self.session_utilisateur, self._ticket, str(exc))
            QMessageBox.warning(self, "SALMOSPHARM", str(exc))
        except SalmospharmError as exc:
            QMessageBox.warning(self, "SALMOSPHARM", str(exc))

    def _exporter_pdf(self) -> None:
        if self._ticket is None:
            return
        destination, _ = QFileDialog.getSaveFileName(self, "Télécharger la facture PDF", f"{self._ticket.numero_vente}.pdf", "PDF (*.pdf)")
        if not destination:
            return
        try:
            self._ticket_service.exporter_pdf(self._ticket, destination if destination.lower().endswith(".pdf") else f"{destination}.pdf")
            QMessageBox.information(self, "SALMOSPHARM", "PDF généré avec succès.")
        except SalmospharmError as exc:
            QMessageBox.warning(self, "SALMOSPHARM", str(exc))


class _MetricCard(QFrame):
    def __init__(self, icon: str, color: str, title: str, value: str, trend: str) -> None:
        super().__init__()
        self.setObjectName("invoiceMetricCard")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        icon_label = QLabel()
        icon_label.setObjectName("invoiceMetricIcon")
        icon_label.setPixmap(ui_icon(icon, "#ffffff", 20).pixmap(20, 20))
        icon_label.setStyleSheet(f"background-color: {color};")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text = QVBoxLayout()
        label = QLabel(title)
        label.setObjectName("invoiceMetricTitle")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("invoiceMetricValue")
        trend_label = QLabel(trend)
        trend_label.setObjectName("invoiceMetricTrend")
        text.addWidget(label)
        text.addWidget(self.value_label)
        text.addWidget(trend_label)
        layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(text, 1)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class _PartyBox(QWidget):
    def __init__(self, title: str, icon: str) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        title_label = QLabel(title)
        title_label.setObjectName("ticketPartyTitle")
        identity = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setObjectName("invoicePartyIcon")
        icon_label.setPixmap(ui_icon(icon, "#173b68", 17).pixmap(17, 17))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label = QLabel()
        self.value_label.setObjectName("ticketPartyValue")
        self.sub_label = QLabel()
        self.sub_label.setObjectName("ticketPartySub")
        identity.addWidget(icon_label)
        identity.addWidget(self.value_label, 1)
        layout.addWidget(title_label)
        layout.addLayout(identity)
        layout.addWidget(self.sub_label)


def _format_number(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def _format_cdf(value: int) -> str:
    return f"{_format_number(value)} CDF"
