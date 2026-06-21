"""Exceptions applicatives propres de SALMOSPHARM."""

from __future__ import annotations


class SalmospharmError(Exception):
    """Erreur applicative de base."""


class ValidationError(SalmospharmError):
    """Erreur de validation metier ou formulaire."""


class UtilisateurExisteDejaError(ValidationError):
    """Erreur levee quand un utilisateur existe deja."""


class PremierGerantExisteDejaError(ValidationError):
    """Erreur levee si le premier compte gerant a deja ete cree."""
