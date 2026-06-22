"""Exceptions applicatives propres de SALMOSPHARM."""

from __future__ import annotations


class SalmospharmError(Exception):
    """Erreur applicative de base."""


class ValidationError(SalmospharmError):
    """Erreur de validation metier ou formulaire."""


class PermissionRefuseeError(SalmospharmError):
    """Erreur levee quand un role tente une action interdite."""


class StockInsuffisantError(ValidationError):
    """Erreur levee quand le stock vendable ne couvre pas la demande."""


class ProduitExpireError(ValidationError):
    """Erreur levee quand un produit ou lot expire est utilise pour vendre."""


class ProduitInactifError(ValidationError):
    """Erreur levee quand un produit inactif est utilise dans une action metier."""


class UtilisateurInactifError(ValidationError):
    """Erreur levee quand un utilisateur desactive tente d'utiliser l'application."""


class BackupInvalideError(ValidationError):
    """Erreur levee quand un fichier de sauvegarde ne respecte pas le format attendu."""


class ImprimanteIndisponibleError(SalmospharmError):
    """Erreur levee quand l'impression thermique ne peut pas aboutir."""


class AuthentificationError(ValidationError):
    """Erreur levee quand l'identite de l'utilisateur ne peut pas etre confirmee."""


class UtilisateurExisteDejaError(ValidationError):
    """Erreur levee quand un utilisateur existe deja."""


class PremierGerantExisteDejaError(ValidationError):
    """Erreur levee si le premier compte gerant a deja ete cree."""
