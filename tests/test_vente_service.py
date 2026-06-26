from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from app.core.constants import ACTION_VENTE_VALIDEE, ROLE_GERANT, ROLE_VENDEUR, TYPE_MOUVEMENT_SORTIE
from app.core.exceptions import PermissionRefuseeError, ProduitInactifError, StockInsuffisantError, ValidationError
from app.database.connection import create_app_engine
from app.database.init_db import init_database
from app.database.models import JournalActivite, LigneVente, LotProduit, MouvementStock, Produit, Utilisateur, Vente
from app.services.auth_service import SessionUtilisateur
from app.services.vente_service import LignePanierPayload, VentePayload, VenteService


def test_valider_vente_applique_fefo_cree_lignes_mouvements_et_journal(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    vendeur = _creer_utilisateur(SessionLocal, ROLE_VENDEUR)
    produit_id = _creer_produit(SessionLocal, nom="Paracetamol 500mg", prix_vente=1000, stock_minimum=2)
    lot_lointain = _creer_lot(SessionLocal, produit_id=produit_id, numero_lot="LOT-LOINTAIN", quantite=10, date_expiration="2026-12-31")
    lot_proche = _creer_lot(SessionLocal, produit_id=produit_id, numero_lot="LOT-PROCHE", quantite=5, date_expiration="2026-07-01")
    service = VenteService(session_factory=SessionLocal)

    result = service.valider_vente(
        vendeur,
        VentePayload(lignes=[LignePanierPayload(produit_id=produit_id, quantite=8)], montant_recu=10_000),
        date_reference=date(2026, 6, 26),
    )

    with SessionLocal() as session:
        vente = session.get(Vente, result.vente_id)
        lignes = session.execute(select(LigneVente).order_by(LigneVente.id.asc())).scalars().all()
        mouvements = session.execute(select(MouvementStock).order_by(MouvementStock.id.asc())).scalars().all()
        journal = session.execute(
            select(JournalActivite).where(JournalActivite.action == ACTION_VENTE_VALIDEE)
        ).scalar_one()
        quantites = {
            lot.id: lot.quantite
            for lot in session.execute(select(LotProduit).order_by(LotProduit.id.asc())).scalars().all()
        }

    engine.dispose()

    assert result.numero_vente == "VTE-2026-000001"
    assert result.total == 8_000
    assert result.monnaie_rendue == 2_000
    assert vente.total == 8_000
    assert [(ligne.lot_id, ligne.quantite, ligne.sous_total) for ligne in lignes] == [
        (lot_proche, 5, 5_000),
        (lot_lointain, 3, 3_000),
    ]
    assert all(mouvement.type_mouvement == TYPE_MOUVEMENT_SORTIE for mouvement in mouvements)
    assert [mouvement.quantite for mouvement in mouvements] == [5, 3]
    assert quantites[lot_proche] == 0
    assert quantites[lot_lointain] == 7
    assert journal.table_cible == "ventes"
    assert journal.element_id == result.vente_id


def test_valider_vente_groupe_les_doublons_et_genere_numero_suivant(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    gerant = _creer_utilisateur(SessionLocal, ROLE_GERANT)
    produit_id = _creer_produit(SessionLocal, nom="Amoxicilline 500mg", prix_vente=800)
    _creer_lot(SessionLocal, produit_id=produit_id, numero_lot="LOT-A", quantite=10, date_expiration="2026-08-01")
    service = VenteService(session_factory=SessionLocal)

    premier = service.valider_vente(
        gerant,
        VentePayload(
            lignes=[
                LignePanierPayload(produit_id=produit_id, quantite=1),
                LignePanierPayload(produit_id=produit_id, quantite=2),
            ],
            montant_recu=3_000,
        ),
        date_reference=date(2026, 6, 26),
    )
    second = service.valider_vente(
        gerant,
        VentePayload(lignes=[LignePanierPayload(produit_id=produit_id, quantite=1)], montant_recu=1_000),
        date_reference=date(2026, 6, 26),
    )

    with SessionLocal() as session:
        lignes = session.execute(select(LigneVente).where(LigneVente.vente_id == premier.vente_id)).scalars().all()

    engine.dispose()

    assert premier.numero_vente == "VTE-2026-000001"
    assert second.numero_vente == "VTE-2026-000002"
    assert premier.total == 2_400
    assert len(lignes) == 1
    assert lignes[0].quantite == 3


def test_valider_vente_refuse_panier_vide_quantite_invalide_et_montant_insuffisant(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    vendeur = _creer_utilisateur(SessionLocal, ROLE_VENDEUR)
    produit_id = _creer_produit(SessionLocal, nom="Vitamine C 500mg", prix_vente=750)
    _creer_lot(SessionLocal, produit_id=produit_id, numero_lot="LOT-A", quantite=4, date_expiration="2026-08-01")
    service = VenteService(session_factory=SessionLocal)

    with pytest.raises(ValidationError):
        service.valider_vente(vendeur, VentePayload(lignes=[], montant_recu=1_000), date_reference=date(2026, 6, 26))

    with pytest.raises(ValidationError):
        service.valider_vente(
            vendeur,
            VentePayload(lignes=[LignePanierPayload(produit_id=produit_id, quantite=0)], montant_recu=1_000),
            date_reference=date(2026, 6, 26),
        )

    with pytest.raises(ValidationError):
        service.valider_vente(
            vendeur,
            VentePayload(lignes=[LignePanierPayload(produit_id=produit_id, quantite=2)], montant_recu=1_000),
            date_reference=date(2026, 6, 26),
        )

    _assert_aucune_vente_creee(SessionLocal)
    engine.dispose()


def test_valider_vente_refuse_stock_insuffisant_et_reste_atomique(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    vendeur = _creer_utilisateur(SessionLocal, ROLE_VENDEUR)
    produit_id = _creer_produit(SessionLocal, nom="Ibuprofene 400mg", prix_vente=900)
    lot_id = _creer_lot(SessionLocal, produit_id=produit_id, numero_lot="LOT-A", quantite=2, date_expiration="2026-08-01")
    service = VenteService(session_factory=SessionLocal)

    with pytest.raises(StockInsuffisantError):
        service.valider_vente(
            vendeur,
            VentePayload(lignes=[LignePanierPayload(produit_id=produit_id, quantite=3)], montant_recu=5_000),
            date_reference=date(2026, 6, 26),
        )

    with SessionLocal() as session:
        lot = session.get(LotProduit, lot_id)
        ventes = session.execute(select(func.count(Vente.id))).scalar_one()
        mouvements = session.execute(select(func.count(MouvementStock.id))).scalar_one()

    engine.dispose()

    assert lot.quantite == 2
    assert ventes == 0
    assert mouvements == 0


def test_valider_vente_ignore_lot_expire_et_refuse_produit_inactif(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    vendeur = _creer_utilisateur(SessionLocal, ROLE_VENDEUR)
    produit_id = _creer_produit(SessionLocal, nom="Produit expire", prix_vente=500)
    produit_inactif_id = _creer_produit(SessionLocal, nom="Produit inactif", prix_vente=500, actif=0)
    _creer_lot(SessionLocal, produit_id=produit_id, numero_lot="LOT-EXPIRE", quantite=5, date_expiration="2026-06-25")
    _creer_lot(SessionLocal, produit_id=produit_inactif_id, numero_lot="LOT-I", quantite=5, date_expiration="2026-08-01")
    service = VenteService(session_factory=SessionLocal)

    with pytest.raises(StockInsuffisantError):
        service.valider_vente(
            vendeur,
            VentePayload(lignes=[LignePanierPayload(produit_id=produit_id, quantite=1)], montant_recu=1_000),
            date_reference=date(2026, 6, 26),
        )

    with pytest.raises(ProduitInactifError):
        service.valider_vente(
            vendeur,
            VentePayload(lignes=[LignePanierPayload(produit_id=produit_inactif_id, quantite=1)], montant_recu=1_000),
            date_reference=date(2026, 6, 26),
        )

    _assert_aucune_vente_creee(SessionLocal)
    engine.dispose()


def test_valider_vente_refuse_role_sans_permission(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    inconnu = SessionUtilisateur(utilisateur_id=99, nom="Invite", identifiant="invite", role="INVITE")
    service = VenteService(session_factory=SessionLocal)

    with pytest.raises(PermissionRefuseeError):
        service.valider_vente(
            inconnu,
            VentePayload(lignes=[LignePanierPayload(produit_id=1, quantite=1)], montant_recu=1_000),
            date_reference=date(2026, 6, 26),
        )

    engine.dispose()


def test_lister_produits_vendables_exclut_stock_expire_ou_vide(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    vendeur = _creer_utilisateur(SessionLocal, ROLE_VENDEUR)
    disponible_id = _creer_produit(SessionLocal, nom="Disponible", prix_vente=1000)
    expire_id = _creer_produit(SessionLocal, nom="Expire", prix_vente=1000)
    vide_id = _creer_produit(SessionLocal, nom="Vide", prix_vente=1000)
    _creer_lot(SessionLocal, produit_id=disponible_id, numero_lot="LOT-A", quantite=3, date_expiration="2026-08-01")
    _creer_lot(SessionLocal, produit_id=expire_id, numero_lot="LOT-B", quantite=3, date_expiration="2026-06-25")
    _creer_lot(SessionLocal, produit_id=vide_id, numero_lot="LOT-C", quantite=0, date_expiration="2026-08-01")
    service = VenteService(session_factory=SessionLocal)

    produits = service.lister_produits_vendables(vendeur, date_reference=date(2026, 6, 26))

    engine.dispose()

    assert [(produit.produit_id, produit.stock_disponible) for produit in produits] == [(disponible_id, 3)]


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
            email=f"{role.lower()}-vente@test.local",
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


def _creer_produit(SessionLocal, *, nom: str, prix_vente: int, stock_minimum: int = 0, actif: int = 1) -> int:
    with SessionLocal() as session:
        produit = Produit(
            nom=nom,
            code_barres=f"{nom.upper().replace(' ', '-')}-{actif}",
            prix_vente=prix_vente,
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


def _assert_aucune_vente_creee(SessionLocal) -> None:
    with SessionLocal() as session:
        assert session.execute(select(func.count(Vente.id))).scalar_one() == 0
        assert session.execute(select(func.count(LigneVente.id))).scalar_one() == 0
        assert session.execute(select(func.count(MouvementStock.id))).scalar_one() == 0
