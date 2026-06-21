"""Acces base pour les ventes validees et leurs lignes."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.models import LigneVente, Vente


class VenteRepository:
    """Manipule les ventes persistantes sans permettre d'annulation."""

    def chercher_par_id(self, session: Session, vente_id: int) -> Vente | None:
        statement = select(Vente).options(selectinload(Vente.lignes)).where(Vente.id == vente_id)
        return session.execute(statement).scalar_one_or_none()

    def chercher_par_numero(self, session: Session, numero_vente: str) -> Vente | None:
        statement = select(Vente).where(Vente.numero_vente == numero_vente)
        return session.execute(statement).scalar_one_or_none()

    def dernier_numero_pour_annee(self, session: Session, annee: int) -> str | None:
        statement = (
            select(Vente.numero_vente)
            .where(Vente.numero_vente.like(f"VTE-{annee}-%"))
            .order_by(Vente.numero_vente.desc())
            .limit(1)
        )
        return session.execute(statement).scalar_one_or_none()

    def creer_vente(self, session: Session, vente: Vente) -> Vente:
        session.add(vente)
        session.flush()
        return vente

    def creer_ligne(self, session: Session, ligne: LigneVente) -> LigneVente:
        session.add(ligne)
        session.flush()
        return ligne

    def lister_lignes(self, session: Session, vente_id: int) -> list[LigneVente]:
        statement = select(LigneVente).where(LigneVente.vente_id == vente_id).order_by(LigneVente.id.asc())
        return list(session.execute(statement).scalars().all())

    def lister_par_vendeur(self, session: Session, vendeur_id: int) -> list[Vente]:
        statement = (
            select(Vente)
            .where(Vente.vendeur_id == vendeur_id)
            .order_by(Vente.cree_le.desc(), Vente.id.desc())
        )
        return list(session.execute(statement).scalars().all())

    def lister_toutes(self, session: Session) -> list[Vente]:
        statement = select(Vente).order_by(Vente.cree_le.desc(), Vente.id.desc())
        return list(session.execute(statement).scalars().all())

