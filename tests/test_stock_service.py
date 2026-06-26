from datetime import date, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.core.constants import (
    ACTION_STOCK_AJUSTE,
    ACTION_STOCK_ENTREE,
    ROLE_GERANT,
    ROLE_VENDEUR,
    TYPE_ALERTE_EXPIRATION_PROCHE,
    TYPE_ALERTE_STOCK_FAIBLE,
    TYPE_MOUVEMENT_AJUSTEMENT,
    TYPE_MOUVEMENT_ENTREE,
)
from app.core.exceptions import PermissionRefuseeError, ValidationError
from app.database.connection import create_app_engine
from app.database.init_db import init_database
from app.database.models import Alerte, JournalActivite, LotProduit, MouvementStock, Produit, Utilisateur
from app.services.auth_service import SessionUtilisateur
from app.services.stock_service import AjustementStockPayload, EntreeStockPayload, StockService


def test_entree_stock_cree_lot_mouvement_journal_et_alertes(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    gerant = _creer_utilisateur(SessionLocal, ROLE_GERANT)
    produit_id = _creer_produit(SessionLocal, stock_minimum=5)
    service = StockService(session_factory=SessionLocal)
    expiration = (date.today() + timedelta(days=10)).isoformat()

    result = service.entrer_stock(
        gerant,
        EntreeStockPayload(
            produit_id=produit_id,
            numero_lot="LOT-A",
            quantite=3,
            prix_achat=800,
            date_expiration=expiration,
            motif="Reception fournisseur",
        ),
    )

    with SessionLocal() as session:
        lot = session.get(LotProduit, result.lot.id)
        mouvement = session.execute(select(MouvementStock)).scalar_one()
        alertes = session.execute(select(Alerte).order_by(Alerte.type_alerte.asc())).scalars().all()
        journal = session.execute(
            select(JournalActivite).where(JournalActivite.action == ACTION_STOCK_ENTREE)
        ).scalar_one()

    engine.dispose()

    assert lot.quantite == 3
    assert lot.prix_achat == 800
    assert lot.date_expiration == expiration
    assert mouvement.type_mouvement == TYPE_MOUVEMENT_ENTREE
    assert mouvement.quantite == 3
    assert journal.table_cible == "lots_produits"
    assert {alerte.type_alerte for alerte in alertes} == {
        TYPE_ALERTE_EXPIRATION_PROCHE,
        TYPE_ALERTE_STOCK_FAIBLE,
    }
    assert result.alertes_creees == 2


def test_entree_stock_met_a_jour_lot_existant_et_trace_mouvement(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    gerant = _creer_utilisateur(SessionLocal, ROLE_GERANT)
    produit_id = _creer_produit(SessionLocal, stock_minimum=0)
    service = StockService(session_factory=SessionLocal)

    premier = service.entrer_stock(
        gerant,
        EntreeStockPayload(produit_id=produit_id, numero_lot="LOT-A", quantite=4, prix_achat=700),
    )
    second = service.entrer_stock(
        gerant,
        EntreeStockPayload(produit_id=produit_id, numero_lot="LOT-A", quantite=6, prix_achat=750),
    )

    with SessionLocal() as session:
        lots = session.execute(select(LotProduit)).scalars().all()
        mouvements = session.execute(select(MouvementStock).order_by(MouvementStock.id.asc())).scalars().all()

    engine.dispose()

    assert premier.lot.id == second.lot.id
    assert len(lots) == 1
    assert lots[0].quantite == 10
    assert lots[0].prix_achat == 750
    assert [mouvement.quantite for mouvement in mouvements] == [4, 6]


def test_ajustement_stock_avec_motif_modifie_quantite_et_journalise(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    gerant = _creer_utilisateur(SessionLocal, ROLE_GERANT)
    produit_id = _creer_produit(SessionLocal, stock_minimum=2)
    service = StockService(session_factory=SessionLocal)
    entree = service.entrer_stock(
        gerant,
        EntreeStockPayload(produit_id=produit_id, numero_lot="LOT-B", quantite=10, prix_achat=500),
    )

    result = service.ajuster_stock(
        gerant,
        AjustementStockPayload(
            lot_id=entree.lot.id,
            nouvelle_quantite=4,
            motif="Correction inventaire",
        ),
    )

    with SessionLocal() as session:
        lot = session.get(LotProduit, entree.lot.id)
        mouvement = session.execute(
            select(MouvementStock).where(MouvementStock.type_mouvement == TYPE_MOUVEMENT_AJUSTEMENT)
        ).scalar_one()
        journal = session.execute(
            select(JournalActivite).where(JournalActivite.action == ACTION_STOCK_AJUSTE)
        ).scalar_one()

    engine.dispose()

    assert result.lot.quantite == 4
    assert lot.quantite == 4
    assert mouvement.quantite == 6
    assert mouvement.motif == "Correction inventaire"
    assert journal.element_id == entree.lot.id


def test_quantite_negative_et_motif_absent_refuses(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    gerant = _creer_utilisateur(SessionLocal, ROLE_GERANT)
    produit_id = _creer_produit(SessionLocal, stock_minimum=0)
    service = StockService(session_factory=SessionLocal)
    entree = service.entrer_stock(
        gerant,
        EntreeStockPayload(produit_id=produit_id, numero_lot="LOT-C", quantite=3, prix_achat=500),
    )

    with pytest.raises(ValidationError):
        service.entrer_stock(
            gerant,
            EntreeStockPayload(produit_id=produit_id, numero_lot="LOT-D", quantite=-1, prix_achat=500),
        )

    with pytest.raises(ValidationError):
        service.ajuster_stock(
            gerant,
            AjustementStockPayload(lot_id=entree.lot.id, nouvelle_quantite=2, motif=""),
        )

    with pytest.raises(ValidationError):
        service.ajuster_stock(
            gerant,
            AjustementStockPayload(lot_id=entree.lot.id, nouvelle_quantite=-2, motif="Correction inventaire"),
        )

    engine.dispose()


def test_vendeur_interdit_entree_et_ajustement_stock(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    gerant = _creer_utilisateur(SessionLocal, ROLE_GERANT)
    vendeur = _creer_utilisateur(SessionLocal, ROLE_VENDEUR)
    produit_id = _creer_produit(SessionLocal, stock_minimum=0)
    service = StockService(session_factory=SessionLocal)
    entree = service.entrer_stock(
        gerant,
        EntreeStockPayload(produit_id=produit_id, numero_lot="LOT-E", quantite=3, prix_achat=500),
    )

    with pytest.raises(PermissionRefuseeError):
        service.entrer_stock(
            vendeur,
            EntreeStockPayload(produit_id=produit_id, numero_lot="LOT-F", quantite=3, prix_achat=500),
        )

    with pytest.raises(PermissionRefuseeError):
        service.ajuster_stock(
            vendeur,
            AjustementStockPayload(lot_id=entree.lot.id, nouvelle_quantite=2, motif="Correction inventaire"),
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


def _creer_utilisateur(SessionLocal, role: str) -> SessionUtilisateur:
    with SessionLocal() as session:
        utilisateur = Utilisateur(
            nom=f"Utilisateur {role}",
            email=f"{role.lower()}-stock@test.local",
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


def _creer_produit(SessionLocal, *, stock_minimum: int) -> int:
    with SessionLocal() as session:
        produit = Produit(
            nom=f"Produit stock {stock_minimum}",
            code_barres=f"STOCK-{stock_minimum}",
            prix_vente=1500,
            stock_minimum=stock_minimum,
            actif=1,
        )
        session.add(produit)
        session.commit()
        return produit.id
