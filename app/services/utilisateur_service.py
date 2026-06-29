"""Service metier de gestion des comptes vendeurs."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.constants import (
    ACTION_CODE_RECUPERATION_GENERE,
    ACTION_CONNEXION_REUSSIE,
    ACTION_UTILISATEUR_CREE,
    ACTION_UTILISATEUR_DESACTIVE,
    ACTION_UTILISATEUR_MODIFIE,
    ACTION_UTILISATEUR_REACTIVE,
    ROLE_VENDEUR,
)
from app.core.exceptions import UtilisateurExisteDejaError, UtilisateurInactifError, ValidationError
from app.core.permissions import (
    PERMISSION_CREER_VENDEUR,
    PERMISSION_DESACTIVER_UTILISATEUR,
    PERMISSION_MODIFIER_UTILISATEUR,
    PERMISSION_CONSULTER_TOUTES_VENTES,
    exiger_permission,
)
from app.core.security import hasher_mot_de_passe
from app.database.connection import create_session
from app.database.models import Utilisateur
from app.repositories.journal_repository import JournalRepository
from app.repositories.utilisateur_repository import UtilisateurRepository
from app.repositories.vente_repository import VenteRepository
from app.services.auth_service import SessionUtilisateur
from app.services.journal_service import JournalService
from app.services.recuperation_service import RecuperationService


@dataclass(frozen=True)
class VendeurPayload:
    nom_complet: str
    identifiant: str
    mot_de_passe: str


@dataclass(frozen=True)
class ModificationVendeurPayload:
    nom_complet: str
    identifiant: str
    nouveau_mot_de_passe: str = ""


@dataclass(frozen=True)
class CreationVendeurResult:
    utilisateur_id: int
    code_recuperation: str


@dataclass(frozen=True)
class VendeurListItem:
    utilisateur_id: int
    nom: str
    identifiant: str
    actif: bool
    derniere_connexion: str | None
    ventes_du_jour: int


@dataclass(frozen=True)
class VendeurMetrics:
    total_vendeurs: int
    actifs: int
    inactifs: int
    ventes_du_jour: int


@dataclass(frozen=True)
class VendeurDashboardData:
    vendeurs: list[VendeurListItem]
    metrics: VendeurMetrics


class UtilisateurService:
    """Gere les vendeurs sans exposer SQLAlchemy a l'interface gerant."""

    def __init__(
        self,
        session_factory: Callable[[], Session] = create_session,
        utilisateur_repository: UtilisateurRepository | None = None,
        vente_repository: VenteRepository | None = None,
        journal_repository: JournalRepository | None = None,
        journal_service: JournalService | None = None,
        recuperation_service: RecuperationService | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._utilisateur_repository = utilisateur_repository or UtilisateurRepository()
        self._vente_repository = vente_repository or VenteRepository()
        self._journal_repository = journal_repository or JournalRepository()
        self._journal_service = journal_service or JournalService()
        self._recuperation_service = recuperation_service or RecuperationService()

    def tableau_vendeurs(
        self,
        utilisateur: SessionUtilisateur,
        *,
        terme: str = "",
        date_reference: date | None = None,
    ) -> VendeurDashboardData:
        exiger_permission(utilisateur.role, PERMISSION_CONSULTER_TOUTES_VENTES)
        reference = date_reference or date.today()
        with self._session_factory() as session:
            vendeurs = self._utilisateur_repository.rechercher_par_role(
                session,
                role=ROLE_VENDEUR,
                terme=terme,
            )
            items = [self._build_item(session, vendeur, reference) for vendeur in vendeurs]
            tous_les_vendeurs = self._utilisateur_repository.lister_par_role(session, ROLE_VENDEUR)
            metrics = VendeurMetrics(
                total_vendeurs=len(tous_les_vendeurs),
                actifs=sum(1 for vendeur in tous_les_vendeurs if vendeur.actif == 1),
                inactifs=sum(1 for vendeur in tous_les_vendeurs if vendeur.actif != 1),
                ventes_du_jour=sum(self._total_vendeur_du_jour(session, vendeur.id, reference) for vendeur in tous_les_vendeurs),
            )
            return VendeurDashboardData(vendeurs=items, metrics=metrics)

    def creer_vendeur(self, utilisateur: SessionUtilisateur, payload: VendeurPayload) -> CreationVendeurResult:
        exiger_permission(utilisateur.role, PERMISSION_CREER_VENDEUR)
        donnees = self._valider_payload(payload)
        with self._session_factory() as session:
            if self._utilisateur_repository.existe_par_email(session, donnees.identifiant):
                raise UtilisateurExisteDejaError("Cet identifiant est deja utilise.")

            code_recuperation = self._recuperation_service.generer_code_hash()
            vendeur = Utilisateur(
                nom=donnees.nom_complet,
                email=donnees.identifiant,
                mot_de_passe_hash=hasher_mot_de_passe(donnees.mot_de_passe),
                code_recuperation_hash=code_recuperation.code_hash,
                doit_changer_mot_de_passe=0,
                role=ROLE_VENDEUR,
                actif=1,
            )
            try:
                self._utilisateur_repository.creer(session, vendeur)
                self._journal_service.journaliser(
                    session,
                    action=ACTION_UTILISATEUR_CREE,
                    utilisateur_id=utilisateur.utilisateur_id,
                    table_cible="utilisateurs",
                    element_id=vendeur.id,
                    details=f"Vendeur cree: {vendeur.email}.",
                )
                self._journal_service.journaliser(
                    session,
                    action=ACTION_CODE_RECUPERATION_GENERE,
                    utilisateur_id=utilisateur.utilisateur_id,
                    table_cible="utilisateurs",
                    element_id=vendeur.id,
                    details="Code de recuperation vendeur genere et affiche une seule fois.",
                )
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise ValidationError("Impossible de creer le vendeur.") from exc

            return CreationVendeurResult(utilisateur_id=vendeur.id, code_recuperation=code_recuperation.code)

    def desactiver_vendeur(self, utilisateur: SessionUtilisateur, *, vendeur_id: int) -> None:
        exiger_permission(utilisateur.role, PERMISSION_DESACTIVER_UTILISATEUR)
        with self._session_factory() as session:
            vendeur = self._obtenir_vendeur(session, vendeur_id)
            if vendeur.actif != 1:
                raise UtilisateurInactifError("Ce vendeur est deja desactive.")
            self._utilisateur_repository.desactiver(session, vendeur)
            self._journal_service.journaliser(
                session,
                action=ACTION_UTILISATEUR_DESACTIVE,
                utilisateur_id=utilisateur.utilisateur_id,
                table_cible="utilisateurs",
                element_id=vendeur.id,
                details=f"Vendeur desactive: {vendeur.email}.",
            )
            session.commit()

    def modifier_vendeur(
        self,
        utilisateur: SessionUtilisateur,
        *,
        vendeur_id: int,
        payload: ModificationVendeurPayload,
    ) -> None:
        exiger_permission(utilisateur.role, PERMISSION_MODIFIER_UTILISATEUR)
        nom = payload.nom_complet.strip()
        identifiant = payload.identifiant.strip().lower()
        if not nom:
            raise ValidationError("Le nom complet est obligatoire.")
        if not identifiant:
            raise ValidationError("L'identifiant est obligatoire.")
        if payload.nouveau_mot_de_passe and len(payload.nouveau_mot_de_passe) < 5:
            raise ValidationError(
                "Le nouveau mot de passe doit contenir au moins 5 caracteres."
            )
        with self._session_factory() as session:
            vendeur = self._obtenir_vendeur(session, vendeur_id)
            existant = self._utilisateur_repository.chercher_par_email(
                session, identifiant
            )
            if existant is not None and existant.id != vendeur.id:
                raise UtilisateurExisteDejaError("Cet identifiant est deja utilise.")
            vendeur.nom = nom
            vendeur.email = identifiant
            if payload.nouveau_mot_de_passe:
                vendeur.mot_de_passe_hash = hasher_mot_de_passe(
                    payload.nouveau_mot_de_passe
                )
            self._utilisateur_repository.mettre_a_jour(session, vendeur)
            self._journal_service.journaliser(
                session,
                action=ACTION_UTILISATEUR_MODIFIE,
                utilisateur_id=utilisateur.utilisateur_id,
                table_cible="utilisateurs",
                element_id=vendeur.id,
                details=f"Vendeur modifie: {vendeur.email}.",
            )
            session.commit()

    def reactiver_vendeur(self, utilisateur: SessionUtilisateur, *, vendeur_id: int) -> None:
        exiger_permission(utilisateur.role, PERMISSION_MODIFIER_UTILISATEUR)
        with self._session_factory() as session:
            vendeur = self._obtenir_vendeur(session, vendeur_id)
            if vendeur.actif == 1:
                raise ValidationError("Ce vendeur est deja actif.")
            self._utilisateur_repository.reactiver(session, vendeur)
            self._journal_service.journaliser(
                session,
                action=ACTION_UTILISATEUR_REACTIVE,
                utilisateur_id=utilisateur.utilisateur_id,
                table_cible="utilisateurs",
                element_id=vendeur.id,
                details=f"Vendeur reactive: {vendeur.email}.",
            )
            session.commit()

    def _build_item(self, session: Session, vendeur: Utilisateur, reference: date) -> VendeurListItem:
        return VendeurListItem(
            utilisateur_id=vendeur.id,
            nom=vendeur.nom,
            identifiant=vendeur.email,
            actif=vendeur.actif == 1,
            derniere_connexion=self._derniere_connexion(session, vendeur.id),
            ventes_du_jour=self._total_vendeur_du_jour(session, vendeur.id, reference),
        )

    def _derniere_connexion(self, session: Session, utilisateur_id: int) -> str | None:
        journaux = self._journal_repository.lister_par_utilisateur(session, utilisateur_id, limite=20)
        for journal in journaux:
            if journal.action == ACTION_CONNEXION_REUSSIE:
                return journal.cree_le
        return None

    def _total_vendeur_du_jour(self, session: Session, vendeur_id: int, reference: date) -> int:
        prefix = reference.isoformat()
        ventes = self._vente_repository.lister_par_vendeur(session, vendeur_id)
        return sum(vente.total for vente in ventes if vente.cree_le.startswith(prefix))

    def _obtenir_vendeur(self, session: Session, vendeur_id: int) -> Utilisateur:
        vendeur = self._utilisateur_repository.chercher_par_id(session, vendeur_id)
        if vendeur is None or vendeur.role != ROLE_VENDEUR:
            raise ValidationError("Vendeur introuvable.")
        return vendeur

    def _valider_payload(self, payload: VendeurPayload) -> VendeurPayload:
        nom = payload.nom_complet.strip()
        identifiant = payload.identifiant.strip().lower()
        if not nom:
            raise ValidationError("Le nom complet est obligatoire.")
        if not identifiant:
            raise ValidationError("L'identifiant est obligatoire.")
        if not payload.mot_de_passe:
            raise ValidationError("Le mot de passe est obligatoire.")
        if identifiant == "admin" and payload.mot_de_passe.lower() == "admin":
            raise ValidationError("Le compte admin/admin est interdit.")
        if len(payload.mot_de_passe) < 5:
            raise ValidationError("Le mot de passe doit contenir au moins 5 caracteres.")
        return VendeurPayload(nom_complet=nom, identifiant=identifiant, mot_de_passe=payload.mot_de_passe)
