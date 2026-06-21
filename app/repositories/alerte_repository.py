"""Acces base pour les alertes metier."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Alerte


class AlerteRepository:
    """Isole les requetes de creation et consultation des alertes."""

    def chercher_par_id(self, session: Session, alerte_id: int) -> Alerte | None:
        return session.get(Alerte, alerte_id)

    def chercher_non_lue(
        self,
        session: Session,
        produit_id: int,
        lot_id: int | None,
        type_alerte: str,
    ) -> Alerte | None:
        statement = select(Alerte).where(
            Alerte.produit_id == produit_id,
            Alerte.lot_id == lot_id,
            Alerte.type_alerte == type_alerte,
            Alerte.est_lue == 0,
        )
        return session.execute(statement).scalar_one_or_none()

    def lister_non_lues(self, session: Session) -> list[Alerte]:
        statement = (
            select(Alerte)
            .where(Alerte.est_lue == 0)
            .order_by(Alerte.cree_le.desc(), Alerte.id.desc())
        )
        return list(session.execute(statement).scalars().all())

    def creer(self, session: Session, alerte: Alerte) -> Alerte:
        session.add(alerte)
        session.flush()
        return alerte

    def marquer_lue(self, session: Session, alerte: Alerte) -> Alerte:
        alerte.est_lue = 1
        session.flush()
        return alerte
