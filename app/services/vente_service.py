"""Service metier de validation des ventes definitives."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.constants import ACTION_VENTE_VALIDEE, STATUT_VENTE_VALIDEE, TYPE_MOUVEMENT_SORTIE
from app.core.exceptions import ProduitInactifError, SalmospharmError, StockInsuffisantError, UtilisateurInactifError, ValidationError
from app.core.permissions import PERMISSION_CREER_VENTE, PERMISSION_RECHERCHER_PRODUITS, exiger_permission
from app.database.connection import create_session
from app.database.models import LigneVente, MouvementStock, Vente
from app.repositories.categorie_repository import CategorieRepository
from app.repositories.lot_produit_repository import LotProduitRepository
from app.repositories.produit_repository import ProduitRepository
from app.repositories.stock_repository import StockRepository
from app.repositories.utilisateur_repository import UtilisateurRepository
from app.repositories.vente_repository import VenteRepository
from app.services.alerte_service import AlerteService
from app.services.alert_events import publier_evenement_alerte
from app.services.auth_service import SessionUtilisateur
from app.services.journal_service import JournalService


@dataclass(frozen=True)
class LignePanierPayload:
    """Ligne panier recue depuis l'interface avant validation."""

    produit_id: int
    quantite: int


@dataclass(frozen=True)
class VentePayload:
    """Donnees de paiement et panier pour une vente especes en CDF."""

    lignes: list[LignePanierPayload]
    montant_recu: int


@dataclass(frozen=True)
class ProduitVendable:
    """Produit vendable affiche dans le point de vente."""

    produit_id: int
    nom: str
    prix_vente: int
    stock_disponible: int
    categorie_id: int | None
    categorie_nom: str | None
    description: str | None


@dataclass(frozen=True)
class LigneVenteResult:
    produit_id: int
    produit_nom: str
    lot_id: int
    numero_lot: str | None
    quantite: int
    prix_unitaire: int
    sous_total: int


@dataclass(frozen=True)
class VenteResult:
    vente_id: int
    numero_vente: str
    total: int
    montant_recu: int
    monnaie_rendue: int
    lignes: list[LigneVenteResult]


@dataclass(frozen=True)
class _PlanLot:
    lot_id: int
    numero_lot: str | None
    quantite: int


@dataclass(frozen=True)
class _PlanProduit:
    produit_id: int
    produit_nom: str
    prix_unitaire: int
    quantite: int
    lots: list[_PlanLot]


