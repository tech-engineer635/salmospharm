import re

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.core.constants import ACTION_CODE_RECUPERATION_GENERE, ACTION_COMPTE_GERANT_CREE
from app.core.exceptions import PremierGerantExisteDejaError, ValidationError
from app.core.security import verifier_code_recuperation, verifier_mot_de_passe
from app.database.connection import create_app_engine
from app.database.init_db import init_database
from app.database.models import JournalActivite, Utilisateur
from app.services.auth_service import AuthService


def test_creer_premier_gerant_hash_mot_de_passe_et_code(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    service = AuthService(session_factory=SessionLocal)

    result = service.creer_premier_gerant(
        nom_complet="Gerant Principal",
        identifiant="gerant",
        mot_de_passe="Secret123",
        confirmation_mot_de_passe="Secret123",
    )

    with SessionLocal() as session:
        utilisateur = session.execute(select(Utilisateur)).scalar_one()

    engine.dispose()

    assert result.utilisateur_id == utilisateur.id
    assert re.fullmatch(r"SALMOS-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}", result.code_recuperation)
    assert utilisateur.nom == "Gerant Principal"
    assert utilisateur.email == "gerant"
    assert utilisateur.role == "GERANT"
    assert utilisateur.actif == 1
    assert utilisateur.mot_de_passe_hash != "Secret123"
    assert utilisateur.code_recuperation_hash != result.code_recuperation
    assert verifier_mot_de_passe("Secret123", utilisateur.mot_de_passe_hash)
    assert verifier_code_recuperation(result.code_recuperation, utilisateur.code_recuperation_hash)


def test_creer_premier_gerant_journalise_les_actions_sensibles(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    service = AuthService(session_factory=SessionLocal)

    result = service.creer_premier_gerant(
        nom_complet="Gerant Principal",
        identifiant="gerant",
        mot_de_passe="Secret123",
        confirmation_mot_de_passe="Secret123",
    )

    with SessionLocal() as session:
        journaux = session.execute(
            select(JournalActivite).order_by(JournalActivite.id.asc())
        ).scalars().all()

    engine.dispose()

    assert [journal.action for journal in journaux] == [
        ACTION_COMPTE_GERANT_CREE,
        ACTION_CODE_RECUPERATION_GENERE,
    ]
    assert all(journal.utilisateur_id == result.utilisateur_id for journal in journaux)
    assert all(journal.table_cible == "utilisateurs" for journal in journaux)
    assert all(journal.element_id == result.utilisateur_id for journal in journaux)
    assert result.code_recuperation not in " ".join(journal.details or "" for journal in journaux)


def test_creer_premier_gerant_refuse_double_creation(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    service = AuthService(session_factory=SessionLocal)

    service.creer_premier_gerant(
        nom_complet="Gerant Principal",
        identifiant="gerant",
        mot_de_passe="Secret123",
        confirmation_mot_de_passe="Secret123",
    )

    with pytest.raises(PremierGerantExisteDejaError):
        service.creer_premier_gerant(
            nom_complet="Autre Gerant",
            identifiant="autre",
            mot_de_passe="Secret123",
            confirmation_mot_de_passe="Secret123",
        )

    engine.dispose()


def test_creer_premier_gerant_refuse_admin_admin(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    service = AuthService(session_factory=SessionLocal)

    with pytest.raises(ValidationError):
        service.creer_premier_gerant(
            nom_complet="Admin",
            identifiant="admin",
            mot_de_passe="admin",
            confirmation_mot_de_passe="admin",
        )

    engine.dispose()


def _create_test_session_factory(tmp_path):
    database_path = tmp_path / "salmospharm.sqlite3"
    engine = create_app_engine(database_path)
    init_database(database_engine=engine)
    return engine, sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )
