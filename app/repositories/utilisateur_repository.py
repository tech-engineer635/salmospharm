"""Acces base pour les utilisateurs."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import Utilisateur


class UtilisateurRepository:
    """Regroupe uniquement les requetes SQLAlchemy liees aux utilisateurs."""

    def compter(self, session: Session) -> int:
        return session.execute(select(func.count()).select_from(Utilisateur)).scalar_one()

    def chercher_par_id(self, session: Session, utilisateur_id: int) -> Utilisateur | None:
        return session.get(Utilisateur, utilisateur_id)

    def existe_par_email(self, session: Session, email: str) -> bool:
        statement = select(Utilisateur.id).where(Utilisateur.email == email)
        return session.execute(statement).first() is not None

    def chercher_par_email(self, session: Session, email: str) -> Utilisateur | None:
        statement = select(Utilisateur).where(Utilisateur.email == email)
        return session.execute(statement).scalar_one_or_none()

    def lister(self, session: Session) -> list[Utilisateur]:
        statement = select(Utilisateur).order_by(Utilisateur.nom.asc())
        return list(session.execute(statement).scalars().all())

    def lister_par_role(self, session: Session, role: str) -> list[Utilisateur]:
        statement = select(Utilisateur).where(Utilisateur.role == role).order_by(Utilisateur.nom.asc())
        return list(session.execute(statement).scalars().all())

    def lister_actifs(self, session: Session) -> list[Utilisateur]:
        statement = select(Utilisateur).where(Utilisateur.actif == 1).order_by(Utilisateur.nom.asc())
        return list(session.execute(statement).scalars().all())

    def creer(self, session: Session, utilisateur: Utilisateur) -> Utilisateur:
        session.add(utilisateur)
        session.flush()
        return utilisateur

    def desactiver(self, session: Session, utilisateur: Utilisateur) -> Utilisateur:
        utilisateur.actif = 0
        session.flush()
        return utilisateur
