"""Service d'authentification et de premier lancement."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.constants import (
    ACTION_CODE_RECUPERATION_GENERE,
    ACTION_COMPTE_GERANT_CREE,
    ACTION_CONNEXION_ECHOUEE,
    ACTION_CONNEXION_REUSSIE,
    ROLE_GERANT,
)
from app.core.exceptions import (
    AuthentificationError,
    PremierGerantExisteDejaError,
    UtilisateurExisteDejaError,
    UtilisateurInactifError,
    ValidationError,
)
from app.core.security import hasher_mot_de_passe, verifier_mot_de_passe
from app.database.connection import create_session
from app.database.models import Utilisateur
from app.repositories.utilisateur_repository import UtilisateurRepository
from app.services.journal_service import JournalService
from app.services.recuperation_service import RecuperationService


@dataclass(frozen=True)
class CreationGerantResult:
    utilisateur_id: int
    code_recuperation: str


@dataclass(frozen=True)
class SessionUtilisateur:
    """Representation memoire de l'utilisateur connecte, sans donnees sensibles."""

    utilisateur_id: int
    nom: str
    identifiant: str
    role: str


class AuthService:
    def __init__(
        self,
        session_factory: Callable[[], Session] = create_session,
        utilisateur_repository: UtilisateurRepository | None = None,
        recuperation_service: RecuperationService | None = None,
        journal_service: JournalService | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._utilisateur_repository = utilisateur_repository or UtilisateurRepository()
        self._recuperation_service = recuperation_service or RecuperationService()
        self._journal_service = journal_service or JournalService()

    def existe_utilisateur(self) -> bool:
        with self._session_factory() as session:
            return self._utilisateur_repository.compter(session) > 0

    def connecter(self, *, identifiant: str, mot_de_passe: str) -> SessionUtilisateur:
        """Authentifie un utilisateur et journalise chaque tentative de connexion."""
        identifiant_normalise = identifiant.strip().lower()
        self._valider_demande_connexion(identifiant=identifiant_normalise, mot_de_passe=mot_de_passe)

        with self._session_factory() as session:
            utilisateur = self._utilisateur_repository.chercher_par_email(session, identifiant_normalise)

            if utilisateur is None:
                self._journaliser_connexion_echouee(
                    session,
                    utilisateur_id=None,
                    identifiant=identifiant_normalise,
                    raison="identifiant inconnu",
                )
                session.commit()
                raise AuthentificationError("Identifiant ou mot de passe incorrect.")

            if utilisateur.actif != 1:
                self._journaliser_connexion_echouee(
                    session,
                    utilisateur_id=utilisateur.id,
                    identifiant=identifiant_normalise,
                    raison="compte desactive",
                )
                session.commit()
                raise UtilisateurInactifError("Ce compte est desactive. Veuillez contacter le gerant.")

            if not verifier_mot_de_passe(mot_de_passe, utilisateur.mot_de_passe_hash):
                self._journaliser_connexion_echouee(
                    session,
                    utilisateur_id=utilisateur.id,
                    identifiant=identifiant_normalise,
                    raison="mot de passe incorrect",
                )
                session.commit()
                raise AuthentificationError("Identifiant ou mot de passe incorrect.")

            self._journal_service.journaliser(
                session,
                action=ACTION_CONNEXION_REUSSIE,
                utilisateur_id=utilisateur.id,
                table_cible="utilisateurs",
                element_id=utilisateur.id,
                details=f"Connexion reussie pour l'identifiant {utilisateur.email}.",
            )
            session.commit()

            return SessionUtilisateur(
                utilisateur_id=utilisateur.id,
                nom=utilisateur.nom,
                identifiant=utilisateur.email,
                role=utilisateur.role,
            )

    def creer_premier_gerant(
        self,
        *,
        nom_complet: str,
        identifiant: str,
        mot_de_passe: str,
        confirmation_mot_de_passe: str,
    ) -> CreationGerantResult:
        nom_normalise = nom_complet.strip()
        identifiant_normalise = identifiant.strip().lower()
        self._valider_creation_gerant(
            nom_complet=nom_normalise,
            identifiant=identifiant_normalise,
            mot_de_passe=mot_de_passe,
            confirmation_mot_de_passe=confirmation_mot_de_passe,
        )

        with self._session_factory() as session:
            if self._utilisateur_repository.compter(session) > 0:
                raise PremierGerantExisteDejaError("Le premier compte gerant existe deja.")

            if self._utilisateur_repository.existe_par_email(session, identifiant_normalise):
                raise UtilisateurExisteDejaError("Cet identifiant est deja utilise.")

            code_recuperation = self._recuperation_service.generer_code_hash()
            utilisateur = Utilisateur(
                nom=nom_normalise,
                email=identifiant_normalise,
                mot_de_passe_hash=hasher_mot_de_passe(mot_de_passe),
                code_recuperation_hash=code_recuperation.code_hash,
                doit_changer_mot_de_passe=0,
                role=ROLE_GERANT,
                actif=1,
            )

            try:
                self._utilisateur_repository.creer(session, utilisateur)
                self._journaliser_creation_premier_gerant(session, utilisateur)
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise ValidationError("Impossible de creer le compte gerant.") from exc

            return CreationGerantResult(
                utilisateur_id=utilisateur.id,
                code_recuperation=code_recuperation.code,
            )

    def _valider_creation_gerant(
        self,
        *,
        nom_complet: str,
        identifiant: str,
        mot_de_passe: str,
        confirmation_mot_de_passe: str,
    ) -> None:
        if not nom_complet:
            raise ValidationError("Le nom complet est obligatoire.")

        if not identifiant:
            raise ValidationError("Le nom d'utilisateur est obligatoire.")

        if not mot_de_passe:
            raise ValidationError("Le mot de passe est obligatoire.")

        if mot_de_passe != confirmation_mot_de_passe:
            raise ValidationError("La confirmation ne correspond pas au mot de passe.")

        if identifiant == "admin" and mot_de_passe.lower() == "admin":
            raise ValidationError("Le compte admin/admin est interdit.")

        if len(mot_de_passe) < 5:
            raise ValidationError("Le mot de passe doit contenir au moins 5 caracteres.")

    def _valider_demande_connexion(self, *, identifiant: str, mot_de_passe: str) -> None:
        """Bloque les tentatives incompletes avant tout acces metier."""
        if not identifiant:
            raise ValidationError("L'identifiant est obligatoire.")

        if not mot_de_passe:
            raise ValidationError("Le mot de passe est obligatoire.")

    def _journaliser_creation_premier_gerant(self, session: Session, utilisateur: Utilisateur) -> None:
        """Trace les actions sensibles du premier lancement dans la meme transaction."""
        self._journal_service.journaliser(
            session,
            action=ACTION_COMPTE_GERANT_CREE,
            utilisateur_id=utilisateur.id,
            table_cible="utilisateurs",
            element_id=utilisateur.id,
            details=f"Premier compte gerant cree pour l'identifiant {utilisateur.email}.",
        )
        self._journal_service.journaliser(
            session,
            action=ACTION_CODE_RECUPERATION_GENERE,
            utilisateur_id=utilisateur.id,
            table_cible="utilisateurs",
            element_id=utilisateur.id,
            details="Code de recuperation genere et affiche une seule fois.",
        )

    def _journaliser_connexion_echouee(
        self,
        session: Session,
        *,
        utilisateur_id: int | None,
        identifiant: str,
        raison: str,
    ) -> None:
        """Trace un echec de connexion sans enregistrer le mot de passe saisi."""
        self._journal_service.journaliser(
            session,
            action=ACTION_CONNEXION_ECHOUEE,
            utilisateur_id=utilisateur_id,
            table_cible="utilisateurs",
            element_id=utilisateur_id,
            details=f"Connexion echouee pour l'identifiant {identifiant}: {raison}.",
        )
