from sqlalchemy import text

from app.database.connection import create_app_engine
from app.database.init_db import init_database


def test_init_database_creates_sqlite_file_and_enables_foreign_keys(tmp_path):
    database_path = tmp_path / "salmospharm.sqlite3"
    database_engine = create_app_engine(database_path)

    init_database(database_engine=database_engine)

    assert database_path.exists()

    with database_engine.connect() as connection:
        foreign_keys_enabled = connection.execute(text("PRAGMA foreign_keys")).scalar_one()
        table_names = connection.execute(
            text("SELECT name FROM sqlite_master WHERE type = 'table'")
        ).scalars().all()

    database_engine.dispose()

    assert foreign_keys_enabled == 1
    assert table_names == []
    assert "modes_paiement" not in table_names
    assert "factures" not in table_names
    assert "rapports" not in table_names
