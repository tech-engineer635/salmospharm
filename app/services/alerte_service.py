"""Service de generation des alertes de stock."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.constants import TYPE_ALERTE_EXPIRATION_PROCHE, TYPE_ALERTE_STOCK_FAIBLE
from app.database.models import Alerte, LotProduit, Produit
from app.repositories.alerte_repository import AlerteRepository
from app.repositories.parametre_repository import ParametreRepository
from app.repositories.stock_repository import StockRepository


class AlerteService:
    """Genere les alertes non lues sans les dupliquer."""

    def __init__(
        self,
        alerte_repository: AlerteRepository | None = None,
        stock_repository: StockRepository | None = None,
        parametre_repository: ParametreRepository | None = None,
    ) -> None:
        self._alerte_repository = alerte_repository or AlerteRepository()
        self._stock_repository = stock_repository or StockRepository()
        self._parametre_repository = parametre_repository or ParametreRepository()

    def generer_alertes_pour_lot(
        self,
        session: Session,
        *,
        produit: Produit,
        lot: LotProduit,
        date_reference: date | None = None,
    ) -> list[Alerte]:
        """Cree les alertes stock faible et expiration proche dans la transaction courante."""
        reference = date_reference or date.today()
        alertes: list[Alerte] = []
        alertes.extend(self._generer_alerte_stock_faible(session, produit=produit, date_reference=reference))
        alertes.extend(self._generer_alerte_expiration(session, produit=produit, lot=lot, date_reference=reference))
        return alertes

    def _generer_alerte_stock_faible(
        self,
        session: Session,
        *,
        produit: Produit,
        date_reference: date,
    ) -> list[Alerte]:
        stock_disponible = self._stock_repository.calculer_stock_disponible(
            session,
            produit.id,
            date_reference.isoformat(),
        )
        if stock_disponible > produit.stock_minimum:
            return []
        existante = self._alerte_repository.chercher_non_lue(
            session,
            produit.id,
            None,
            TYPE_ALERTE_STOCK_FAIBLE,
        )
        if existante is not None:
            return []
        alerte = Alerte(
            produit_id=produit.id,
            lot_id=None,
            type_alerte=TYPE_ALERTE_STOCK_FAIBLE,
            message=f"Stock faible pour {produit.nom}: {stock_disponible} disponible(s).",
        )
        return [self._alerte_repository.creer(session, alerte)]

    def _generer_alerte_expiration(
        self,
        session: Session,
        *,
        produit: Produit,
        lot: LotProduit,
        date_reference: date,
    ) -> list[Alerte]:
        if not lot.date_expiration:
            return []
        try:
            expiration = date.fromisoformat(lot.date_expiration)
        except ValueError:
            return []

        parametre = self._parametre_repository.obtenir_principal(session)
        seuil_jours = parametre.seuil_expiration_jours if parametre is not None else 30
        if not (date_reference <= expiration <= date_reference + timedelta(days=seuil_jours)):
            return []

        existante = self._alerte_repository.chercher_non_lue(
            session,
            produit.id,
            lot.id,
            TYPE_ALERTE_EXPIRATION_PROCHE,
        )
        if existante is not None:
            return []

        alerte = Alerte(
            produit_id=produit.id,
            lot_id=lot.id,
            type_alerte=TYPE_ALERTE_EXPIRATION_PROCHE,
            message=f"Expiration proche pour {produit.nom}, lot {lot.numero_lot or lot.id}.",
        )
        return [self._alerte_repository.creer(session, alerte)]
