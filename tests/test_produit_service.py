import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.core.constants import (
    ACTION_PRODUIT_CREE,
    ACTION_PRODUIT_DESACTIVE,
    ACTION_PRODUIT_MODIFIE,
    ROLE_GERANT,
    ROLE_VENDEUR,
)
from app.core.exceptions import PermissionRefuseeError, ValidationError
from app.database.connection import create_app_engine
from app.database.init_db import init_database
from app.database.models import JournalActivite, Produit, Utilisateur
from app.services.auth_service import SessionUtilisateur
from app.services.produit_service import ProduitPayload, ProduitService


def test_creer_categorie_et_produit_journalise_action(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    gerant = _creer_utilisateur(SessionLocal, ROLE_GERANT)
    service = ProduitService(session_factory=SessionLocal)

    categorie = service.creer_categorie(gerant, nom=" Tests antalgiques ", description="Douleur")
    produit = service.creer_produit(
        gerant,
        ProduitPayload(
            nom=" Paracetamol 500mg ",
            code_barres="PARA-001",
            categorie_id=categorie.id,
            prix_vente=1500,
            stock_minimum=5,
            description="Comprime",
        ),
    )

    with SessionLocal() as session:
        journal = session.execute(
            select(JournalActivite).where(JournalActivite.action == ACTION_PRODUIT_CREE)
        ).scalar_one()

    engine.dispose()

    assert categorie.nom == "Tests antalgiques"
    assert produit.nom == "Paracetamol 500mg"
    assert produit.prix_vente == 1500
    assert produit.actif == 1
    assert journal.table_cible == "produits"
    assert journal.element_id == produit.id
    assert journal.utilisateur_id == gerant.utilisateur_id


def test_creer_produit_refuse_prix_negatif(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    gerant = _creer_utilisateur(SessionLocal, ROLE_GERANT)
    service = ProduitService(session_factory=SessionLocal)

    with pytest.raises(ValidationError, match="prix de vente"):
        service.creer_produit(
            gerant,
            ProduitPayload(nom="Ibuprofene", prix_vente=-1),
        )

    engine.dispose()


def test_creer_produit_refuse_code_barres_doublon(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    gerant = _creer_utilisateur(SessionLocal, ROLE_GERANT)
    service = ProduitService(session_factory=SessionLocal)

    service.creer_produit(
        gerant,
        ProduitPayload(nom="Amoxicilline", code_barres="DUP-001", prix_vente=2500),
    )

    with pytest.raises(ValidationError, match="code-barres"):
        service.creer_produit(
            gerant,
            ProduitPayload(nom="Amoxicilline autre", code_barres="DUP-001", prix_vente=2600),
        )

    engine.dispose()


def test_vendeur_interdit_de_creation_produit(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    vendeur = _creer_utilisateur(SessionLocal, ROLE_VENDEUR)
    service = ProduitService(session_factory=SessionLocal)

    with pytest.raises(PermissionRefuseeError):
        service.creer_produit(
            vendeur,
            ProduitPayload(nom="Produit vendeur", prix_vente=1000),
        )

    engine.dispose()


def test_modifier_et_desactiver_produit_preserve_historique(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    gerant = _creer_utilisateur(SessionLocal, ROLE_GERANT)
    service = ProduitService(session_factory=SessionLocal)
    produit = service.creer_produit(
        gerant,
        ProduitPayload(nom="Vitamine C", code_barres="VIT-001", prix_vente=1200),
    )

    modifie = service.modifier_produit(
        gerant,
        produit_id=produit.id,
        payload=ProduitPayload(nom="Vitamine C 500mg", code_barres="VIT-001", prix_vente=1300),
    )
    desactive = service.desactiver_produit(gerant, produit_id=produit.id)

    with SessionLocal() as session:
        produit_db = session.get(Produit, produit.id)
        actions = [
            journal.action
            for journal in session.execute(
                select(JournalActivite).order_by(JournalActivite.id.asc())
            ).scalars()
        ]

    engine.dispose()

    assert modifie.nom == "Vitamine C 500mg"
    assert desactive.actif == 0
    assert produit_db is not None
    assert produit_db.actif == 0
    assert ACTION_PRODUIT_MODIFIE in actions
    assert ACTION_PRODUIT_DESACTIVE in actions


def test_reactiver_produit_desactive_et_journalise_action(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    gerant = _creer_utilisateur(SessionLocal, ROLE_GERANT)
    service = ProduitService(session_factory=SessionLocal)
    produit = service.creer_produit(
        gerant,
        ProduitPayload(nom="Produit a reactiver", code_barres="REA-001", prix_vente=900),
    )
    service.desactiver_produit(gerant, produit_id=produit.id)

    reactive = service.reactiver_produit(gerant, produit_id=produit.id)

    with SessionLocal() as session:
        produit_db = session.get(Produit, produit.id)
        journaux = session.execute(
            select(JournalActivite).where(JournalActivite.action == ACTION_PRODUIT_MODIFIE)
        ).scalars().all()

    engine.dispose()

    assert reactive.actif == 1
    assert produit_db.actif == 1
    assert any("reactive" in (journal.details or "") for journal in journaux)


def test_vendeur_interdit_de_reactivation_produit(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    gerant = _creer_utilisateur(SessionLocal, ROLE_GERANT)
    vendeur = _creer_utilisateur(SessionLocal, ROLE_VENDEUR)
    service = ProduitService(session_factory=SessionLocal)
    produit = service.creer_produit(
        gerant,
        ProduitPayload(nom="Produit protege", code_barres="REA-002", prix_vente=900),
    )
    service.desactiver_produit(gerant, produit_id=produit.id)

    with pytest.raises(PermissionRefuseeError):
        service.reactiver_produit(vendeur, produit_id=produit.id)

    engine.dispose()


def test_rechercher_produits_filtre_par_categorie_et_statut(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    gerant = _creer_utilisateur(SessionLocal, ROLE_GERANT)
    service = ProduitService(session_factory=SessionLocal)
    categorie_a = service.creer_categorie(gerant, nom="Tests antibiotiques")
    categorie_b = service.creer_categorie(gerant, nom="Tests vitamines")
    produit_a = service.creer_produit(
        gerant,
        ProduitPayload(nom="Amoxicilline", categorie_id=categorie_a.id, prix_vente=2500),
    )
    produit_b = service.creer_produit(
        gerant,
        ProduitPayload(nom="Vitamine C", categorie_id=categorie_b.id, prix_vente=1200),
    )
    service.desactiver_produit(gerant, produit_id=produit_b.id)

    resultats = service.rechercher_produits(
        gerant,
        terme="a",
        categorie_id=categorie_a.id,
        actifs_seulement=True,
    )

    engine.dispose()

    assert [produit.id for produit in resultats] == [produit_a.id]


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


def _creer_utilisateur(SessionLocal, role: str) -> SessionUtilisateur:
    with SessionLocal() as session:
        utilisateur = Utilisateur(
            nom=f"Utilisateur {role}",
            email=f"{role.lower()}@test.local",
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
