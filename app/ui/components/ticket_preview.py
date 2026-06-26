"""Composant d'apercu facture/recu genere depuis une vente."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.exceptions import ImprimanteIndisponibleError, SalmospharmError
from app.services.auth_service import SessionUtilisateur
from app.services.impression_service import ImpressionService
from app.services.ticket_service import TicketDocument, TicketService
from app.ui.components.icons import ui_icon


class TicketPreviewPage(QWidget):
    """Page Facture/Recu sans table facture persistante."""

    retour_demande = Signal()

    def __init__(
        self,
        session_utilisateur: SessionUtilisateur,
        ticket_service: TicketService | None = None,
        impression_service: ImpressionService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("ticketPage")
        self.session_utilisateur = session_utilisateur
        self._ticket_service = ticket_service or TicketService()
        self._impression_service = impression_service or ImpressionService()
        self._ticket: TicketDocument | None = None
        self._build_ui()
        self._set_empty_state()

    def set_ticket(self, ticket: TicketDocument, message: str | None = None) -> None:
        self._ticket = ticket
        self._render_ticket(ticket)
        if message:
            self.notice_label.setText(message)
            self.notice_label.show()
        else:
            self.notice_label.hide()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        header = QVBoxLayout()
        header.setSpacing(6)
        title = QLabel("Facture / Recu")
        title.setObjectName("ticketPageTitle")
        breadcrumb = QLabel("Accueil > Factures > Facture / Recu")
        breadcrumb.setObjectName("ticketBreadcrumb")
        header.addWidget(title)
        header.addWidget(breadcrumb)
        layout.addLayout(header)

        self.notice_label = QLabel()
        self.notice_label.setObjectName("ticketNotice")
        self.notice_label.setWordWrap(True)
        layout.addWidget(self.notice_label)

        self.card = QFrame()
        self.card.setObjectName("ticketCard")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(16)

        top = QHBoxLayout()
        top.setSpacing(22)
        self.logo = QLabel()
        self.logo.setObjectName("ticketLogo")
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo.setFixedSize(210, 150)
        top.addWidget(self.logo)

        details = QVBoxLayout()
        details.setSpacing(6)
        self.pharmacy_label = QLabel()
        self.pharmacy_label.setObjectName("ticketPharmacy")
        self.address_label = QLabel()
        self.address_label.setObjectName("ticketMeta")
        self.phone_label = QLabel()
        self.phone_label.setObjectName("ticketMeta")
        details.addWidget(self.pharmacy_label)
        details.addWidget(self.address_label)
        details.addWidget(self.phone_label)
        details.addStretch(1)
        top.addLayout(details, 1)

        invoice_box = QFrame()
        invoice_box.setObjectName("invoiceBox")
        invoice_layout = QVBoxLayout(invoice_box)
        invoice_layout.setContentsMargins(18, 12, 18, 12)
        invoice_layout.setSpacing(8)
        invoice_title = QLabel("FACTURE / RECU")
        invoice_title.setObjectName("invoiceTitle")
        invoice_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.number_label = QLabel()
        self.number_label.setObjectName("invoiceNumber")
        self.number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.barcode_label = QLabel()
        self.barcode_label.setObjectName("ticketBarcode")
        self.barcode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label = QLabel()
        self.date_label.setObjectName("ticketMeta")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        invoice_layout.addWidget(invoice_title)
        invoice_layout.addWidget(self.number_label)
        invoice_layout.addWidget(self.barcode_label)
        invoice_layout.addWidget(self.date_label)
        top.addWidget(invoice_box)
        card_layout.addLayout(top)

        parties = QHBoxLayout()
        parties.setSpacing(22)
        self.client_box = _party_box("Client")
        self.vendor_box = _party_box("Vendeur")
        parties.addWidget(self.client_box, 1)
        parties.addWidget(self.vendor_box, 1)
        card_layout.addLayout(parties)

        self.lines_layout = QVBoxLayout()
        self.lines_layout.setSpacing(0)
        card_layout.addLayout(self.lines_layout)

        totals = QHBoxLayout()
        totals.addStretch(1)
        totals_card = QFrame()
        totals_card.setObjectName("ticketTotals")
        totals_layout = QVBoxLayout(totals_card)
        totals_layout.setContentsMargins(16, 10, 16, 10)
        totals_layout.setSpacing(8)
        self.subtotal_label = QLabel()
        self.received_label = QLabel()
        self.change_label = QLabel()
        self.total_label = QLabel()
        totals_layout.addLayout(_total_row("Sous-total", self.subtotal_label))
        totals_layout.addLayout(_total_row("Recu", self.received_label))
        totals_layout.addLayout(_total_row("Monnaie", self.change_label))
        totals_layout.addLayout(_total_row("TOTAL A PAYER", self.total_label, strong=True))
        totals.addWidget(totals_card, 0)
        card_layout.addLayout(totals)

        actions = QHBoxLayout()
        actions.setSpacing(28)
        self.print_button = QPushButton("Imprimer")
        self.print_button.setObjectName("outlineButton")
        self.print_button.setIcon(ui_icon("print", "#0b3567", 18))
        self.print_button.clicked.connect(self._imprimer)
        self.pdf_button = QPushButton("Telecharger (PDF)")
        self.pdf_button.setObjectName("outlineButton")
        self.pdf_button.setIcon(ui_icon("download", "#0b3567", 18))
        self.pdf_button.clicked.connect(self._exporter_pdf)
        self.close_button = QPushButton("Fermer")
        self.close_button.setObjectName("successButton")
        self.close_button.setIcon(ui_icon("close", "#0a7f31", 18))
        self.close_button.clicked.connect(self.retour_demande.emit)
        actions.addWidget(self.print_button)
        actions.addWidget(self.pdf_button)
        actions.addWidget(self.close_button)
        card_layout.addLayout(actions)

        layout.addWidget(self.card, 1)

    def _set_empty_state(self) -> None:
        self.notice_label.setText("Aucun ticket selectionne. Validez une vente pour afficher le recu.")
        self.notice_label.show()
        self.pharmacy_label.setText("SALMOSPHARM 133")
        self.address_label.setText("")
        self.phone_label.setText("")
        self.number_label.setText("En attente")
        self.barcode_label.setText("|||| |||| |||| ||||")
        self.date_label.setText("")
        self.logo.setText("SALMOSPHARM")
        for button in (self.print_button, self.pdf_button):
            button.setEnabled(False)
        self._clear_lines()

    def _render_ticket(self, ticket: TicketDocument) -> None:
        logo_path = Path(__file__).resolve().parents[2] / "assets" / "logo.png"
        pixmap = QPixmap(str(logo_path))
        if pixmap.isNull():
            self.logo.setText("SALMOSPHARM")
        else:
            self.logo.setPixmap(pixmap.scaled(190, 140, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.pharmacy_label.setText(ticket.nom_pharmacie)
        self.address_label.setText(ticket.adresse or "Adresse non configuree")
        self.phone_label.setText(ticket.telephone or "Telephone non configure")
        self.number_label.setText(ticket.numero_vente)
        self.barcode_label.setText(_fake_barcode(ticket.numero_vente))
        self.date_label.setText(f"Date : {ticket.date_vente}")
        self.client_box.value_label.setText(ticket.numero_vente)
        self.vendor_box.value_label.setText(ticket.vendeur_nom)
        self.vendor_box.sub_label.setText("Poste de vente")
        self._render_lines(ticket)
        self.subtotal_label.setText(_format_cdf(ticket.total))
        self.received_label.setText(_format_cdf(ticket.montant_recu))
        self.change_label.setText(_format_cdf(ticket.monnaie_rendue))
        self.total_label.setText(_format_cdf(ticket.total))
        for button in (self.print_button, self.pdf_button):
            button.setEnabled(True)

    def _render_lines(self, ticket: TicketDocument) -> None:
        self._clear_lines()
        header = QGridLayout()
        header.setColumnStretch(0, 0)
        header.setColumnStretch(1, 4)
        header.setColumnStretch(2, 1)
        header.setColumnStretch(3, 1)
        header.setColumnStretch(4, 1)
        for column, text in enumerate(("#", "Produit", "Quantite", "Prix unitaire (CDF)", "Total (CDF)")):
            label = QLabel(text)
            label.setObjectName("ticketTableHeader")
            header.addWidget(label, 0, column)
        self.lines_layout.addLayout(header)
        for index, line in enumerate(ticket.lignes, start=1):
            row = QGridLayout()
            row.setColumnStretch(0, 0)
            row.setColumnStretch(1, 4)
            row.setColumnStretch(2, 1)
            row.setColumnStretch(3, 1)
            row.setColumnStretch(4, 1)
            values = (str(index), line.produit_nom, str(line.quantite), _format_number(line.prix_unitaire), _format_number(line.sous_total))
            for column, text in enumerate(values):
                label = QLabel(text)
                label.setObjectName("ticketTableCell")
                row.addWidget(label, 0, column)
            self.lines_layout.addLayout(row)

    def _clear_lines(self) -> None:
        while self.lines_layout.count():
            item = self.lines_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
            nested = item.layout()
            if nested is not None:
                _clear_layout(nested)

    def _imprimer(self) -> None:
        if self._ticket is None:
            return
        try:
            self._impression_service.imprimer_ticket(self._ticket)
            self._ticket_service.journaliser_impression(self.session_utilisateur, self._ticket)
            QMessageBox.information(self, "SALMOSPHARM", "Ticket envoye a l'imprimante.")
        except ImprimanteIndisponibleError as exc:
            self._ticket_service.journaliser_erreur_impression(self.session_utilisateur, self._ticket, str(exc))
            QMessageBox.warning(self, "SALMOSPHARM", str(exc))
        except SalmospharmError as exc:
            QMessageBox.warning(self, "SALMOSPHARM", str(exc))

    def _exporter_pdf(self) -> None:
        if self._ticket is None:
            return
        default_name = f"{self._ticket.numero_vente}.pdf"
        path, _ = QFileDialog.getSaveFileName(self, "Telecharger le ticket PDF", default_name, "PDF (*.pdf)")
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path = f"{path}.pdf"
        try:
            self._ticket_service.exporter_pdf(self._ticket, path)
            QMessageBox.information(self, "SALMOSPHARM", "PDF genere avec succes.")
        except SalmospharmError as exc:
            QMessageBox.warning(self, "SALMOSPHARM", str(exc))


class _PartyBox(QFrame):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.setObjectName("ticketPartyBox")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        label = QLabel(title)
        label.setObjectName("ticketPartyTitle")
        self.value_label = QLabel("")
        self.value_label.setObjectName("ticketPartyValue")
        self.sub_label = QLabel("")
        self.sub_label.setObjectName("ticketPartySub")
        layout.addWidget(label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.sub_label)


def _party_box(title: str) -> _PartyBox:
    return _PartyBox(title)


def _total_row(label_text: str, value_label: QLabel, *, strong: bool = False) -> QHBoxLayout:
    row = QHBoxLayout()
    label = QLabel(label_text)
    label.setObjectName("ticketTotalLabelStrong" if strong else "ticketTotalLabel")
    value_label.setObjectName("ticketTotalValueStrong" if strong else "ticketTotalValue")
    row.addWidget(label)
    row.addStretch(1)
    row.addWidget(value_label)
    return row


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


def _fake_barcode(value: str) -> str:
    pattern = []
    for char in value[-16:]:
        pattern.append("||" if ord(char) % 2 == 0 else "|")
    return " ".join(pattern)


def _format_number(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def _format_cdf(value: int) -> str:
    return f"{_format_number(value)} CDF"
