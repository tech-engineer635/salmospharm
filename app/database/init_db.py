"""Initialisation de la base SQLite SALMOSPHARM."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from app.core.paths import ensure_app_directories
from app.database.connection import create_app_engine, engine
from app.database.models import Base
from app.database.seed import seed_initial_data


def init_database(database_path: Path | None = None, database_engine: Engine | None = None) -> None:
    target_engine = database_engine
    if target_engine is None:
        if database_path is None:
            ensure_app_directories()
        else:
            database_path.parent.mkdir(parents=True, exist_ok=True)

        target_engine = create_app_engine(database_path) if database_path else engine

    with target_engine.begin() as connection:
        Base.metadata.create_all(bind=connection)
        _migrate_alertes(connection)
        seed_initial_data(connection)


def _migrate_alertes(connection: Connection) -> None:
    """Ajoute sans perte les colonnes d'alertes introduites apres la base initiale."""

    colonnes = {
        row[1]
        for row in connection.exec_driver_sql("PRAGMA table_info(alertes)").fetchall()
    }
    ajouts = {
        "est_active": "INTEGER NOT NULL DEFAULT 1 CHECK (est_active IN (0, 1))",
        "derniere_detection_le": "TEXT",
        "resolue_le": "TEXT",
    }
    for nom, definition in ajouts.items():
        if nom not in colonnes:
            connection.exec_driver_sql(
                f"ALTER TABLE alertes ADD COLUMN {nom} {definition}"
            )
    connection.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_alertes_est_active "
            "ON alertes(est_active)"
        )
    )
