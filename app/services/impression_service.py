"""Impression thermique Windows des tickets."""

from __future__ import annotations

from collections.abc import Callable

from app.core.exceptions import ImprimanteIndisponibleError
from app.services.ticket_service import TicketDocument


PrinterWriter = Callable[[str, bytes], None]


class ImpressionService:
    """Envoie un ticket texte a une imprimante Windows configurable."""

    def __init__(self, printer_writer: PrinterWriter | None = None) -> None:
        self._printer_writer = printer_writer

    def imprimer_ticket(self, ticket: TicketDocument) -> None:
        """Imprime le ticket, ou leve une erreur propre sans toucher a la vente."""
        if not ticket.nom_imprimante:
            raise ImprimanteIndisponibleError("Aucune imprimante n'est configuree.")
        data = self.formater_ticket(ticket).encode("cp850", errors="replace")
        writer = self._printer_writer or _write_windows_printer
        try:
            writer(ticket.nom_imprimante, data)
        except ImprimanteIndisponibleError:
            raise
        except Exception as exc:  # pragma: no cover - depend de Windows et du pilote
            raise ImprimanteIndisponibleError("Impossible d'imprimer le ticket. Verifiez l'imprimante.") from exc

    def formater_ticket(self, ticket: TicketDocument) -> str:
        width = 32 if ticket.largeur_ticket == 58 else 42
        separator = "=" * width
        thin = "-" * width
        lines = [
            separator,
            ticket.nom_pharmacie.center(width),
        ]
        if ticket.adresse:
            lines.append(_clip(ticket.adresse, width).center(width))
        if ticket.telephone:
            lines.append(_clip(ticket.telephone, width).center(width))
        lines.extend(
            [
                separator,
                f"Facture : {ticket.numero_vente}",
                f"Date    : {ticket.date_vente}",
                f"Vendeur : {ticket.vendeur_nom}",
                thin,
            ]
        )
        for item in ticket.lignes:
            lines.append(_clip(item.produit_nom, width))
            lines.append(f"{item.quantite} x {_format_number(item.prix_unitaire)} = {_format_cdf(item.sous_total)}")
        lines.extend(
            [
                thin,
                _pair("TOTAL", _format_cdf(ticket.total), width),
                _pair("Recu", _format_cdf(ticket.montant_recu), width),
                _pair("Monnaie", _format_cdf(ticket.monnaie_rendue), width),
                "Paiement : Especes",
                thin,
                "Merci de votre visite".center(width),
                separator,
                "",
                "",
            ]
        )
        return "\n".join(lines)


def _write_windows_printer(printer_name: str, data: bytes) -> None:  # pragma: no cover - integration Windows
    try:
        import win32print
    except ImportError as exc:
        raise ImprimanteIndisponibleError("Le module d'impression Windows est indisponible.") from exc

    handle = None
    try:
        handle = win32print.OpenPrinter(printer_name)
        job = win32print.StartDocPrinter(handle, 1, ("SALMOSPHARM Ticket", None, "RAW"))
        win32print.StartPagePrinter(handle)
        win32print.WritePrinter(handle, data)
        win32print.EndPagePrinter(handle)
        win32print.EndDocPrinter(handle)
    except Exception as exc:
        raise ImprimanteIndisponibleError("Impossible d'imprimer le ticket. Verifiez l'imprimante.") from exc
    finally:
        if handle is not None:
            win32print.ClosePrinter(handle)


def _pair(label: str, value: str, width: int) -> str:
    left = f"{label} :"
    spacing = max(1, width - len(left) - len(value))
    return f"{left}{' ' * spacing}{value}"


def _clip(value: str, width: int) -> str:
    return value if len(value) <= width else value[: width - 1] + "."


def _format_number(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def _format_cdf(value: int) -> str:
    return f"{_format_number(value)} CDF"
