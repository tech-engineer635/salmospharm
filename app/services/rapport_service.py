"""Rapports et historiques calcules depuis les ventes validees."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, or_, select

from app.core.constants import ROLE_GERANT
from app.core.permissions import (
    PERMISSION_CONSULTER_HISTORIQUE_PERSONNEL,
    PERMISSION_CONSULTER_HISTORIQUE_SYSTEME,
    PERMISSION_CONSULTER_RAPPORTS_GLOBAUX,
    PERMISSION_CONSULTER_TOUTES_VENTES,
    exiger_permission,
)
from app.database.connection import create_session
from app.database.models import JournalActivite, LigneVente, Produit, Utilisateur, Vente
from app.services.auth_service import SessionUtilisateur


@dataclass(frozen=True)
class VenteHistoriqueItem:
    vente_id: int
    numero_vente: str
    vendeur_id: int | None
    vendeur_nom: str
    date_vente: str
    total: int
    montant_recu: int
    monnaie_rendue: int
    articles: int


@dataclass(frozen=True)
class RapportVendeurItem:
    vendeur_id: int | None
    vendeur_nom: str
    ventes: int
    total: int


@dataclass(frozen=True)
class ProduitVenduItem:
    produit_id: int
    produit_nom: str
    quantite: int
    total: int


@dataclass(frozen=True)
class RapportSynthese:
    ventes_jour: int
    total_jour: int
    ventes_mois: int
    total_mois: int
    panier_moyen: int
    vendeurs: list[RapportVendeurItem]
    produits: list[ProduitVenduItem]


@dataclass(frozen=True)
class JournalActionItem:
    journal_id: int
    date_action: str
    utilisateur_nom: str
    action: str
    details: str
    module: str


class RapportService:
    """Calcule les rapports sans table `rapports` persistante."""

    def __init__(self, session_factory=create_session) -> None:
        self._session_factory = session_factory

    def lister_ventes(
        self,
        utilisateur: SessionUtilisateur,
        *,
        terme: str = "",
        date_debut: date | None = None,
        date_fin: date | None = None,
        limit: int = 100,
    ) -> list[VenteHistoriqueItem]:
        """Retourne l'historique autorise : tout pour gerant, personnel pour vendeur."""
        if utilisateur.role == ROLE_GERANT:
            exiger_permission(utilisateur.role, PERMISSION_CONSULTER_TOUTES_VENTES)
        else:
            exiger_permission(utilisateur.role, PERMISSION_CONSULTER_HISTORIQUE_PERSONNEL)

        with self._session_factory() as session:
            statement = (
                select(
                    Vente.id,
                    Vente.numero_vente,
                    Vente.vendeur_id,
                    func.coalesce(Utilisateur.nom, "Vendeur"),
                    Vente.cree_le,
                    Vente.total,
                    Vente.montant_recu,
                    func.coalesce(func.sum(LigneVente.quantite), 0),
                )
                .select_from(Vente)
                .outerjoin(Utilisateur, Utilisateur.id == Vente.vendeur_id)
                .outerjoin(LigneVente, LigneVente.vente_id == Vente.id)
                .group_by(Vente.id, Vente.numero_vente, Vente.vendeur_id, Utilisateur.nom, Vente.cree_le, Vente.total, Vente.montant_recu)
            )
            if utilisateur.role != ROLE_GERANT:
                statement = statement.where(Vente.vendeur_id == utilisateur.utilisateur_id)
            if terme.strip():
                motif = f"%{terme.strip()}%"
                statement = statement.where(or_(Vente.numero_vente.ilike(motif), Utilisateur.nom.ilike(motif)))
            if date_debut is not None:
                statement = statement.where(func.substr(Vente.cree_le, 1, 10) >= date_debut.isoformat())
            if date_fin is not None:
                statement = statement.where(func.substr(Vente.cree_le, 1, 10) <= date_fin.isoformat())
            statement = statement.order_by(Vente.cree_le.desc(), Vente.id.desc()).limit(limit)

            rows = session.execute(statement).all()
            return [
                VenteHistoriqueItem(
                    vente_id=row[0],
                    numero_vente=row[1],
                    vendeur_id=row[2],
                    vendeur_nom=row[3],
                    date_vente=_format_datetime(row[4]),
                    total=row[5],
                    montant_recu=row[6],
                    monnaie_rendue=row[6] - row[5],
                    articles=int(row[7]),
                )
                for row in rows
            ]

    def synthese_gerant(self, utilisateur: SessionUtilisateur, *, date_reference: date | None = None) -> RapportSynthese:
        """Calcule les indicateurs globaux reserves au gerant."""
        exiger_permission(utilisateur.role, PERMISSION_CONSULTER_RAPPORTS_GLOBAUX)
        reference = date_reference or date.today()
        mois_prefix = reference.strftime("%Y-%m")
        jour = reference.isoformat()

        with self._session_factory() as session:
            ventes_jour, total_jour = _count_sum(
                session.execute(
                    select(func.count(Vente.id), func.coalesce(func.sum(Vente.total), 0)).where(
                        func.substr(Vente.cree_le, 1, 10) == jour
                    )
                ).one()
            )
            ventes_mois, total_mois = _count_sum(
                session.execute(
                    select(func.count(Vente.id), func.coalesce(func.sum(Vente.total), 0)).where(
                        func.substr(Vente.cree_le, 1, 7) == mois_prefix
                    )
                ).one()
            )
            panier_moyen = int(total_jour / ventes_jour) if ventes_jour else 0

            vendeurs_rows = session.execute(
                select(
                    Vente.vendeur_id,
                    func.coalesce(Utilisateur.nom, "Vendeur"),
                    func.count(Vente.id),
                    func.coalesce(func.sum(Vente.total), 0),
                )
                .select_from(Vente)
                .outerjoin(Utilisateur, Utilisateur.id == Vente.vendeur_id)
                .where(func.substr(Vente.cree_le, 1, 10) == jour)
                .group_by(Vente.vendeur_id, Utilisateur.nom)
                .order_by(func.coalesce(func.sum(Vente.total), 0).desc())
            ).all()
            produits_rows = session.execute(
                select(
                    Produit.id,
                    Produit.nom,
                    func.coalesce(func.sum(LigneVente.quantite), 0),
                    func.coalesce(func.sum(LigneVente.sous_total), 0),
                )
                .select_from(LigneVente)
                .join(Vente, Vente.id == LigneVente.vente_id)
                .join(Produit, Produit.id == LigneVente.produit_id)
                .where(func.substr(Vente.cree_le, 1, 10) == jour)
                .group_by(Produit.id, Produit.nom)
                .order_by(func.coalesce(func.sum(LigneVente.quantite), 0).desc())
                .limit(10)
            ).all()

            return RapportSynthese(
                ventes_jour=ventes_jour,
                total_jour=total_jour,
                ventes_mois=ventes_mois,
                total_mois=total_mois,
                panier_moyen=panier_moyen,
                vendeurs=[
                    RapportVendeurItem(vendeur_id=row[0], vendeur_nom=row[1], ventes=int(row[2]), total=int(row[3]))
                    for row in vendeurs_rows
                ],
                produits=[
                    ProduitVenduItem(produit_id=row[0], produit_nom=row[1], quantite=int(row[2]), total=int(row[3]))
                    for row in produits_rows
                ],
            )

    def lister_actions(self, utilisateur: SessionUtilisateur, *, terme: str = "", limit: int = 100) -> list[JournalActionItem]:
        """Retourne le journal systeme reserve au gerant."""
        exiger_permission(utilisateur.role, PERMISSION_CONSULTER_HISTORIQUE_SYSTEME)
        with self._session_factory() as session:
            statement = (
                select(
                    JournalActivite.id,
                    JournalActivite.cree_le,
                    func.coalesce(Utilisateur.nom, "Systeme"),
                    JournalActivite.action,
                    func.coalesce(JournalActivite.details, ""),
                    func.coalesce(JournalActivite.table_cible, "systeme"),
                )
                .select_from(JournalActivite)
                .outerjoin(Utilisateur, Utilisateur.id == JournalActivite.utilisateur_id)
            )
            if terme.strip():
                motif = f"%{terme.strip()}%"
                statement = statement.where(
                    or_(
                        Utilisateur.nom.ilike(motif),
                        JournalActivite.action.ilike(motif),
                        JournalActivite.details.ilike(motif),
                        JournalActivite.table_cible.ilike(motif),
                    )
                )
            rows = session.execute(statement.order_by(JournalActivite.cree_le.desc(), JournalActivite.id.desc()).limit(limit)).all()
            return [
                JournalActionItem(
                    journal_id=row[0],
                    date_action=_format_datetime(row[1]),
                    utilisateur_nom=row[2],
                    action=row[3],
                    details=row[4],
                    module=_module_label(row[5]),
                )
                for row in rows
            ]


def _count_sum(row) -> tuple[int, int]:
    return int(row[0]), int(row[1])


def _format_datetime(value: str) -> str:
    return value[:16].replace("-", "/") if value else ""


def _module_label(value: str) -> str:
    labels = {
        "ventes": "Ventes",
        "produits": "Produits",
        "lots_produits": "Stock",
        "mouvements_stock": "Stock",
        "utilisateurs": "Vendeurs",
        "parametres": "Parametres",
    }
    return labels.get(value or "", "Systeme")
