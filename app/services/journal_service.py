"""Service de journalisation des actions sensibles."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.constants import ACTIONS_JOURNAL
from app.core.exceptions import ValidationError
from app.database.models import JournalActivite
from app.repositories.journal_repository import JournalRepository


class JournalService:
    """Enregistre les actions metier importantes dans `journaux_activite`."""

    def __init__(self, journal_repository: JournalRepository | None = None) -> None:
        self._journal_repository = journal_repository or JournalRepository()

    def journaliser(
        self,
        session: Session,
        *,
        action: str,
        utilisateur_id: int | None = None,
        table_cible: str | None = None,
        element_id: int | None = None,
        details: str | None = None,
    ) -> JournalActivite:
        """Cree une entree de journal dans la transaction SQLAlchemy en cours."""
        if action not in ACTIONS_JOURNAL:
            raise ValidationError("Action de journalisation inconnue.")

        journal = JournalActivite(
            utilisateur_id=utilisateur_id,
            action=action,
            table_cible=table_cible,
            element_id=element_id,
            details=details,
        )
        return self._journal_repository.creer(session, journal)
