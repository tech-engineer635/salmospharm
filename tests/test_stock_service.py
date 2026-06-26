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
from app.core.exceptions import ProduitInactifError, StockInsuffisantError
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


def test_fefo_selectionne_lot_expiration_proche_en_premier(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    gerant = _creer_utilisateur(SessionLocal, ROLE_GERANT)
    produit_id = _creer_produit(SessionLocal, stock_minimum=0)
    _creer_lot(SessionLocal, produit_id=produit_id, numero_lot="LOT-LOINTAIN", quantite=10, date_expiration="2026-12-31")
    _creer_lot(SessionLocal, produit_id=produit_id, numero_lot="LOT-PROCHE", quantite=5, date_expiration="2026-07-01")
    service = StockService(session_factory=SessionLocal)

    selections = service.choisir_lots_fefo(
        gerant,
        produit_id=produit_id,
        quantite_demandee=8,
        date_reference=date(2026, 6, 26),
    )

    engine.dispose()

    assert [(selection.numero_lot, selection.quantite) for selection in selections] == [
        ("LOT-PROCHE", 5),
        ("LOT-LOINTAIN", 3),
    ]


def test_fefo_ignore_lot_expire_et_lot_vide(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    vendeur = _creer_utilisateur(SessionLocal, ROLE_VENDEUR)
    produit_id = _creer_produit(SessionLocal, stock_minimum=0)
    _creer_lot(SessionLocal, produit_id=produit_id, numero_lot="LOT-EXPIRE", quantite=20, date_expiration="2026-06-25")
    _creer_lot(SessionLocal, produit_id=produit_id, numero_lot="LOT-VIDE", quantite=0, date_expiration="2026-07-01")
    _creer_lot(SessionLocal, produit_id=produit_id, numero_lot="LOT-OK", quantite=4, date_expiration="2026-08-01")
    service = StockService(session_factory=SessionLocal)

    selections = service.choisir_lots_fefo(
        vendeur,
        produit_id=produit_id,
        quantite_demandee=3,
        date_reference=date(2026, 6, 26),
    )

    engine.dispose()

    assert [(selection.numero_lot, selection.quantite) for selection in selections] == [("LOT-OK", 3)]


def test_fefo_place_lot_sans_expiration_apres_lots_dates(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    gerant = _creer_utilisateur(SessionLocal, ROLE_GERANT)
    produit_id = _creer_produit(SessionLocal, stock_minimum=0)
    _creer_lot(SessionLocal, produit_id=produit_id, numero_lot="LOT-SANS-DATE", quantite=10, date_expiration=None)
    _creer_lot(SessionLocal, produit_id=produit_id, numero_lot="LOT-DATE", quantite=2, date_expiration="2026-07-15")
    service = StockService(session_factory=SessionLocal)

    selections = service.choisir_lots_fefo(
        gerant,
        produit_id=produit_id,
        quantite_demandee=5,
        date_reference=date(2026, 6, 26),
    )

    engine.dispose()

    assert [(selection.numero_lot, selection.quantite) for selection in selections] == [
        ("LOT-DATE", 2),
        ("LOT-SANS-DATE", 3),
    ]


def test_fefo_refuse_stock_insuffisant_et_quantite_invalide(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    gerant = _creer_utilisateur(SessionLocal, ROLE_GERANT)
    produit_id = _creer_produit(SessionLocal, stock_minimum=0)
    _creer_lot(SessionLocal, produit_id=produit_id, numero_lot="LOT-A", quantite=2, date_expiration="2026-07-01")
    service = StockService(session_factory=SessionLocal)

    with pytest.raises(StockInsuffisantError):
        service.choisir_lots_fefo(
            gerant,
            produit_id=produit_id,
            quantite_demandee=3,
            date_reference=date(2026, 6, 26),
        )

    with pytest.raises(ValidationError):
        service.choisir_lots_fefo(
            gerant,
            produit_id=produit_id,
            quantite_demandee=0,
            date_reference=date(2026, 6, 26),
        )

    engine.dispose()


def test_fefo_refuse_produit_inactif(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    gerant = _creer_utilisateur(SessionLocal, ROLE_GERANT)
    produit_id = _creer_produit(SessionLocal, stock_minimum=0, actif=0)
    _creer_lot(SessionLocal, produit_id=produit_id, numero_lot="LOT-A", quantite=5, date_expiration="2026-07-01")
    service = StockService(session_factory=SessionLocal)

    with pytest.raises(ProduitInactifError):
        service.choisir_lots_fefo(
            gerant,
            produit_id=produit_id,
            quantite_demandee=1,
            date_reference=date(2026, 6, 26),
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


def _creer_produit(SessionLocal, *, stock_minimum: int, actif: int = 1) -> int:
    with SessionLocal() as session:
        produit = Produit(
            nom=f"Produit stock {stock_minimum}",
            code_barres=f"STOCK-{stock_minimum}",
            prix_vente=1500,
            stock_minimum=stock_minimum,
            actif=actif,
        )
        session.add(produit)
        session.commit()
        return produit.id


def _creer_lot(
    SessionLocal,
    *,
    produit_id: int,
    numero_lot: str,
    quantite: int,
    date_expiration: str | None,
) -> int:
    with SessionLocal() as session:
        lot = LotProduit(
            produit_id=produit_id,
            numero_lot=numero_lot,
            quantite=quantite,
            prix_achat=500,
            date_expiration=date_expiration,
        )
        session.add(lot)
        session.commit()
        return lot.id
