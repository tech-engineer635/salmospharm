"""File d'evenements legere pour la reconciliation des alertes."""

from __future__ import annotations

from queue import Empty, Queue
from threading import Lock


_events: Queue[int | None] = Queue()
_pending: set[int | None] = set()
_lock = Lock()


def publier_evenement_alerte(produit_id: int | None = None) -> None:
    """Publie un produit a verifier en evitant les doublons en attente."""

    with _lock:
        if produit_id in _pending:
            return
        _pending.add(produit_id)
        _events.put(produit_id)


def depiler_evenements_alertes() -> set[int | None]:
    """Vide la file et libere les cles pour de futures publications."""

    elements: set[int | None] = set()
    while True:
        try:
            elements.add(_events.get_nowait())
        except Empty:
            break
    with _lock:
        _pending.difference_update(elements)
    return elements
