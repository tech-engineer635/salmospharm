"""Service des parametres generaux de la pharmacie."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.constants import ACTION_PARAMETRES_MODIFIES
from app.core.exceptions import ValidationError
from app.core.permissions import (
    PERMISSION_CONSULTER_PARAMETRES,
    PERMISSION_MODIFIER_PARAMETRES,
    exiger_permission,
)
from app.database.connection import create_session
from app.repositories.parametre_repository import ParametreRepository
from app.services.auth_service import SessionUtilisateur
from app.services.journal_service import JournalService


@dataclass(frozen=True)
class ParametresGeneraux:
    nom_pharmacie: str
    telephone: str
    adresse: str
    seuil_expiration_jours: int
    nom_imprimante: str
    largeur_ticket: int
    impression_auto: bool


class ParametreService:
    def __init__(
        self,
        session_factory=create_session,
        repository: ParametreRepository | None = None,
        journal_service: JournalService | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._repository = repository or ParametreRepository()
        self._journal_service = journal_service or JournalService()

    def obtenir(self, utilisateur: SessionUtilisateur) -> ParametresGeneraux:
        exiger_permission(utilisateur.role, PERMISSION_CONSULTER_PARAMETRES)
        with self._session_factory() as session:
            valeur = self._repository.obtenir_principal(session)
            if valeur is None:
                raise ValidationError("Les parametres sont introuvables.")
            return ParametresGeneraux(
                nom_pharmacie=valeur.nom_pharmacie,
                telephone=valeur.telephone or "",
                adresse=valeur.adresse or "",
                seuil_expiration_jours=valeur.seuil_expiration_jours,
                nom_imprimante=valeur.nom_imprimante or "",
                largeur_ticket=valeur.largeur_ticket,
                impression_auto=valeur.impression_auto == 1,
            )

    def enregistrer(
        self, utilisateur: SessionUtilisateur, valeurs: ParametresGeneraux
    ) -> None:
        exiger_permission(utilisateur.role, PERMISSION_MODIFIER_PARAMETRES)
        nom = valeurs.nom_pharmacie.strip()
        if not nom:
            raise ValidationError("Le nom de la pharmacie est obligatoire.")
        if valeurs.seuil_expiration_jours <= 0:
            raise ValidationError("Le seuil d'expiration doit etre positif.")
        if valeurs.largeur_ticket not in {58, 80}:
            raise ValidationError("La largeur du ticket doit etre 58 ou 80 mm.")
        with self._session_factory() as session:
            parametre = self._repository.obtenir_principal(session)
            if parametre is None:
                raise ValidationError("Les parametres sont introuvables.")
            self._repository.mettre_a_jour_general(
                session,
                parametre,
                nom_pharmacie=nom,
                telephone=valeurs.telephone.strip() or None,
                adresse=valeurs.adresse.strip() or None,
                seuil_expiration_jours=valeurs.seuil_expiration_jours,
                nom_imprimante=valeurs.nom_imprimante.strip() or None,
                largeur_ticket=valeurs.largeur_ticket,
                impression_auto=valeurs.impression_auto,
            )
            self._journal_service.journaliser(
                session,
                action=ACTION_PARAMETRES_MODIFIES,
                utilisateur_id=utilisateur.utilisateur_id,
                table_cible="parametres",
                element_id=parametre.id,
                details="Parametres generaux et d'impression modifies.",
            )
            session.commit()
