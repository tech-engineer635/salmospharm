"""Service de generation des alertes de stock."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.constants import (
    TYPE_ALERTE_EXPIRATION_PROCHE,
    TYPE_ALERTE_PRODUIT_EXPIRE,
    TYPE_ALERTE_STOCK_FAIBLE,
)
from app.core.permissions import PERMISSION_CONSULTER_RAPPORTS_GLOBAUX, exiger_permission
from app.database.connection import create_session
from app.database.models import Alerte, LotProduit, Produit
from app.repositories.alerte_repository import AlerteRepository
from app.repositories.parametre_repository import ParametreRepository
from app.repositories.lot_produit_repository import LotProduitRepository
from app.repositories.produit_repository import ProduitRepository
from app.repositories.stock_repository import StockRepository
from app.services.auth_service import SessionUtilisateur


class AlerteService:
    """Genere les alertes non lues sans les dupliquer."""

    def __init__(
        self,
        session_factory=create_session,
        alerte_repository: AlerteRepository | None = None,
        stock_repository: StockRepository | None = None,
        parametre_repository: ParametreRepository | None = None,
        produit_repository: ProduitRepository | None = None,
        lot_repository: LotProduitRepository | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._alerte_repository = alerte_repository or AlerteRepository()
        self._stock_repository = stock_repository or StockRepository()
        self._parametre_repository = parametre_repository or ParametreRepository()
        self._produit_repository = produit_repository or ProduitRepository()
        self._lot_repository = lot_repository or LotProduitRepository()

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

    def lister_alertes(self, utilisateur: SessionUtilisateur, *, non_lues_seulement: bool = False) -> list[Alerte]:
        """Retourne les alertes visibles par le gerant."""
        exiger_permission(utilisateur.role, PERMISSION_CONSULTER_RAPPORTS_GLOBAUX)
        with self._session_factory() as session:
            return self._alerte_repository.lister(session, non_lues_seulement=non_lues_seulement)

    def marquer_lue(self, utilisateur: SessionUtilisateur, *, alerte_id: int) -> None:
        """Marque une alerte comme lue, operation reservee au gerant."""
        exiger_permission(utilisateur.role, PERMISSION_CONSULTER_RAPPORTS_GLOBAUX)
        with self._session_factory() as session:
            alerte = self._alerte_repository.chercher_par_id(session, alerte_id)
            if alerte is None:
                return
            self._alerte_repository.marquer_lue(session, alerte)
            session.commit()

    def reinitialiser_alertes_actives_au_demarrage(self) -> int:
        """Rend visibles les alertes acquittees qui restent non resolues."""

        with self._session_factory() as session:
            count = self._alerte_repository.reactiver_non_lues_au_demarrage(session)
            session.commit()
            return count

    def reconcilier_alertes(
        self,
        *,
        produit_ids: set[int] | None = None,
        date_reference: date | None = None,
    ) -> int:
        """Synchronise les alertes persistantes avec l'etat reel du stock."""

        reference = date_reference or date.today()
        changements = 0
        with self._session_factory() as session:
            produits = self._produit_repository.lister(session)
            if produit_ids is not None:
                produits = [produit for produit in produits if produit.id in produit_ids]

            for produit in produits:
                attendues = self._alertes_attendues(
                    session, produit=produit, date_reference=reference
                )
                existantes = [
                    alerte
                    for alerte in self._alerte_repository.lister_actives(session)
                    if alerte.produit_id == produit.id
                ]
                index = {
                    (alerte.type_alerte, alerte.lot_id): alerte
                    for alerte in existantes
                }
                for cle, message in attendues.items():
                    alerte = index.pop(cle, None)
                    if alerte is None:
                        self._alerte_repository.creer(
                            session,
                            Alerte(
                                produit_id=produit.id,
                                lot_id=cle[1],
                                type_alerte=cle[0],
                                message=message,
                                est_active=1,
                                est_lue=0,
                                derniere_detection_le=datetime.now().isoformat(
                                    timespec="seconds"
                                ),
                            ),
                        )
                        changements += 1
                    elif alerte.message != message:
                        self._alerte_repository.toucher(session, alerte, message)
                        changements += 1
                for alerte in index.values():
                    self._alerte_repository.resoudre(session, alerte)
                    changements += 1
            session.commit()
        return changements

    def _alertes_attendues(
        self,
        session: Session,
        *,
        produit: Produit,
        date_reference: date,
    ) -> dict[tuple[str, int | None], str]:
        if produit.actif != 1:
            return {}
        attendues: dict[tuple[str, int | None], str] = {}
        stock = self._stock_repository.calculer_stock_disponible(
            session, produit.id, date_reference.isoformat()
        )
        if stock <= produit.stock_minimum:
            etat = "Rupture" if stock == 0 else "Stock faible"
            attendues[(TYPE_ALERTE_STOCK_FAIBLE, None)] = (
                f"{etat} pour {produit.nom}: {stock} disponible(s)."
            )

        parametre = self._parametre_repository.obtenir_principal(session)
        seuil = parametre.seuil_expiration_jours if parametre is not None else 30
        for lot in self._lot_repository.lister_par_produit(session, produit.id):
            if lot.quantite <= 0 or not lot.date_expiration:
                continue
            try:
                expiration = date.fromisoformat(lot.date_expiration)
            except ValueError:
                continue
            numero = lot.numero_lot or str(lot.id)
            if expiration < date_reference:
                attendues[(TYPE_ALERTE_PRODUIT_EXPIRE, lot.id)] = (
                    f"Lot expire pour {produit.nom}, lot {numero}."
                )
            elif expiration <= date_reference + timedelta(days=seuil):
                attendues[(TYPE_ALERTE_EXPIRATION_PROCHE, lot.id)] = (
                    f"Expiration proche pour {produit.nom}, lot {numero}."
                )
        return attendues

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
        existante = self._alerte_repository.chercher_active(
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

        existante = self._alerte_repository.chercher_active(
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
