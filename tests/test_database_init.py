import pytest
from sqlalchemy import insert, text
from sqlalchemy.exc import IntegrityError

from app.database.connection import create_app_engine
from app.database.init_db import init_database
from app.database.models import Parametre, Utilisateur, Vente


AUTHORIZED_TABLES = {
    "utilisateurs",
    "categories",
    "produits",
    "lots_produits",
    "mouvements_stock",
    "ventes",
    "lignes_vente",
    "alertes",
    "journaux_activite",
    "parametres",
}

FORBIDDEN_TABLES = {
    "modes_paiement",
    "paiements",
    "factures",
    "rapports",
    "clients",
    "fournisseurs",
}


def test_init_database_creates_official_schema_and_seed_data(tmp_path):
    database_path = tmp_path / "salmospharm.sqlite3"
    database_engine = create_app_engine(database_path)

    init_database(database_engine=database_engine)

    assert database_path.exists()

    with database_engine.connect() as connection:
        foreign_keys_enabled = connection.execute(text("PRAGMA foreign_keys")).scalar_one()
        table_names = connection.execute(
            text("SELECT name FROM sqlite_master WHERE type = 'table'")
        ).scalars().all()
        category_names = connection.execute(text("SELECT nom FROM categories ORDER BY nom")).scalars().all()
        parametres = connection.execute(
            text(
                """
                SELECT nom_pharmacie, devise, seuil_expiration_jours, largeur_ticket,
                       impression_auto, sauvegarde_auto, frequence_sauvegarde
                FROM parametres
                """
            )
        ).mappings().all()
        utilisateurs_count = connection.execute(text("SELECT COUNT(*) FROM utilisateurs")).scalar_one()
        produits_columns = connection.execute(text("PRAGMA table_info(produits)")).mappings().all()
        ventes_columns = connection.execute(text("PRAGMA table_info(ventes)")).mappings().all()
        index_names = connection.execute(
            text("SELECT name FROM sqlite_master WHERE type = 'index'")
        ).scalars().all()

    database_engine.dispose()

    assert foreign_keys_enabled == 1
    assert AUTHORIZED_TABLES.issubset(set(table_names))
    assert not FORBIDDEN_TABLES.intersection(table_names)

    assert category_names == [
        "Antalgiques",
        "Antibiotiques",
        "Antipaludeens",
        "Antiseptiques",
        "Vitamines",
    ]
    assert parametres == [
        {
            "nom_pharmacie": "SALMOSPHARM 133",
            "devise": "CDF",
            "seuil_expiration_jours": 30,
            "largeur_ticket": 80,
            "impression_auto": 1,
            "sauvegarde_auto": 1,
            "frequence_sauvegarde": "QUOTIDIENNE",
        }
    ]
    assert utilisateurs_count == 0

    assert _column_type(produits_columns, "prix_vente") == "INTEGER"
    assert _column_type(ventes_columns, "total") == "INTEGER"
    assert _column_type(ventes_columns, "montant_recu") == "INTEGER"

    assert "idx_produits_nom" in index_names
    assert "idx_lots_produits_expiration" in index_names
    assert "idx_ventes_numero" in index_names
    assert "idx_journaux_action" in index_names


def test_init_database_is_idempotent_for_seed_data(tmp_path):
    database_path = tmp_path / "salmospharm.sqlite3"
    database_engine = create_app_engine(database_path)

    init_database(database_engine=database_engine)
    init_database(database_engine=database_engine)

    with database_engine.connect() as connection:
        categories_count = connection.execute(text("SELECT COUNT(*) FROM categories")).scalar_one()
        parametres_count = connection.execute(text("SELECT COUNT(*) FROM parametres")).scalar_one()

    database_engine.dispose()

    assert categories_count == 5
    assert parametres_count == 1


def test_database_rejects_invalid_core_constraints(tmp_path):
    database_path = tmp_path / "salmospharm.sqlite3"
    database_engine = create_app_engine(database_path)
    init_database(database_engine=database_engine)

    with pytest.raises(IntegrityError):
        with database_engine.begin() as connection:
            connection.execute(
                insert(Utilisateur).values(
                    nom="Test",
                    email="test@example.local",
                    mot_de_passe_hash="hash",
                    role="ADMIN",
                )
            )

    with pytest.raises(IntegrityError):
        with database_engine.begin() as connection:
            connection.execute(insert(Parametre).values(nom_pharmacie="Test", devise="USD"))

    with pytest.raises(IntegrityError):
        with database_engine.begin() as connection:
            connection.execute(
                insert(Vente).values(
                    numero_vente="VTE-2026-000001",
                    total=1000,
                    montant_recu=999,
                    statut="VALIDEE",
                )
            )

    with pytest.raises(IntegrityError):
        with database_engine.begin() as connection:
            connection.execute(
                insert(Vente).values(
                    numero_vente="VTE-2026-000002",
                    total=1000,
                    montant_recu=1000,
                    statut="ANNULEE",
                )
            )

    database_engine.dispose()


def _column_type(columns, column_name: str) -> str:
    return next(column["type"] for column in columns if column["name"] == column_name)
