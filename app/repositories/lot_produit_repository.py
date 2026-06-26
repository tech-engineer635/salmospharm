"""Acces base pour les lots physiques de produits."""

from __future__ import annotations

from sqlalchemy import case, or_, select
from sqlalchemy.orm import Session

from app.database.models import LotProduit, Produit


class LotProduitRepository:
    """Fournit les requetes de lots necessaires au stock et a FEFO."""

    def chercher_par_id(self, session: Session, lot_id: int) -> LotProduit | None:
        return session.get(LotProduit, lot_id)

    def chercher_par_produit_et_numero(
        self,
        session: Session,
        produit_id: int,
        numero_lot: str | None,
    ) -> LotProduit | None:
        statement = select(LotProduit).where(
            LotProduit.produit_id == produit_id,
            LotProduit.numero_lot == numero_lot,
        )
        return session.execute(statement).scalar_one_or_none()

    def lister_par_produit(self, session: Session, produit_id: int) -> list[LotProduit]:
        statement = (
            select(LotProduit)
            .where(LotProduit.produit_id == produit_id)
            .order_by(LotProduit.date_expiration.asc(), LotProduit.id.asc())
        )
        return list(session.execute(statement).scalars().all())

    def lister(self, session: Session) -> list[LotProduit]:
        statement = select(LotProduit).order_by(LotProduit.id.desc())
        return list(session.execute(statement).scalars().all())

    def lister_disponibles_par_produit(
        self,
        session: Session,
        produit_id: int,
        date_reference: str,
    ) -> list[LotProduit]:
        """Retourne les lots vendables tries pour aider le service FEFO."""
        expiration_inconnue_en_dernier = case((LotProduit.date_expiration.is_(None), 1), else_=0)
        statement = (
            select(LotProduit)
            .join(Produit)
            .where(
                LotProduit.produit_id == produit_id,
                Produit.actif == 1,
                LotProduit.quantite > 0,
                or_(LotProduit.date_expiration.is_(None), LotProduit.date_expiration >= date_reference),
            )
            .order_by(expiration_inconnue_en_dernier.asc(), LotProduit.date_expiration.asc(), LotProduit.id.asc())
        )
        return list(session.execute(statement).scalars().all())

    def creer(self, session: Session, lot: LotProduit) -> LotProduit:
        session.add(lot)
        session.flush()
        return lot

    def enregistrer_quantite(self, session: Session, lot: LotProduit, quantite: int) -> LotProduit:
        lot.quantite = quantite
        session.flush()
        return lot

    def mettre_a_jour(self, session: Session, lot: LotProduit) -> LotProduit:
        session.add(lot)
        session.flush()
        return lot
