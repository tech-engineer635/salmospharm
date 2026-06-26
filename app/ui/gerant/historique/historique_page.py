"""Historique complet des ventes pour le gerant."""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.core.exceptions import SalmospharmError
from app.services.auth_service import SessionUtilisateur
from app.services.rapport_service import RapportService, VenteHistoriqueItem
from app.services.ticket_service import TicketService
from app.ui.components.icons import ui_icon


class HistoriqueVentesGerantPage(QWidget):
    """Liste toutes les ventes validees, sans annulation ni modification."""

    ticket_demande = Signal(object, str)

    def __init__(
        self,
        session_utilisateur: SessionUtilisateur,
        rapport_service: RapportService | None = None,
        ticket_service: TicketService | None = None,
        autoload: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("historyPage")
        self.session_utilisateur = session_utilisateur
        self._rapport_service = rapport_service or RapportService()
        self._ticket_service = ticket_service or TicketService()
        self._ventes: list[VenteHistoriqueItem] = []
        self._build_ui()
        if autoload:
            self.on_show()

    def on_show(self) -> None:
        self._charger()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        header = QHBoxLayout()
        text = QVBoxLayout()
        title = QLabel("Historique des ventes")
        title.setObjectName("reportsTitle")
        subtitle = QLabel("Consultez toutes les ventes validees et ouvrez les recus associes.")
        subtitle.setObjectName("reportsSubtitle")
        text.addWidget(title)
        text.addWidget(subtitle)
        self.search_input = QLineEdit()
        self.search_input.setObjectName("reportsSearch")
        self.search_input.setPlaceholderText("Rechercher numero ou vendeur...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.addAction(ui_icon("search", "#506b92", 18), QLineEdit.ActionPosition.LeadingPosition)
        self.search_input.textChanged.connect(self._charger)
        self.start_input = QLineEdit()
        self.start_input.setObjectName("dateFilterInput")
        self.start_input.setPlaceholderText("Debut AAAA-MM-JJ")
        self.start_input.editingFinished.connect(self._charger)
        self.end_input = QLineEdit()
        self.end_input.setObjectName("dateFilterInput")
        self.end_input.setPlaceholderText("Fin AAAA-MM-JJ")
        self.end_input.editingFinished.connect(self._charger)
        header.addLayout(text, 1)
        header.addWidget(self.search_input)
        header.addWidget(self.start_input)
        header.addWidget(self.end_input)
        layout.addLayout(header)

        panel = QFrame()
        panel.setObjectName("reportsPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)
        panel_title = QLabel("Ventes validees")
        panel_title.setObjectName("reportsPanelTitle")
        panel_title.setContentsMargins(18, 16, 18, 12)
        panel_layout.addWidget(panel_title)
        self.table = QTableWidget(0, 7)
        self.table.setObjectName("reportsTable")
        self.table.setHorizontalHeaderLabels(["Numero", "Date", "Vendeur", "Articles", "Total", "Recu", "Ticket"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setMinimumHeight(470)
        panel_layout.addWidget(self.table)
        layout.addWidget(panel, 1)

    def _charger(self) -> None:
        try:
            self._ventes = self._rapport_service.lister_ventes(
                self.session_utilisateur,
                terme=self.search_input.text(),
                date_debut=_parse_date(self.start_input.text()),
                date_fin=_parse_date(self.end_input.text()),
            )
            self._remplir()
        except (SalmospharmError, ValueError) as exc:
            QMessageBox.warning(self, "SALMOSPHARM", str(exc))

    def _remplir(self) -> None:
        self.table.setRowCount(0)
        for vente in self._ventes:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                vente.numero_vente,
                vente.date_vente,
                vente.vendeur_nom,
                str(vente.articles),
                _format_cdf(vente.total),
                _format_cdf(vente.montant_recu),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, vente.vente_id)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | (Qt.AlignmentFlag.AlignRight if column in {3, 4, 5} else Qt.AlignmentFlag.AlignLeft))
                self.table.setItem(row, column, item)
            button = QPushButton("Ouvrir")
            button.setObjectName("outlineButton")
            button.setIcon(ui_icon("ticket", "#0b3567", 16))
            button.clicked.connect(lambda checked=False, vente_id=vente.vente_id: self._ouvrir_ticket(vente_id))
            self.table.setCellWidget(row, 6, button)

    def _ouvrir_ticket(self, vente_id: int) -> None:
        try:
            ticket = self._ticket_service.generer_ticket(self.session_utilisateur, vente_id)
            self.ticket_demande.emit(ticket, f"Ticket {ticket.numero_vente} pret pour reimpression.")
        except SalmospharmError as exc:
            QMessageBox.warning(self, "SALMOSPHARM", str(exc))


def _format_cdf(value: int) -> str:
    return f"{value:,}".replace(",", " ") + " CDF"


def _parse_date(value: str) -> date | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    try:
        return date.fromisoformat(cleaned)
    except ValueError as exc:
        raise ValueError("Le filtre date doit respecter le format AAAA-MM-JJ.") from exc
