"""Acces base pour le catalogue des produits."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Produit


class ProduitRepository:
    """Centralise les requetes catalogue sans appliquer les permissions metier."""

    def chercher_par_id(self, session: Session, produit_id: int) -> Produit | None:
        return session.get(Produit, produit_id)

    def chercher_par_code_barres(self, session: Session, code_barres: str) -> Produit | None:
        statement = select(Produit).where(Produit.code_barres == code_barres)
        return session.execute(statement).scalar_one_or_none()

    def lister(self, session: Session) -> list[Produit]:
        statement = select(Produit).order_by(Produit.nom.asc())
        return list(session.execute(statement).scalars().all())

    def lister_actifs(self, session: Session) -> list[Produit]:
        statement = select(Produit).where(Produit.actif == 1).order_by(Produit.nom.asc())
        return list(session.execute(statement).scalars().all())

    def lister_par_categorie(self, session: Session, categorie_id: int) -> list[Produit]:
        statement = (
            select(Produit)
            .where(Produit.categorie_id == categorie_id)
            .order_by(Produit.nom.asc())
        )
        return list(session.execute(statement).scalars().all())

    def rechercher_par_nom(self, session: Session, terme: str) -> list[Produit]:
        statement = (
            select(Produit)
            .where(Produit.nom.ilike(f"%{terme}%"))
            .order_by(Produit.nom.asc())
        )
        return list(session.execute(statement).scalars().all())

    def creer(self, session: Session, produit: Produit) -> Produit:
        session.add(produit)
        session.flush()
        return produit

    def desactiver(self, session: Session, produit: Produit) -> Produit:
        produit.actif = 0
        session.flush()
        return produit