class VenteService:
    """Valide les ventes atomiques en appliquant FEFO dans la couche metier."""

    def __init__(
        self,
        session_factory: Callable[[], Session] = create_session,
        produit_repository: ProduitRepository | None = None,
        categorie_repository: CategorieRepository | None = None,
        lot_repository: LotProduitRepository | None = None,
        stock_repository: StockRepository | None = None,
        utilisateur_repository: UtilisateurRepository | None = None,
        vente_repository: VenteRepository | None = None,
        alerte_service: AlerteService | None = None,
        journal_service: JournalService | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._produit_repository = produit_repository or ProduitRepository()
        self._categorie_repository = categorie_repository or CategorieRepository()
        self._lot_repository = lot_repository or LotProduitRepository()
        self._stock_repository = stock_repository or StockRepository()
        self._utilisateur_repository = utilisateur_repository or UtilisateurRepository()
        self._vente_repository = vente_repository or VenteRepository()
        self._alerte_service = alerte_service or AlerteService(stock_repository=self._stock_repository)
        self._journal_service = journal_service or JournalService()

    def lister_produits_vendables(
        self,
        utilisateur: SessionUtilisateur,
        *,
        terme: str = "",
        categorie_id: int | None = None,
        date_reference: date | None = None,
    ) -> list[ProduitVendable]:
        """Retourne les produits actifs avec stock vendable, sans exposer les lots a l'UI."""
        exiger_permission(utilisateur.role, PERMISSION_RECHERCHER_PRODUITS)
        reference = date_reference or date.today()
        with self._session_factory() as session:
            categories = {categorie.id: categorie.nom for categorie in self._categorie_repository.lister(session)}
            produits = self._produit_repository.rechercher(
                session,
                terme=terme,
                categorie_id=categorie_id,
                actifs_seulement=True,
            )
            cards: list[ProduitVendable] = []
            for produit in produits:
                stock = self._stock_repository.calculer_stock_disponible(
                    session,
                    produit.id,
                    reference.isoformat(),
                )
                if stock <= 0:
                    continue
                cards.append(
                    ProduitVendable(
                        produit_id=produit.id,
                        nom=produit.nom,
                        prix_vente=produit.prix_vente,
                        stock_disponible=stock,
                        categorie_id=produit.categorie_id,
                        categorie_nom=categories.get(produit.categorie_id),
                        description=produit.description,
                    )
                )
            return cards

    def valider_vente(
        self,
        utilisateur: SessionUtilisateur,
        payload: VentePayload,
        *,
        date_reference: date | None = None,
    ) -> VenteResult:
        """Cree la vente, les lignes et les sorties de stock en une transaction.

        L'interface fournit uniquement un panier et le montant recu. Le service
        recalcule les prix, choisit les lots FEFO et refuse toute vente partielle.
        """
        exiger_permission(utilisateur.role, PERMISSION_CREER_VENTE)
        lignes_groupees = self._valider_lignes(payload.lignes)
        if not isinstance(payload.montant_recu, int) or payload.montant_recu < 0:
            raise ValidationError("Le montant recu doit etre un entier CDF positif.")

        reference = date_reference or date.today()
        with self._session_factory() as session:
            self._exiger_utilisateur_actif(session, utilisateur)
            try:
                plan = self._preparer_plan(session, lignes_groupees, reference)
                total = sum(item.prix_unitaire * item.quantite for item in plan)
                if payload.montant_recu < total:
                    raise ValidationError("Le montant recu est insuffisant.")

                numero_vente = self._generer_numero_vente(session, reference)
                vente = self._vente_repository.creer_vente(
                    session,
                    Vente(
                        numero_vente=numero_vente,
                        vendeur_id=utilisateur.utilisateur_id,
                        total=total,
                        montant_recu=payload.montant_recu,
                        statut=STATUT_VENTE_VALIDEE,
                    ),
                )

                result_lignes: list[LigneVenteResult] = []
                for item in plan:
                    for selection in item.lots:
                        lot = self._lot_repository.chercher_par_id(session, selection.lot_id)
                        if lot is None:
                            raise ValidationError("Lot introuvable.")
                        if lot.quantite < selection.quantite:
                            raise StockInsuffisantError("Stock insuffisant pour ce produit.")

                        lot.quantite -= selection.quantite
                        self._lot_repository.mettre_a_jour(session, lot)
                        sous_total = item.prix_unitaire * selection.quantite
                        self._vente_repository.creer_ligne(
                            session,
                            LigneVente(
                                vente_id=vente.id,
                                produit_id=item.produit_id,
                                lot_id=lot.id,
                                quantite=selection.quantite,
                                prix_unitaire=item.prix_unitaire,
                                sous_total=sous_total,
                            ),
                        )
                        self._stock_repository.creer_mouvement(
                            session,
                            MouvementStock(
                                produit_id=item.produit_id,
                                lot_id=lot.id,
                                utilisateur_id=utilisateur.utilisateur_id,
                                type_mouvement=TYPE_MOUVEMENT_SORTIE,
                                quantite=selection.quantite,
                                motif=f"Vente {numero_vente}",
                            ),
                        )
                        produit = self._produit_repository.chercher_par_id(session, item.produit_id)
                        if produit is not None:
                            self._alerte_service.generer_alertes_pour_lot(
                                session,
                                produit=produit,
                                lot=lot,
                                date_reference=reference,
                            )
                        result_lignes.append(
                            LigneVenteResult(
                                produit_id=item.produit_id,
                                produit_nom=item.produit_nom,
                                lot_id=lot.id,
                                numero_lot=lot.numero_lot,
                                quantite=selection.quantite,
                                prix_unitaire=item.prix_unitaire,
                                sous_total=sous_total,
                            )
                        )

                self._journal_service.journaliser(
                    session,
                    action=ACTION_VENTE_VALIDEE,
                    utilisateur_id=utilisateur.utilisateur_id,
                    table_cible="ventes",
                    element_id=vente.id,
                    details=f"Vente {numero_vente} validee pour {total} CDF.",
                )
                session.commit()
                for produit_id in lignes_groupees:
                    publier_evenement_alerte(produit_id)
                return VenteResult(
                    vente_id=vente.id,
                    numero_vente=numero_vente,
                    total=total,
                    montant_recu=payload.montant_recu,
                    monnaie_rendue=payload.montant_recu - total,
                    lignes=result_lignes,
                )
            except SalmospharmError:
                session.rollback()
                raise
            except IntegrityError as exc:
                session.rollback()
                raise ValidationError("Impossible de valider la vente.") from exc

    def _exiger_utilisateur_actif(self, session: Session, utilisateur: SessionUtilisateur) -> None:
        """Confirme en base que la session peut encore valider une vente."""
        utilisateur_db = self._utilisateur_repository.chercher_par_id(session, utilisateur.utilisateur_id)
        if utilisateur_db is None or utilisateur_db.actif != 1:
            raise UtilisateurInactifError("Ce compte est desactive. Veuillez contacter le gerant.")

    def _preparer_plan(
        self,
        session: Session,
        lignes_groupees: dict[int, int],
        date_reference: date,
    ) -> list[_PlanProduit]:
        plan: list[_PlanProduit] = []
        for produit_id, quantite in lignes_groupees.items():
            produit = self._produit_repository.chercher_par_id(session, produit_id)
            if produit is None:
                raise ValidationError("Produit introuvable.")
            if produit.actif != 1:
                raise ProduitInactifError("Ce produit est desactive et ne peut pas etre vendu.")
            if produit.prix_vente < 0:
                raise ValidationError("Prix unitaire invalide.")

            lots = self._lot_repository.lister_disponibles_par_produit(
                session,
                produit_id=produit.id,
                date_reference=date_reference.isoformat(),
            )
            reste = quantite
            selections: list[_PlanLot] = []
            for lot in lots:
                if reste <= 0:
                    break
                quantite_prise = min(lot.quantite, reste)
                selections.append(_PlanLot(lot_id=lot.id, numero_lot=lot.numero_lot, quantite=quantite_prise))
                reste -= quantite_prise
            if reste > 0:
                raise StockInsuffisantError("Stock insuffisant pour ce produit.")
            plan.append(
                _PlanProduit(
                    produit_id=produit.id,
                    produit_nom=produit.nom,
                    prix_unitaire=produit.prix_vente,
                    quantite=quantite,
                    lots=selections,
                )
            )
        return plan

    def _generer_numero_vente(self, session: Session, date_reference: date) -> str:
        dernier = self._vente_repository.dernier_numero_pour_annee(session, date_reference.year)
        prochain = 1
        if dernier:
            try:
                prochain = int(dernier.rsplit("-", 1)[1]) + 1
            except (IndexError, ValueError):
                prochain = 1
        return f"VTE-{date_reference.year}-{prochain:06d}"

    @staticmethod
    def _valider_lignes(lignes: list[LignePanierPayload]) -> dict[int, int]:
        if not lignes:
            raise ValidationError("Le panier est vide.")
        lignes_groupees: dict[int, int] = {}
        for ligne in lignes:
            if not isinstance(ligne.produit_id, int):
                raise ValidationError("Produit invalide dans le panier.")
            if not isinstance(ligne.quantite, int) or ligne.quantite <= 0:
                raise ValidationError("La quantite vendue doit etre superieure a zero.")
            lignes_groupees[ligne.produit_id] = lignes_groupees.get(ligne.produit_id, 0) + ligne.quantite
        return lignes_groupees
