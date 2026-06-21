"""Acces base pour les parametres applicatifs."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import Parametre


class ParametreRepository:
    """Gere l'enregistrement principal de configuration metier."""

    def compter(self, session: Session) -> int:
        return session.execute(select(func.count()).select_from(Parametre)).scalar_one()

    def obtenir_principal(self, session: Session) -> Parametre | None:
        statement = select(Parametre).order_by(Parametre.id.asc()).limit(1)
        return session.execute(statement).scalar_one_or_none()

    def creer(self, session: Session, parametre: Parametre) -> Parametre:
        session.add(parametre)
        session.flush()
        return parametre
