"""Configuration SQLAlchemy pour la base SQLite locale."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.paths import get_database_path


def _build_sqlite_url(database_path: Path) -> str:
    return f"sqlite:///{database_path.as_posix()}"


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_app_engine(database_path: Path | None = None, echo: bool = False) -> Engine:
    path = database_path or get_database_path()

    return create_engine(
        _build_sqlite_url(path),
        echo=echo,
        future=True,
    )


engine = create_app_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


def create_session() -> Session:
    return SessionLocal()
