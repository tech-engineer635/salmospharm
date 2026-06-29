"""Acces base pour les alertes metier."""

from __future__ import annotations

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from app.database.models import Alerte


class AlerteRepository:
    """Isole les requetes de creation et consultation des alertes."""

    def chercher_par_id(self, session: Session, alerte_id: int) -> Alerte | None:
        return session.get(Alerte, alerte_id)

    def chercher_active(
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
            Alerte.est_active == 1,
        )
        return session.execute(statement).scalar_one_or_none()

    def chercher_non_lue(
        self,
        session: Session,
        produit_id: int,
        lot_id: int | None,
        type_alerte: str,
    ) -> Alerte | None:
        """Compatibilite: une alerte active remplace l'ancien critere non lu."""

        return self.chercher_active(session, produit_id, lot_id, type_alerte)

    def lister_non_lues(self, session: Session) -> list[Alerte]:
        statement = (
            select(Alerte)
            .options(selectinload(Alerte.produit), selectinload(Alerte.lot))
            .where(Alerte.est_active == 1, Alerte.est_lue == 0)
            .order_by(Alerte.cree_le.desc(), Alerte.id.desc())
        )
        return list(session.execute(statement).scalars().all())

    def lister(self, session: Session, *, non_lues_seulement: bool = False, limit: int = 100) -> list[Alerte]:
        statement = (
            select(Alerte)
            .options(selectinload(Alerte.produit), selectinload(Alerte.lot))
            .where(Alerte.est_active == 1)
        )
        if non_lues_seulement:
            statement = statement.where(Alerte.est_lue == 0)
        statement = statement.order_by(Alerte.cree_le.desc(), Alerte.id.desc()).limit(limit)
        return list(session.execute(statement).scalars().all())

    def creer(self, session: Session, alerte: Alerte) -> Alerte:
        session.add(alerte)
        session.flush()
        return alerte

    def marquer_lue(self, session: Session, alerte: Alerte) -> Alerte:
        alerte.est_lue = 1
        session.flush()
        return alerte

    def toucher(self, session: Session, alerte: Alerte, message: str) -> Alerte:
        alerte.message = message
        alerte.derniere_detection_le = func.current_timestamp()
        session.flush()
        return alerte

    def resoudre(self, session: Session, alerte: Alerte) -> Alerte:
        alerte.est_active = 0
        alerte.resolue_le = func.current_timestamp()
        session.flush()
        return alerte

    def lister_actives(self, session: Session) -> list[Alerte]:
        statement = select(Alerte).where(Alerte.est_active == 1)
        return list(session.execute(statement).scalars().all())

    def reactiver_non_lues_au_demarrage(self, session: Session) -> int:
        result = session.execute(
            update(Alerte)
            .where(Alerte.est_active == 1, Alerte.est_lue == 1)
            .values(est_lue=0)
        )
        return int(result.rowcount or 0)
