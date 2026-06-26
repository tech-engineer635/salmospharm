from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.core.constants import (
    ACTION_UTILISATEUR_CREE,
    ACTION_UTILISATEUR_DESACTIVE,
    ACTION_UTILISATEUR_REACTIVE,
    ROLE_GERANT,
    ROLE_VENDEUR,
)
from app.core.exceptions import PermissionRefuseeError, UtilisateurExisteDejaError, ValidationError
from app.core.security import verifier_code_recuperation, verifier_mot_de_passe
from app.database.connection import create_app_engine
from app.database.init_db import init_database
from app.database.models import JournalActivite, Utilisateur, Vente
from app.services.auth_service import SessionUtilisateur
from app.services.utilisateur_service import UtilisateurService, VendeurPayload


def test_creer_vendeur_hash_mot_de_passe_code_et_journalise(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    gerant = _creer_session_utilisateur(SessionLocal, ROLE_GERANT)
    service = UtilisateurService(session_factory=SessionLocal)

    result = service.creer_vendeur(
        gerant,
        VendeurPayload(nom_complet="Jean K.", identifiant="Jean.K", mot_de_passe="Secret123"),
    )

    with SessionLocal() as session:
        vendeur = session.get(Utilisateur, result.utilisateur_id)
        journaux = session.execute(select(JournalActivite).order_by(JournalActivite.id.asc())).scalars().all()

    engine.dispose()

    assert vendeur.nom == "Jean K."
    assert vendeur.email == "jean.k"
    assert vendeur.role == ROLE_VENDEUR
    assert vendeur.actif == 1
    assert vendeur.mot_de_passe_hash != "Secret123"
    assert verifier_mot_de_passe("Secret123", vendeur.mot_de_passe_hash)
    assert verifier_code_recuperation(result.code_recuperation, vendeur.code_recuperation_hash)
    assert ACTION_UTILISATEUR_CREE in [journal.action for journal in journaux]


def test_creer_vendeur_refuse_doublon_admin_admin_et_role_non_autorise(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    gerant = _creer_session_utilisateur(SessionLocal, ROLE_GERANT)
    vendeur = _creer_session_utilisateur(SessionLocal, ROLE_VENDEUR)
    service = UtilisateurService(session_factory=SessionLocal)

    service.creer_vendeur(
        gerant,
        VendeurPayload(nom_complet="Jean K.", identifiant="jean", mot_de_passe="abcde"),
    )

    with pytest.raises(UtilisateurExisteDejaError):
        service.creer_vendeur(
            gerant,
            VendeurPayload(nom_complet="Jean Bis", identifiant="jean", mot_de_passe="abcde"),
        )

    with pytest.raises(ValidationError):
        service.creer_vendeur(
            gerant,
            VendeurPayload(nom_complet="Admin", identifiant="admin", mot_de_passe="admin"),
        )

    with pytest.raises(PermissionRefuseeError):
        service.creer_vendeur(
            vendeur,
            VendeurPayload(nom_complet="Alice", identifiant="alice", mot_de_passe="abcde"),
        )

    engine.dispose()


def test_desactiver_et_reactiver_vendeur(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    gerant = _creer_session_utilisateur(SessionLocal, ROLE_GERANT)
    vendeur_id = _creer_vendeur_db(SessionLocal, nom="Alice M.", email="alice")
    service = UtilisateurService(session_factory=SessionLocal)

    service.desactiver_vendeur(gerant, vendeur_id=vendeur_id)
    service.reactiver_vendeur(gerant, vendeur_id=vendeur_id)

    with SessionLocal() as session:
        vendeur = session.get(Utilisateur, vendeur_id)
        actions = [journal.action for journal in session.execute(select(JournalActivite)).scalars().all()]

    engine.dispose()

    assert vendeur.actif == 1
    assert ACTION_UTILISATEUR_DESACTIVE in actions
    assert ACTION_UTILISATEUR_REACTIVE in actions


def test_tableau_vendeurs_retourne_metriques_et_ventes_du_jour(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    gerant = _creer_session_utilisateur(SessionLocal, ROLE_GERANT)
    jean_id = _creer_vendeur_db(SessionLocal, nom="Jean K.", email="jean")
    alice_id = _creer_vendeur_db(SessionLocal, nom="Alice M.", email="alice", actif=0)
    _creer_vente(SessionLocal, vendeur_id=jean_id, total=1500, cree_le="2026-06-26 10:00:00")
    _creer_vente(SessionLocal, vendeur_id=jean_id, total=500, cree_le="2026-06-25 10:00:00")
    service = UtilisateurService(session_factory=SessionLocal)

    data = service.tableau_vendeurs(gerant, date_reference=date(2026, 6, 26))

    engine.dispose()

    assert data.metrics.total_vendeurs == 2
    assert data.metrics.actifs == 1
    assert data.metrics.inactifs == 1
    assert data.metrics.ventes_du_jour == 1500
    assert [(item.utilisateur_id, item.ventes_du_jour, item.actif) for item in data.vendeurs] == [
        (alice_id, 0, False),
        (jean_id, 1500, True),
    ]


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


def _creer_session_utilisateur(SessionLocal, role: str) -> SessionUtilisateur:
    with SessionLocal() as session:
        utilisateur = Utilisateur(
            nom=f"Utilisateur {role}",
            email=f"{role.lower()}-service@test.local",
            mot_de_passe_hash="hash",
            role=role,
            actif=1,
        )
        session.add(utilisateur)
        session.commit()
        return SessionUtilisateur(
            utilisateur_id=utilisateur.id,
            nom=utilisateur.nom,
            identifiant=utilisateur.email,
            role=utilisateur.role,
        )


def _creer_vendeur_db(SessionLocal, *, nom: str, email: str, actif: int = 1) -> int:
    with SessionLocal() as session:
        vendeur = Utilisateur(
            nom=nom,
            email=email,
            mot_de_passe_hash="hash",
            role=ROLE_VENDEUR,
            actif=actif,
        )
        session.add(vendeur)
        session.commit()
        return vendeur.id


def _creer_vente(SessionLocal, *, vendeur_id: int, total: int, cree_le: str) -> int:
    with SessionLocal() as session:
        vente = Vente(
            numero_vente=f"VTE-{vendeur_id}-{total}",
            vendeur_id=vendeur_id,
            total=total,
            montant_recu=total,
            statut="VALIDEE",
            cree_le=cree_le,
        )
        session.add(vente)
        session.commit()
        return vente.id
