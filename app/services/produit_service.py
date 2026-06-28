"""Service metier de gestion des produits et categories."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.constants import (
    ACTION_EXPORT_EXCEL,
    ACTION_PRODUIT_CREE,
    ACTION_PRODUIT_DESACTIVE,
    ACTION_PRODUIT_MODIFIE,
)
from app.core.exceptions import ProduitInactifError, ValidationError
from app.core.paths import get_exports_dir
from app.core.permissions import (
    PERMISSION_CREER_PRODUIT,
    PERMISSION_DESACTIVER_PRODUIT,
    PERMISSION_MODIFIER_PRODUIT,
    PERMISSION_RECHERCHER_PRODUITS,
    PERMISSION_EXPORTER_DONNEES,
    exiger_permission,
)
from app.database.connection import create_session
from app.database.models import Categorie, Produit
from app.repositories.categorie_repository import CategorieRepository
from app.repositories.produit_repository import ProduitRepository
from app.services.auth_service import SessionUtilisateur
from app.services.journal_service import JournalService
from app.utils.excel import convertir_datetime, creer_classeur_tableau, enregistrer_classeur


@dataclass(frozen=True)
class ProduitPayload:
    """Donnees validees pour creer ou modifier une fiche produit."""

    nom: str
    prix_vente: int
    categorie_id: int | None = None
    code_barres: str | None = None
    stock_minimum: int = 0
    description: str | None = None


class ProduitService:
    """Porte les regles catalogue sans exposer SQLAlchemy a l'interface."""

    def __init__(
        self,
        session_factory: Callable[[], Session] = create_session,
        produit_repository: ProduitRepository | None = None,
        categorie_repository: CategorieRepository | None = None,
        journal_service: JournalService | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._produit_repository = produit_repository or ProduitRepository()
        self._categorie_repository = categorie_repository or CategorieRepository()
        self._journal_service = journal_service or JournalService()

    def lister_categories(self, utilisateur: SessionUtilisateur) -> list[Categorie]:
        exiger_permission(utilisateur.role, PERMISSION_RECHERCHER_PRODUITS)
        with self._session_factory() as session:
            return self._categorie_repository.lister(session)

    def rechercher_produits(
        self,
        utilisateur: SessionUtilisateur,
        *,
        terme: str = "",
        categorie_id: int | None = None,
        actifs_seulement: bool = False,
    ) -> list[Produit]:
        exiger_permission(utilisateur.role, PERMISSION_RECHERCHER_PRODUITS)
        with self._session_factory() as session:
            return self._produit_repository.rechercher(
                session,
                terme=terme.strip(),
                categorie_id=categorie_id,
                actifs_seulement=actifs_seulement,
            )

    def exporter_excel(
        self,
        utilisateur: SessionUtilisateur,
        *,
        destination: str | Path | None = None,
        terme: str = "",
        categorie_id: int | None = None,
        statut: str = "TOUS",
        stock_minimum_positif: bool = False,
    ) -> Path:
        exiger_permission(utilisateur.role, PERMISSION_EXPORTER_DONNEES)
        with self._session_factory() as session:
            rows = list(
                self._produit_repository.donnees_export(
                    session,
                    terme=terme,
                    categorie_id=categorie_id,
                    statut=statut,
                )
            )
            if stock_minimum_positif:
                rows = [row for row in rows if int(row[5]) > 0]
            workbook, count = creer_classeur_tableau(
                titre_feuille="Produits",
                entetes=(
                    "Code",
                    "Nom du produit",
                    "Categorie",
                    "Code-barres",
                    "Prix de vente (CDF)",
                    "Stock minimum",
                    "Statut",
                    "Date de creation",
                    "Derniere modification",
                ),
                lignes=(
                    (
                        f"PRD-{row[0]:05d}",
                        row[1],
                        row[2] or "Sans categorie",
                        row[3] or "",
                        int(row[4]),
                        int(row[5]),
                        "Actif" if row[6] == 1 else "Desactive",
                        convertir_datetime(row[7]),
                        convertir_datetime(row[8]),
                    )
                    for row in rows
                ),
                colonnes_cdf=(5,),
                colonnes_datetime=(8, 9),
            )
            path = enregistrer_classeur(
                workbook,
                destination or get_exports_dir() / f"produits_{date.today().isoformat()}.xlsx",
            )
            self._journal_service.journaliser(
                session,
                action=ACTION_EXPORT_EXCEL,
                utilisateur_id=utilisateur.utilisateur_id,
                table_cible="produits",
                details=f"Export Excel produits : {path.name}, {count} ligne(s).",
            )
            session.commit()
        return path

    def creer_categorie(
        self,
        utilisateur: SessionUtilisateur,
        *,
        nom: str,
        description: str | None = None,
    ) -> Categorie:
        exiger_permission(utilisateur.role, PERMISSION_CREER_PRODUIT)
        nom_normalise = self._normaliser_texte_obligatoire(nom, "Le nom de la categorie est obligatoire.")
        description_normalisee = self._normaliser_texte_optionnel(description)

        with self._session_factory() as session:
            if self._categorie_repository.chercher_par_nom(session, nom_normalise) is not None:
                raise ValidationError("Cette categorie existe deja.")

            categorie = Categorie(nom=nom_normalise, description=description_normalisee)
            try:
                self._categorie_repository.creer(session, categorie)
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise ValidationError("Impossible de creer la categorie.") from exc

            return categorie

    def creer_produit(self, utilisateur: SessionUtilisateur, payload: ProduitPayload) -> Produit:
        exiger_permission(utilisateur.role, PERMISSION_CREER_PRODUIT)
        donnees = self._valider_payload(payload)

        with self._session_factory() as session:
            self._verifier_categorie(session, donnees.categorie_id)
            self._verifier_code_barres_unique(session, donnees.code_barres)

            produit = Produit(
                categorie_id=donnees.categorie_id,
                nom=donnees.nom,
                code_barres=donnees.code_barres,
                prix_vente=donnees.prix_vente,
                stock_minimum=donnees.stock_minimum,
                description=donnees.description,
                actif=1,
            )

            try:
                self._produit_repository.creer(session, produit)
                self._journal_service.journaliser(
                    session,
                    action=ACTION_PRODUIT_CREE,
                    utilisateur_id=utilisateur.utilisateur_id,
                    table_cible="produits",
                    element_id=produit.id,
                    details=f"Produit cree: {produit.nom}.",
                )
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise ValidationError("Impossible de creer le produit.") from exc

            return produit

    def modifier_produit(
        self,
        utilisateur: SessionUtilisateur,
        *,
        produit_id: int,
        payload: ProduitPayload,
    ) -> Produit:
        exiger_permission(utilisateur.role, PERMISSION_MODIFIER_PRODUIT)
        donnees = self._valider_payload(payload)

        with self._session_factory() as session:
            produit = self._obtenir_produit(session, produit_id)
            if produit.actif != 1:
                raise ProduitInactifError("Ce produit est desactive.")

            self._verifier_categorie(session, donnees.categorie_id)
            self._verifier_code_barres_unique(session, donnees.code_barres, produit_id_a_ignorer=produit.id)

            produit.nom = donnees.nom
            produit.categorie_id = donnees.categorie_id
            produit.code_barres = donnees.code_barres
            produit.prix_vente = donnees.prix_vente
            produit.stock_minimum = donnees.stock_minimum
            produit.description = donnees.description

            try:
                self._produit_repository.mettre_a_jour(session, produit)
                self._journal_service.journaliser(
                    session,
                    action=ACTION_PRODUIT_MODIFIE,
                    utilisateur_id=utilisateur.utilisateur_id,
                    table_cible="produits",
                    element_id=produit.id,
                    details=f"Produit modifie: {produit.nom}.",
                )
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise ValidationError("Impossible de modifier le produit.") from exc

            return produit

    def desactiver_produit(self, utilisateur: SessionUtilisateur, *, produit_id: int) -> Produit:
        exiger_permission(utilisateur.role, PERMISSION_DESACTIVER_PRODUIT)

        with self._session_factory() as session:
            produit = self._obtenir_produit(session, produit_id)
            if produit.actif != 1:
                raise ProduitInactifError("Ce produit est deja desactive.")

            produit = self._produit_repository.desactiver(session, produit)
            self._journal_service.journaliser(
                session,
                action=ACTION_PRODUIT_DESACTIVE,
                utilisateur_id=utilisateur.utilisateur_id,
                table_cible="produits",
                element_id=produit.id,
                details=f"Produit desactive: {produit.nom}.",
            )
            session.commit()
            return produit

    def reactiver_produit(self, utilisateur: SessionUtilisateur, *, produit_id: int) -> Produit:
        exiger_permission(utilisateur.role, PERMISSION_MODIFIER_PRODUIT)

        with self._session_factory() as session:
            produit = self._obtenir_produit(session, produit_id)
            if produit.actif == 1:
                raise ValidationError("Ce produit est deja actif.")

            produit = self._produit_repository.reactiver(session, produit)
            self._journal_service.journaliser(
                session,
                action=ACTION_PRODUIT_MODIFIE,
                utilisateur_id=utilisateur.utilisateur_id,
                table_cible="produits",
                element_id=produit.id,
                details=f"Produit reactive: {produit.nom}.",
            )
            session.commit()
            return produit

    def _valider_payload(self, payload: ProduitPayload) -> ProduitPayload:
        """Applique les validations Phase 11 avant toute ecriture catalogue."""
        nom = self._normaliser_texte_obligatoire(payload.nom, "Le nom du produit est obligatoire.")
        code_barres = self._normaliser_texte_optionnel(payload.code_barres)
        description = self._normaliser_texte_optionnel(payload.description)

        if not isinstance(payload.prix_vente, int):
            raise ValidationError("Le prix de vente doit etre un montant entier en CDF.")
        if payload.prix_vente < 0:
            raise ValidationError("Le prix de vente ne peut pas etre negatif.")
        if not isinstance(payload.stock_minimum, int):
            raise ValidationError("Le stock minimum doit etre un nombre entier.")
        if payload.stock_minimum < 0:
            raise ValidationError("Le stock minimum ne peut pas etre negatif.")

        return ProduitPayload(
            nom=nom,
            prix_vente=payload.prix_vente,
            categorie_id=payload.categorie_id,
            code_barres=code_barres,
            stock_minimum=payload.stock_minimum,
            description=description,
        )

    def _verifier_categorie(self, session: Session, categorie_id: int | None) -> None:
        if categorie_id is None:
            return
        if self._categorie_repository.chercher_par_id(session, categorie_id) is None:
            raise ValidationError("Categorie invalide.")

    def _verifier_code_barres_unique(
        self,
        session: Session,
        code_barres: str | None,
        *,
        produit_id_a_ignorer: int | None = None,
    ) -> None:
        if not code_barres:
            return
        produit_existant = self._produit_repository.chercher_par_code_barres(session, code_barres)
        if produit_existant is not None and produit_existant.id != produit_id_a_ignorer:
            raise ValidationError("Ce code-barres est deja utilise.")

    def _obtenir_produit(self, session: Session, produit_id: int) -> Produit:
        produit = self._produit_repository.chercher_par_id(session, produit_id)
        if produit is None:
            raise ValidationError("Produit introuvable.")
        return produit

    @staticmethod
    def _normaliser_texte_obligatoire(valeur: str, message: str) -> str:
        valeur_normalisee = valeur.strip()
        if not valeur_normalisee:
            raise ValidationError(message)
        return valeur_normalisee

    @staticmethod
    def _normaliser_texte_optionnel(valeur: str | None) -> str | None:
        if valeur is None:
            return None
        valeur_normalisee = valeur.strip()
        return valeur_normalisee or None
