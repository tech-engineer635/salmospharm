"""Generation des tickets depuis les ventes validees."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from textwrap import shorten

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.core.constants import ACTION_ERREUR_IMPRESSION, ACTION_FACTURE_IMPRIMEE, ACTION_FACTURE_REIMPRIMEE, ROLE_GERANT
from app.core.exceptions import PermissionRefuseeError, ValidationError
from app.core.permissions import PERMISSION_CREER_VENTE, exiger_permission
from app.database.connection import create_session
from app.repositories.parametre_repository import ParametreRepository
from app.repositories.vente_repository import VenteRepository
from app.services.auth_service import SessionUtilisateur
from app.services.journal_service import JournalService


@dataclass(frozen=True)
class TicketLine:
    """Ligne affichee sur le ticket, derivee de `lignes_vente`."""

    produit_nom: str
    quantite: int
    prix_unitaire: int
    sous_total: int


@dataclass(frozen=True)
class TicketDocument:
    """Document ticket/recu pret pour apercu, PDF ou impression."""

    vente_id: int
    numero_vente: str
    date_vente: str
    vendeur_id: int | None
    vendeur_nom: str
    nom_pharmacie: str
    telephone: str | None
    adresse: str | None
    devise: str
    largeur_ticket: int
    impression_auto: bool
    nom_imprimante: str | None
    lignes: list[TicketLine]
    total: int
    montant_recu: int
    monnaie_rendue: int


class TicketService:
    """Produit les tickets sans creer de table facture."""

    def __init__(
        self,
        session_factory=create_session,
        vente_repository: VenteRepository | None = None,
        parametre_repository: ParametreRepository | None = None,
        journal_service: JournalService | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._vente_repository = vente_repository or VenteRepository()
        self._parametre_repository = parametre_repository or ParametreRepository()
        self._journal_service = journal_service or JournalService()

    def generer_ticket(self, utilisateur: SessionUtilisateur, vente_id: int) -> TicketDocument:
        """Genere un apercu de ticket depuis une vente deja validee."""
        exiger_permission(utilisateur.role, PERMISSION_CREER_VENTE)
        with self._session_factory() as session:
            vente = self._vente_repository.chercher_detail_par_id(session, vente_id)
            if vente is None:
                raise ValidationError("Vente introuvable.")
            if utilisateur.role != ROLE_GERANT and vente.vendeur_id != utilisateur.utilisateur_id:
                raise PermissionRefuseeError("Vous ne pouvez consulter que vos propres tickets.")

            parametres = self._parametre_repository.obtenir_principal(session)
            nom_pharmacie = parametres.nom_pharmacie if parametres is not None else "SALMOSPHARM 133"
            devise = parametres.devise if parametres is not None else "CDF"
            if devise != "CDF":
                raise ValidationError("La devise configuree est invalide.")

            lignes = [
                TicketLine(
                    produit_nom=ligne.produit.nom if ligne.produit is not None else "Produit",
                    quantite=ligne.quantite,
                    prix_unitaire=ligne.prix_unitaire,
                    sous_total=ligne.sous_total,
                )
                for ligne in sorted(vente.lignes, key=lambda item: item.id)
            ]
            if not lignes:
                raise ValidationError("Cette vente ne contient aucune ligne.")

            return TicketDocument(
                vente_id=vente.id,
                numero_vente=vente.numero_vente,
                date_vente=_format_datetime(vente.cree_le),
                vendeur_id=vente.vendeur_id,
                vendeur_nom=vente.vendeur.nom if vente.vendeur is not None else "Vendeur",
                nom_pharmacie=nom_pharmacie,
                telephone=parametres.telephone if parametres is not None else None,
                adresse=parametres.adresse if parametres is not None else None,
                devise=devise,
                largeur_ticket=parametres.largeur_ticket if parametres is not None else 80,
                impression_auto=bool(parametres.impression_auto) if parametres is not None else False,
                nom_imprimante=parametres.nom_imprimante if parametres is not None else None,
                lignes=lignes,
                total=vente.total,
                montant_recu=vente.montant_recu,
                monnaie_rendue=vente.montant_recu - vente.total,
            )

    def exporter_pdf(self, ticket: TicketDocument, destination: str | Path) -> Path:
        """Exporte le ticket en PDF local avec ReportLab."""
        output = Path(destination)
        doc = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        rows = [["Produit", "Quantite", "Prix unitaire", "Total"]]
        rows.extend(
            [
                [line.produit_nom, str(line.quantite), _format_cdf(line.prix_unitaire), _format_cdf(line.sous_total)]
                for line in ticket.lignes
            ]
        )
        table = Table(rows, colWidths=[230, 70, 100, 100])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#064f8e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d8e2ec")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fbff")]),
                ]
            )
        )
        story = [
            Paragraph(ticket.nom_pharmacie, styles["Title"]),
            Paragraph(f"Facture / Recu : {ticket.numero_vente}", styles["Heading2"]),
            Paragraph(f"Date : {ticket.date_vente}", styles["Normal"]),
            Paragraph(f"Vendeur : {ticket.vendeur_nom}", styles["Normal"]),
            Spacer(1, 18),
            table,
            Spacer(1, 18),
            Paragraph(f"Total : {_format_cdf(ticket.total)}", styles["Heading2"]),
            Paragraph(f"Recu : {_format_cdf(ticket.montant_recu)}", styles["Normal"]),
            Paragraph(f"Monnaie : {_format_cdf(ticket.monnaie_rendue)}", styles["Normal"]),
            Paragraph("Paiement : Especes", styles["Normal"]),
        ]
        doc.build(story)
        return output

    def journaliser_impression(
        self,
        utilisateur: SessionUtilisateur,
        ticket: TicketDocument,
        *,
        reimpression: bool = False,
    ) -> None:
        action = ACTION_FACTURE_REIMPRIMEE if reimpression else ACTION_FACTURE_IMPRIMEE
        details = f"Ticket {ticket.numero_vente} {'reimprime' if reimpression else 'imprime'}."
        self._journaliser_ticket(utilisateur, ticket, action=action, details=details)

    def journaliser_erreur_impression(self, utilisateur: SessionUtilisateur, ticket: TicketDocument, message: str) -> None:
        self._journaliser_ticket(
            utilisateur,
            ticket,
            action=ACTION_ERREUR_IMPRESSION,
            details=f"Erreur impression ticket {ticket.numero_vente}: {shorten(message, width=180, placeholder='...')}",
        )

    def _journaliser_ticket(self, utilisateur: SessionUtilisateur, ticket: TicketDocument, *, action: str, details: str) -> None:
        with self._session_factory() as session:
            self._journal_service.journaliser(
                session,
                action=action,
                utilisateur_id=utilisateur.utilisateur_id,
                table_cible="ventes",
                element_id=ticket.vente_id,
                details=details,
            )
            session.commit()


def _format_datetime(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return value


def _format_number(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def _format_cdf(value: int) -> str:
    return f"{_format_number(value)} CDF"
