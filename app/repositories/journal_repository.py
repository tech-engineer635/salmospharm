"""Acces base pour les journaux d'activite."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import JournalActivite


class JournalRepository:
    """Persiste et lit l'historique metier consultable plus tard par le gerant."""

    def creer(self, session: Session, journal: JournalActivite) -> JournalActivite:
        session.add(journal)
        session.flush()
        return journal

    def lister(self, session: Session, limite: int = 100) -> list[JournalActivite]:
        statement = (
            select(JournalActivite)
            .order_by(JournalActivite.cree_le.desc(), JournalActivite.id.desc())
            .limit(limite)
        )
        return list(session.execute(statement).scalars().all())

    def lister_par_utilisateur(self, session: Session, utilisateur_id: int, limite: int = 100) -> list[JournalActivite]:
        statement = (
            select(JournalActivite)
            .where(JournalActivite.utilisateur_id == utilisateur_id)
            .order_by(JournalActivite.cree_le.desc(), JournalActivite.id.desc())
            .limit(limite)
        )
        return list(session.execute(statement).scalars().all())

    def lister_par_action(self, session: Session, action: str, limite: int = 100) -> list[JournalActivite]:
        statement = (
            select(JournalActivite)
            .where(JournalActivite.action == action)
            .order_by(JournalActivite.cree_le.desc(), JournalActivite.id.desc())
            .limit(limite)
        )
        return list(session.execute(statement).scalars().all())
