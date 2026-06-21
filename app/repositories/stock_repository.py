"""Acces base pour les mouvements et lectures de stock."""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database.models import LotProduit, MouvementStock, Produit


class StockRepository:
    """Contient les requetes de stock sans decider des regles de vente."""

    def calculer_stock_disponible(self, session: Session, produit_id: int, date_reference: str) -> int:
        """Somme les quantites des lots vendables pour un produit actif."""
        statement = (
            select(func.coalesce(func.sum(LotProduit.quantite), 0))
            .join(Produit)
            .where(
                LotProduit.produit_id == produit_id,
                Produit.actif == 1,
                LotProduit.quantite > 0,
                or_(LotProduit.date_expiration.is_(None), LotProduit.date_expiration >= date_reference),
            )
        )
        return int(session.execute(statement).scalar_one())

    def creer_mouvement(self, session: Session, mouvement: MouvementStock) -> MouvementStock:
        session.add(mouvement)
        session.flush()
        return mouvement

    def lister_mouvements_par_produit(self, session: Session, produit_id: int) -> list[MouvementStock]:
        statement = (
            select(MouvementStock)
            .where(MouvementStock.produit_id == produit_id)
            .order_by(MouvementStock.cree_le.desc(), MouvementStock.id.desc())
        )
        return list(session.execute(statement).scalars().all())

    def lister_mouvements_par_lot(self, session: Session, lot_id: int) -> list[MouvementStock]:
        statement = (
            select(MouvementStock)
            .where(MouvementStock.lot_id == lot_id)
            .order_by(MouvementStock.cree_le.desc(), MouvementStock.id.desc())
        )
        return list(session.execute(statement).scalars().all())

