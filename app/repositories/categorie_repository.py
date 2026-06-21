"""Acces base pour les categories de produits."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Categorie


class CategorieRepository:
    """Expose les operations de persistance simples pour `categories`."""

    def chercher_par_id(self, session: Session, categorie_id: int) -> Categorie | None:
        return session.get(Categorie, categorie_id)

    def chercher_par_nom(self, session: Session, nom: str) -> Categorie | None:
        statement = select(Categorie).where(Categorie.nom == nom)
        return session.execute(statement).scalar_one_or_none()

    def lister(self, session: Session) -> list[Categorie]:
        statement = select(Categorie).order_by(Categorie.nom.asc())
        return list(session.execute(statement).scalars().all())

    def creer(self, session: Session, categorie: Categorie) -> Categorie:
        session.add(categorie)
        session.flush()
        return categorie

