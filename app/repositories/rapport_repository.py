"""Requetes de lecture utilisees par les rapports et historiques."""

from __future__ import annotations

from datetime import date

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.constants import STATUT_VENTE_VALIDEE
from app.database.models import Categorie, JournalActivite, LigneVente, Produit, Utilisateur, Vente


class RapportRepository:
    """Centralise les aggregations SQL sans persister de table de rapports."""

    @staticmethod
    def _dans_periode(colonne, date_debut: date, date_fin: date):
        jour = func.substr(colonne, 1, 10)
        return and_(jour >= date_debut.isoformat(), jour <= date_fin.isoformat())

    def resume_periode(self, session: Session, date_debut: date, date_fin: date) -> tuple[int, int, int]:
        ventes = session.execute(
            select(func.count(Vente.id), func.coalesce(func.sum(Vente.total), 0)).where(
                Vente.statut == STATUT_VENTE_VALIDEE,
                self._dans_periode(Vente.cree_le, date_debut, date_fin),
            )
        ).one()
        produits = session.execute(
            select(func.coalesce(func.sum(LigneVente.quantite), 0))
            .join(Vente, Vente.id == LigneVente.vente_id)
            .where(
                Vente.statut == STATUT_VENTE_VALIDEE,
                self._dans_periode(Vente.cree_le, date_debut, date_fin),
            )
        ).scalar_one()
        return int(ventes[0]), int(ventes[1]), int(produits)

    def evolution_journaliere(self, session: Session, date_debut: date, date_fin: date) -> list[tuple[str, int, int]]:
        jour = func.substr(Vente.cree_le, 1, 10)
        rows = session.execute(
            select(jour, func.count(Vente.id), func.coalesce(func.sum(Vente.total), 0))
            .where(
                Vente.statut == STATUT_VENTE_VALIDEE,
                self._dans_periode(Vente.cree_le, date_debut, date_fin),
            )
            .group_by(jour)
            .order_by(jour)
        ).all()
        return [(str(row[0]), int(row[1]), int(row[2])) for row in rows]

    def repartition_categories(self, session: Session, date_debut: date, date_fin: date) -> list[tuple[str, int, int]]:
        nom_categorie = func.coalesce(Categorie.nom, "Sans categorie")
        rows = session.execute(
            select(
                nom_categorie,
                func.coalesce(func.sum(LigneVente.quantite), 0),
                func.coalesce(func.sum(LigneVente.sous_total), 0),
            )
            .select_from(LigneVente)
            .join(Vente, Vente.id == LigneVente.vente_id)
            .join(Produit, Produit.id == LigneVente.produit_id)
            .outerjoin(Categorie, Categorie.id == Produit.categorie_id)
            .where(
                Vente.statut == STATUT_VENTE_VALIDEE,
                self._dans_periode(Vente.cree_le, date_debut, date_fin),
            )
            .group_by(nom_categorie)
            .order_by(func.coalesce(func.sum(LigneVente.sous_total), 0).desc())
        ).all()
        return [(str(row[0]), int(row[1]), int(row[2])) for row in rows]

    def performances_vendeurs(self, session: Session, date_debut: date, date_fin: date) -> list[tuple[int | None, str, int, int, int]]:
        ventes = session.execute(
            select(
                Vente.vendeur_id,
                func.coalesce(Utilisateur.nom, "Vendeur"),
                func.count(Vente.id),
                func.coalesce(func.sum(Vente.total), 0),
            )
            .select_from(Vente)
            .outerjoin(Utilisateur, Utilisateur.id == Vente.vendeur_id)
            .where(
                Vente.statut == STATUT_VENTE_VALIDEE,
                self._dans_periode(Vente.cree_le, date_debut, date_fin),
            )
            .group_by(Vente.vendeur_id, Utilisateur.nom)
            .order_by(func.coalesce(func.sum(Vente.total), 0).desc())
        ).all()
        quantites = dict(
            session.execute(
                select(Vente.vendeur_id, func.coalesce(func.sum(LigneVente.quantite), 0))
                .select_from(LigneVente)
                .join(Vente, Vente.id == LigneVente.vente_id)
                .where(
                    Vente.statut == STATUT_VENTE_VALIDEE,
                    self._dans_periode(Vente.cree_le, date_debut, date_fin),
                )
                .group_by(Vente.vendeur_id)
            ).all()
        )
        return [
            (row[0], str(row[1]), int(row[2]), int(row[3]), int(quantites.get(row[0], 0)))
            for row in ventes
        ]

    def totaux_vendeurs(self, session: Session, date_debut: date, date_fin: date) -> dict[int | None, int]:
        rows = session.execute(
            select(Vente.vendeur_id, func.coalesce(func.sum(Vente.total), 0))
            .where(
                Vente.statut == STATUT_VENTE_VALIDEE,
                self._dans_periode(Vente.cree_le, date_debut, date_fin),
            )
            .group_by(Vente.vendeur_id)
        ).all()
        return {row[0]: int(row[1]) for row in rows}

    def produits_plus_vendus(self, session: Session, date_debut: date, date_fin: date, limit: int = 10) -> list[tuple[int, str, int, int]]:
        rows = session.execute(
            select(
                Produit.id,
                Produit.nom,
                func.coalesce(func.sum(LigneVente.quantite), 0),
                func.coalesce(func.sum(LigneVente.sous_total), 0),
            )
            .select_from(LigneVente)
            .join(Vente, Vente.id == LigneVente.vente_id)
            .join(Produit, Produit.id == LigneVente.produit_id)
            .where(
                Vente.statut == STATUT_VENTE_VALIDEE,
                self._dans_periode(Vente.cree_le, date_debut, date_fin),
            )
            .group_by(Produit.id, Produit.nom)
            .order_by(func.coalesce(func.sum(LigneVente.quantite), 0).desc())
            .limit(limit)
        ).all()
        return [(int(row[0]), str(row[1]), int(row[2]), int(row[3])) for row in rows]

    def lister_ventes(
        self,
        session: Session,
        *,
        vendeur_id: int | None,
        terme: str,
        date_debut: date | None,
        date_fin: date | None,
        limit: int,
    ):
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
            .where(Vente.statut == STATUT_VENTE_VALIDEE)
            .group_by(Vente.id, Vente.numero_vente, Vente.vendeur_id, Utilisateur.nom, Vente.cree_le, Vente.total, Vente.montant_recu)
        )
        if vendeur_id is not None:
            statement = statement.where(Vente.vendeur_id == vendeur_id)
        if terme.strip():
            motif = f"%{terme.strip()}%"
            statement = statement.where(or_(Vente.numero_vente.ilike(motif), Utilisateur.nom.ilike(motif)))
        if date_debut is not None:
            statement = statement.where(func.substr(Vente.cree_le, 1, 10) >= date_debut.isoformat())
        if date_fin is not None:
            statement = statement.where(func.substr(Vente.cree_le, 1, 10) <= date_fin.isoformat())
        return session.execute(statement.order_by(Vente.cree_le.desc(), Vente.id.desc()).limit(limit)).all()

    def lister_actions(self, session: Session, *, terme: str, limit: int):
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
        return session.execute(
            statement.order_by(JournalActivite.cree_le.desc(), JournalActivite.id.desc()).limit(limit)
        ).all()
