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
    ACTION_MOT_DE_PASSE_REINITIALISE,
    ROLE_GERANT,
)
from app.core.exceptions import (
    AuthentificationError,
    PremierGerantExisteDejaError,
    UtilisateurExisteDejaError,
    UtilisateurInactifError,
    ValidationError,
)
from app.core.permissions import exiger_role_valide
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
class RecuperationCompteResult:
    utilisateur_id: int
    nouveau_code_recuperation: str


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
                    raison="compte_trouve=non; actif=non_verifie; hash_valide=non_verifie",
                )
                session.commit()
                raise AuthentificationError("Identifiant ou mot de passe incorrect.")

            if utilisateur.actif != 1:
                self._journaliser_connexion_echouee(
                    session,
                    utilisateur_id=utilisateur.id,
                    identifiant=identifiant_normalise,
                    raison="compte_trouve=oui; actif=non; hash_valide=non_verifie",
                )
                session.commit()
                raise UtilisateurInactifError("Ce compte est desactive. Veuillez contacter le gerant.")

            if not verifier_mot_de_passe(mot_de_passe, utilisateur.mot_de_passe_hash):
                self._journaliser_connexion_echouee(
                    session,
                    utilisateur_id=utilisateur.id,
                    identifiant=identifiant_normalise,
                    raison="compte_trouve=oui; actif=oui; hash_valide=non",
                )
                session.commit()
                raise AuthentificationError("Identifiant ou mot de passe incorrect.")

            exiger_role_valide(utilisateur.role)
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

    def reinitialiser_mot_de_passe(
        self,
        *,
        identifiant: str,
        code_recuperation: str,
        nouveau_mot_de_passe: str,
        confirmation_mot_de_passe: str,
    ) -> RecuperationCompteResult:
        """Reinitialise le compte et remplace le code utilise dans une transaction."""

        identifiant_normalise = identifiant.strip().lower()
        if not identifiant_normalise:
            raise ValidationError("L'identifiant est obligatoire.")
        if not code_recuperation.strip():
            raise ValidationError("Le code de recuperation est obligatoire.")
        if nouveau_mot_de_passe != confirmation_mot_de_passe:
            raise ValidationError("La confirmation ne correspond pas au mot de passe.")
        if len(nouveau_mot_de_passe) < 5:
            raise ValidationError("Le mot de passe doit contenir au moins 5 caracteres.")

        with self._session_factory() as session:
            utilisateur = self._utilisateur_repository.chercher_par_email(
                session, identifiant_normalise
            )
            if (
                utilisateur is None
                or utilisateur.role != ROLE_GERANT
                or not utilisateur.code_recuperation_hash
                or not self._recuperation_service.verifier_code(
                    code_recuperation.strip(), utilisateur.code_recuperation_hash
                )
            ):
                raise AuthentificationError(
                    "Identifiant ou code de recuperation incorrect."
                )
            if utilisateur.actif != 1:
                raise UtilisateurInactifError(
                    "Ce compte est desactive. Veuillez contacter le gerant."
                )

            nouveau_code = self._recuperation_service.generer_code_hash()
            self._utilisateur_repository.mettre_a_jour_securite(
                session,
                utilisateur,
                mot_de_passe_hash=hasher_mot_de_passe(nouveau_mot_de_passe),
                code_recuperation_hash=nouveau_code.code_hash,
            )
            self._journal_service.journaliser(
                session,
                action=ACTION_MOT_DE_PASSE_REINITIALISE,
                utilisateur_id=utilisateur.id,
                table_cible="utilisateurs",
                element_id=utilisateur.id,
                details="Mot de passe reinitialise avec le code de recuperation.",
            )
            self._journal_service.journaliser(
                session,
                action=ACTION_CODE_RECUPERATION_GENERE,
                utilisateur_id=utilisateur.id,
                table_cible="utilisateurs",
                element_id=utilisateur.id,
                details="Nouveau code de recuperation genere apres reinitialisation.",
            )
            session.commit()
            return RecuperationCompteResult(
                utilisateur_id=utilisateur.id,
                nouveau_code_recuperation=nouveau_code.code,
            )

    def changer_mot_de_passe(
        self,
        utilisateur_connecte: SessionUtilisateur,
        *,
        mot_de_passe_actuel: str,
        nouveau_mot_de_passe: str,
        confirmation: str,
    ) -> None:
        if nouveau_mot_de_passe != confirmation:
            raise ValidationError("La confirmation ne correspond pas au mot de passe.")
        if len(nouveau_mot_de_passe) < 5:
            raise ValidationError("Le mot de passe doit contenir au moins 5 caracteres.")
        with self._session_factory() as session:
            utilisateur = self._utilisateur_repository.chercher_par_id(
                session, utilisateur_connecte.utilisateur_id
            )
            if utilisateur is None or not verifier_mot_de_passe(
                mot_de_passe_actuel, utilisateur.mot_de_passe_hash
            ):
                raise AuthentificationError("Le mot de passe actuel est incorrect.")
            utilisateur.mot_de_passe_hash = hasher_mot_de_passe(nouveau_mot_de_passe)
            self._utilisateur_repository.mettre_a_jour(session, utilisateur)
            self._journal_service.journaliser(
                session,
                action=ACTION_MOT_DE_PASSE_REINITIALISE,
                utilisateur_id=utilisateur.id,
                table_cible="utilisateurs",
                element_id=utilisateur.id,
                details="Mot de passe modifie depuis les parametres.",
            )
            session.commit()

    def regenerer_code_recuperation(
        self, utilisateur_connecte: SessionUtilisateur, *, mot_de_passe: str
    ) -> str:
        with self._session_factory() as session:
            utilisateur = self._utilisateur_repository.chercher_par_id(
                session, utilisateur_connecte.utilisateur_id
            )
            if utilisateur is None or not verifier_mot_de_passe(
                mot_de_passe, utilisateur.mot_de_passe_hash
            ):
                raise AuthentificationError("Le mot de passe actuel est incorrect.")
            code = self._recuperation_service.generer_code_hash()
            utilisateur.code_recuperation_hash = code.code_hash
            self._utilisateur_repository.mettre_a_jour(session, utilisateur)
            self._journal_service.journaliser(
                session,
                action=ACTION_CODE_RECUPERATION_GENERE,
                utilisateur_id=utilisateur.id,
                table_cible="utilisateurs",
                element_id=utilisateur.id,
                details="Code de recuperation regenere depuis les parametres.",
            )
            session.commit()
            return code.code

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
