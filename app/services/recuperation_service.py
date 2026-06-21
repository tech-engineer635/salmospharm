"""Service de generation et validation du code de recuperation."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.security import (
    generer_code_recuperation,
    hasher_code_recuperation,
    verifier_code_recuperation,
)


@dataclass(frozen=True)
class CodeRecuperationCree:
    code: str
    code_hash: str


class RecuperationService:
    def generer_code_hash(self) -> CodeRecuperationCree:
        code = generer_code_recuperation()
        return CodeRecuperationCree(code=code, code_hash=hasher_code_recuperation(code))

    def verifier_code(self, code: str, code_hash: str) -> bool:
        return verifier_code_recuperation(code, code_hash)
