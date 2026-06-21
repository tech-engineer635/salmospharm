"""Fonctions de securite locale pour les comptes utilisateurs."""

from __future__ import annotations

import secrets
import string

import bcrypt

from app.core.exceptions import ValidationError


_RECOVERY_ALPHABET = string.ascii_uppercase + string.digits
_BCRYPT_MAX_BYTES = 72


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
    secret_bytes = _to_bcrypt_bytes(secret)
    return bcrypt.hashpw(secret_bytes, bcrypt.gensalt()).decode("utf-8")


def _verify_bcrypt(secret: str, secret_hash: str) -> bool:
    secret_bytes = _to_bcrypt_bytes(secret)
    return bcrypt.checkpw(secret_bytes, secret_hash.encode("utf-8"))


def _to_bcrypt_bytes(secret: str) -> bytes:
    secret_bytes = secret.encode("utf-8")
    if len(secret_bytes) > _BCRYPT_MAX_BYTES:
        raise ValidationError("Le secret depasse la longueur maximale autorisee.")
    return secret_bytes
