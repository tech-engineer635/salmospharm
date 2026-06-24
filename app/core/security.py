"""Fonctions de securite locale pour les comptes utilisateurs."""

from __future__ import annotations

import secrets
import string

from passlib.context import CryptContext
from passlib.exc import PasswordTruncateError, PasswordValueError

from app.core.exceptions import ValidationError


_RECOVERY_ALPHABET = string.ascii_uppercase + string.digits
_BCRYPT_CONTEXT = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=True,
)


def hasher_mot_de_passe(mot_de_passe: str) -> str:
    return _hash_bcrypt(mot_de_passe)


def verifier_mot_de_passe(mot_de_passe: str, mot_de_passe_hash: str) -> bool:
    return _verify_bcrypt(mot_de_passe, mot_de_passe_hash)


def generer_code_recuperation() -> str:
    blocs = ["".join(secrets.choice(_RECOVERY_ALPHABET) for _ in range(4)) for _ in range(3)]
    return "SALMOS-" + "-".join(blocs)


def hasher_code_recuperation(code_recuperation: str) -> str:
    return _hash_bcrypt(code_recuperation)


def verifier_code_recuperation(code_recuperation: str, code_recuperation_hash: str) -> bool:
    return _verify_bcrypt(code_recuperation, code_recuperation_hash)


def _hash_bcrypt(secret: str) -> str:
    """Hash un secret avec passlib/bcrypt sans tronquer silencieusement."""
    try:
        return _BCRYPT_CONTEXT.hash(secret)
    except (PasswordTruncateError, PasswordValueError) as exc:
        raise ValidationError("Le secret depasse la longueur maximale autorisee.") from exc


def _verify_bcrypt(secret: str, secret_hash: str) -> bool:
    """Verifie un secret via passlib et refuse les hash invalides proprement."""
    try:
        return bool(_BCRYPT_CONTEXT.verify(secret, secret_hash))
    except (PasswordTruncateError, PasswordValueError, ValueError, TypeError):
        return False
