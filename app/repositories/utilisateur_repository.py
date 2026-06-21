"""Acces base pour les utilisateurs."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import Utilisateur


class UtilisateurRepository:
    def compter(self, session: Session) -> int:
        return session.execute(select(func.count()).select_from(Utilisateur)).scalar_one()

    def existe_par_email(self, session: Session, email: str) -> bool:
        statement = select(Utilisateur.id).where(Utilisateur.email == email)
        return session.execute(statement).first() is not None

    def chercher_par_email(self, session: Session, email: str) -> Utilisateur | None:
        statement = select(Utilisateur).where(Utilisateur.email == email)
        return session.execute(statement).scalar_one_or_none()

    def creer(self, session: Session, utilisateur: Utilisateur) -> Utilisateur:
        session.add(utilisateur)
        session.flush()
        return utilisateur
