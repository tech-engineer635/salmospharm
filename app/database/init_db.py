"""Initialisation de la base SQLite SALMOSPHARM."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.engine import Engine

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
        seed_initial_data(connection)
