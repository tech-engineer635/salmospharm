"""Service metier de gestion des lots et mouvements de stock."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from datetime import timedelta
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.constants import (
    ACTION_EXPORT_EXCEL,
    ACTION_STOCK_AJUSTE,
    ACTION_STOCK_ENTREE,
    TYPE_MOUVEMENT_AJUSTEMENT,
    TYPE_MOUVEMENT_ENTREE,
)
from app.core.exceptions import ProduitInactifError, StockInsuffisantError, ValidationError
from app.core.paths import get_exports_dir
from app.core.permissions import (
    PERMISSION_AJUSTER_STOCK,
    PERMISSION_CONSULTER_STOCK,
    PERMISSION_ENTRER_STOCK,
    PERMISSION_EXPORTER_DONNEES,
    exiger_permission,
)
from app.database.connection import create_session
from app.database.models import LotProduit, MouvementStock
from app.repositories.lot_produit_repository import LotProduitRepository
from app.repositories.produit_repository import ProduitRepository
from app.repositories.stock_repository import StockRepository
from app.services.alerte_service import AlerteService
from app.services.alert_events import publier_evenement_alerte
from app.services.auth_service import SessionUtilisateur
from app.services.journal_service import JournalService
from app.utils.excel import convertir_date, convertir_datetime, creer_classeur_tableau, enregistrer_classeur


@dataclass(frozen=True)
class EntreeStockPayload:
    produit_id: int
    quantite: int
    prix_achat: int
    numero_lot: str | None = None
    date_expiration: str | None = None
    motif: str | None = None


@dataclass(frozen=True)
class AjustementStockPayload:
    lot_id: int
    nouvelle_quantite: int
    motif: str


@dataclass(frozen=True)
class StockOperationResult:
    lot: LotProduit
    mouvement: MouvementStock
    alertes_creees: int


@dataclass(frozen=True)
class LotFefoSelection:
    lot_id: int
    produit_id: int
    quantite: int
    numero_lot: str | None
    date_expiration: str | None


class StockService:
    """Porte les regles de stock sans laisser l'UI modifier les lots directement."""

    def __init__(
        self,
        session_factory: Callable[[], Session] = create_session,
        produit_repository: ProduitRepository | None = None,
        lot_repository: LotProduitRepository | None = None,
        stock_repository: StockRepository | None = None,
        alerte_service: AlerteService | None = None,
        journal_service: JournalService | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._produit_repository = produit_repository or ProduitRepository()
        self._lot_repository = lot_repository or LotProduitRepository()
        self._stock_repository = stock_repository or StockRepository()
        self._alerte_service = alerte_service or AlerteService(stock_repository=self._stock_repository)
        self._journal_service = journal_service or JournalService()

    def lister_lots(self, utilisateur: SessionUtilisateur) -> list[LotProduit]:
        exiger_permission(utilisateur.role, PERMISSION_CONSULTER_STOCK)
        with self._session_factory() as session:
            return self._lot_repository.lister(session)

    def lister_mouvements_recents(self, utilisateur: SessionUtilisateur, limit: int = 50) -> list[MouvementStock]:
        exiger_permission(utilisateur.role, PERMISSION_CONSULTER_STOCK)
        with self._session_factory() as session:
            return self._stock_repository.lister_mouvements_recents(session, limit)

    def exporter_excel(
        self,
        utilisateur: SessionUtilisateur,
        destination: str | Path | None = None,
    ) -> Path:
        exiger_permission(utilisateur.role, PERMISSION_EXPORTER_DONNEES)
        today = date.today()
        near_limit = today + timedelta(days=30)
        with self._session_factory() as session:
            rows = self._lot_repository.donnees_export(session)
            workbook, count = creer_classeur_tableau(
                titre_feuille="Stock",
                entetes=(
                    "Produit",
                    "Categorie",
                    "Code-barres",
                    "Numero de lot",
                    "Quantite",
                    "Prix d'achat (CDF)",
                    "Date d'expiration",
                    "Etat du lot",
                    "Date d'entree",
                ),
                lignes=(
                    (
                        row[0],
                        row[1] or "Sans categorie",
                        row[2] or "",
                        row[3] or "",
                        int(row[4]),
                        int(row[5]),
                        convertir_date(row[6]),
                        _statut_lot_export(
                            quantite=int(row[4]),
                            stock_total=int(row[7]),
                            stock_minimum=int(row[8]),
                            expiration=convertir_date(row[6]),
                            today=today,
                            near_limit=near_limit,
                        ),
                        convertir_datetime(row[9]),
                    )
                    for row in rows
                ),
                colonnes_cdf=(6,),
                colonnes_date=(7,),
                colonnes_datetime=(9,),
            )
            path = enregistrer_classeur(
                workbook,
                destination or get_exports_dir() / f"stock_{today.isoformat()}.xlsx",
            )
            self._journal_service.journaliser(
                session,
                action=ACTION_EXPORT_EXCEL,
                utilisateur_id=utilisateur.utilisateur_id,
                table_cible="lots_produits",
                details=f"Export Excel stock : {path.name}, {count} ligne(s).",
            )
            session.commit()
        return path

    def choisir_lots_fefo(
        self,
        utilisateur: SessionUtilisateur,
        *,
        produit_id: int,
        quantite_demandee: int,
        date_reference: date | None = None,
    ) -> list[LotFefoSelection]:
        """Selectionne les lots vendables sans les decrementer.

        Cette methode prepare la future vente : elle exclut les lots expires ou
        vides, respecte les produits actifs et repartit la quantite demandee
        du lot qui expire le plus tot vers le plus lointain.
        """
        exiger_permission(utilisateur.role, PERMISSION_CONSULTER_STOCK)
        if not isinstance(quantite_demandee, int) or quantite_demandee <= 0:
            raise ValidationError("La quantite demandee doit etre superieure a zero.")

        reference = date_reference or date.today()
        with self._session_factory() as session:
            produit = self._produit_repository.chercher_par_id(session, produit_id)
            if produit is None:
                raise ValidationError("Produit introuvable.")
            if produit.actif != 1:
                raise ProduitInactifError("Ce produit est desactive et ne peut pas etre vendu.")

            lots = self._lot_repository.lister_disponibles_par_produit(
                session,
                produit_id=produit_id,
                date_reference=reference.isoformat(),
            )
            selections: list[LotFefoSelection] = []
            reste = quantite_demandee

            for lot in lots:
                if reste <= 0:
                    break
                quantite_prise = min(lot.quantite, reste)
                selections.append(
                    LotFefoSelection(
                        lot_id=lot.id,
                        produit_id=lot.produit_id,
                        quantite=quantite_prise,
                        numero_lot=lot.numero_lot,
                        date_expiration=lot.date_expiration,
                    )
                )
                reste -= quantite_prise

            if reste > 0:
                raise StockInsuffisantError("Stock insuffisant pour ce produit.")
            return selections

    def entrer_stock(self, utilisateur: SessionUtilisateur, payload: EntreeStockPayload) -> StockOperationResult:
        exiger_permission(utilisateur.role, PERMISSION_ENTRER_STOCK)
        donnees = self._valider_entree(payload)

        with self._session_factory() as session:
            produit = self._produit_repository.chercher_par_id(session, donnees.produit_id)
            if produit is None:
                raise ValidationError("Produit introuvable.")
            if produit.actif != 1:
                raise ProduitInactifError("Impossible d'ajouter du stock sur un produit desactive.")

            lot = self._lot_repository.chercher_par_produit_et_numero(session, donnees.produit_id, donnees.numero_lot)
            if lot is None:
                lot = LotProduit(
                    produit_id=donnees.produit_id,
                    numero_lot=donnees.numero_lot,
                    quantite=0,
                    prix_achat=donnees.prix_achat,
                    date_expiration=donnees.date_expiration,
                )
                self._lot_repository.creer(session, lot)
            else:
                lot.prix_achat = donnees.prix_achat
                lot.date_expiration = donnees.date_expiration

            lot.quantite += donnees.quantite
            mouvement = MouvementStock(
                produit_id=produit.id,
                lot_id=lot.id,
                utilisateur_id=utilisateur.utilisateur_id,
                type_mouvement=TYPE_MOUVEMENT_ENTREE,
                quantite=donnees.quantite,
                motif=donnees.motif or "Entree de stock",
            )

            try:
                self._lot_repository.mettre_a_jour(session, lot)
                self._stock_repository.creer_mouvement(session, mouvement)
                alertes = self._alerte_service.generer_alertes_pour_lot(session, produit=produit, lot=lot)
                self._journal_service.journaliser(
                    session,
                    action=ACTION_STOCK_ENTREE,
                    utilisateur_id=utilisateur.utilisateur_id,
                    table_cible="lots_produits",
                    element_id=lot.id,
                    details=f"Entree de stock {donnees.quantite} pour {produit.nom}.",
                )
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise ValidationError("Impossible d'enregistrer l'entree de stock.") from exc

            publier_evenement_alerte(produit.id)
            return StockOperationResult(lot=lot, mouvement=mouvement, alertes_creees=len(alertes))

    def ajuster_stock(self, utilisateur: SessionUtilisateur, payload: AjustementStockPayload) -> StockOperationResult:
        exiger_permission(utilisateur.role, PERMISSION_AJUSTER_STOCK)
        donnees = self._valider_ajustement(payload)

        with self._session_factory() as session:
            lot = self._lot_repository.chercher_par_id(session, donnees.lot_id)
            if lot is None:
                raise ValidationError("Lot introuvable.")
            produit = self._produit_repository.chercher_par_id(session, lot.produit_id)
            if produit is None:
                raise ValidationError("Produit introuvable.")

            ancienne_quantite = lot.quantite
            ecart = abs(donnees.nouvelle_quantite - ancienne_quantite)
            if ecart == 0:
                raise ValidationError("La nouvelle quantite doit etre differente de la quantite actuelle.")

            lot.quantite = donnees.nouvelle_quantite
            mouvement = MouvementStock(
                produit_id=lot.produit_id,
                lot_id=lot.id,
                utilisateur_id=utilisateur.utilisateur_id,
                type_mouvement=TYPE_MOUVEMENT_AJUSTEMENT,
                quantite=ecart,
                motif=donnees.motif,
            )

            self._lot_repository.mettre_a_jour(session, lot)
            self._stock_repository.creer_mouvement(session, mouvement)
            alertes = self._alerte_service.generer_alertes_pour_lot(session, produit=produit, lot=lot)
            self._journal_service.journaliser(
                session,
                action=ACTION_STOCK_AJUSTE,
                utilisateur_id=utilisateur.utilisateur_id,
                table_cible="lots_produits",
                element_id=lot.id,
                details=f"Ajustement stock lot {lot.numero_lot or lot.id}: {ancienne_quantite} -> {lot.quantite}.",
            )
            session.commit()

            publier_evenement_alerte(produit.id)
            return StockOperationResult(lot=lot, mouvement=mouvement, alertes_creees=len(alertes))

    def _valider_entree(self, payload: EntreeStockPayload) -> EntreeStockPayload:
        if not isinstance(payload.quantite, int) or payload.quantite <= 0:
            raise ValidationError("La quantite d'entree doit etre superieure a zero.")
        if not isinstance(payload.prix_achat, int) or payload.prix_achat < 0:
            raise ValidationError("Le prix d'achat doit etre un entier CDF positif.")
        date_expiration = self._normaliser_date(payload.date_expiration)
        return EntreeStockPayload(
            produit_id=payload.produit_id,
            quantite=payload.quantite,
            prix_achat=payload.prix_achat,
            numero_lot=self._normaliser_texte_optionnel(payload.numero_lot),
            date_expiration=date_expiration,
            motif=self._normaliser_texte_optionnel(payload.motif),
        )

    def _valider_ajustement(self, payload: AjustementStockPayload) -> AjustementStockPayload:
        if not isinstance(payload.nouvelle_quantite, int) or payload.nouvelle_quantite < 0:
            raise ValidationError("La quantite ajustee ne peut pas etre negative.")
        motif = self._normaliser_texte_optionnel(payload.motif)
        if motif is None:
            raise ValidationError("Le motif d'ajustement est obligatoire.")
        return AjustementStockPayload(
            lot_id=payload.lot_id,
            nouvelle_quantite=payload.nouvelle_quantite,
            motif=motif,
        )

    @staticmethod
    def _normaliser_date(valeur: str | None) -> str | None:
        valeur_normalisee = StockService._normaliser_texte_optionnel(valeur)
        if valeur_normalisee is None:
            return None
        try:
            return date.fromisoformat(valeur_normalisee).isoformat()
        except ValueError as exc:
            raise ValidationError("La date d'expiration doit etre au format AAAA-MM-JJ.") from exc

    @staticmethod
    def _normaliser_texte_optionnel(valeur: str | None) -> str | None:
        if valeur is None:
            return None
        valeur_normalisee = valeur.strip()
        return valeur_normalisee or None


def _statut_lot_export(
    *,
    quantite: int,
    stock_total: int,
    stock_minimum: int,
    expiration: date | None,
    today: date,
    near_limit: date,
) -> str:
    if expiration is not None and expiration < today:
        return "Expire"
    if quantite == 0:
        return "Epuise"
    if expiration is not None and expiration <= near_limit:
        return "Expiration proche"
    if stock_total <= stock_minimum:
        return "Stock faible"
    return "Disponible"
