from datetime import date, timedelta

import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import sessionmaker

from app.core.exceptions import AuthentificationError
from app.database.connection import create_app_engine
from app.database.init_db import init_database
from app.database.models import Alerte, LotProduit, Produit
from app.services.alerte_service import AlerteService
from app.services.auth_service import AuthService, SessionUtilisateur
from app.services.parametre_service import ParametreService, ParametresGeneraux


def _database(tmp_path):
    engine = create_app_engine(tmp_path / "stabilisation.sqlite3")
    init_database(database_engine=engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    return engine, factory


def _gerant(utilisateur_id: int = 1) -> SessionUtilisateur:
    return SessionUtilisateur(
        utilisateur_id=utilisateur_id,
        nom="Gerant Test",
        identifiant="gerant",
        role="GERANT",
    )


def test_migration_alertes_complete_une_ancienne_table(tmp_path):
    engine = create_app_engine(tmp_path / "ancienne.sqlite3")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE alertes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produit_id INTEGER NOT NULL,
                lot_id INTEGER,
                type_alerte TEXT NOT NULL,
                message TEXT,
                est_lue INTEGER NOT NULL DEFAULT 0,
                cree_le TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    init_database(database_engine=engine)

    with engine.connect() as connection:
        colonnes = {
            row["name"]
            for row in connection.execute(text("PRAGMA table_info(alertes)")).mappings()
        }
    engine.dispose()
    assert {"est_active", "derniere_detection_le", "resolue_le"} <= colonnes


def test_cycle_alerte_acquittement_redemarrage_resolution_et_recidive(tmp_path):
    engine, factory = _database(tmp_path)
    reference = date(2026, 6, 28)
    with factory() as session:
        produit = Produit(
            nom="Produit surveille",
            prix_vente=1000,
            stock_minimum=5,
            actif=1,
        )
        session.add(produit)
        session.flush()
        lot = LotProduit(
            produit_id=produit.id,
            numero_lot="LOT-A",
            quantite=2,
            prix_achat=500,
            date_expiration=(reference + timedelta(days=3)).isoformat(),
        )
        session.add(lot)
        session.commit()
        produit_id = produit.id
        lot_id = lot.id

    service = AlerteService(session_factory=factory)
    assert service.reconcilier_alertes(
        produit_ids={produit_id}, date_reference=reference
    ) == 2

    with factory() as session:
        alertes = session.execute(select(Alerte)).scalars().all()
        stock_alert = next(
            alerte for alerte in alertes if alerte.type_alerte == "STOCK_FAIBLE"
        )
        stock_alert_id = stock_alert.id

    service.marquer_lue(_gerant(), alerte_id=stock_alert_id)
    assert service.reinitialiser_alertes_actives_au_demarrage() == 1

    with factory() as session:
        produit = session.get(Produit, produit_id)
        lot = session.get(LotProduit, lot_id)
        produit.stock_minimum = 0
        lot.date_expiration = (reference + timedelta(days=180)).isoformat()
        session.commit()
    service.reconcilier_alertes(
        produit_ids={produit_id}, date_reference=reference
    )
    with factory() as session:
        assert not session.execute(
            select(Alerte).where(Alerte.est_active == 1)
        ).scalars().all()
        lot = session.get(LotProduit, lot_id)
        lot.date_expiration = (reference + timedelta(days=2)).isoformat()
        session.commit()

    service.reconcilier_alertes(
        produit_ids={produit_id}, date_reference=reference
    )
    with factory() as session:
        expiration_alerts = session.execute(
            select(Alerte).where(Alerte.type_alerte == "EXPIRATION_PROCHE")
        ).scalars().all()
    engine.dispose()
    assert len(expiration_alerts) == 2
    assert sum(alerte.est_active for alerte in expiration_alerts) == 1


def test_recuperation_invalide_l_ancien_code(tmp_path):
    engine, factory = _database(tmp_path)
    service = AuthService(session_factory=factory)
    creation = service.creer_premier_gerant(
        nom_complet="Gerant Test",
        identifiant="gerant",
        mot_de_passe="ancien",
        confirmation_mot_de_passe="ancien",
    )
    result = service.reinitialiser_mot_de_passe(
        identifiant="gerant",
        code_recuperation=creation.code_recuperation,
        nouveau_mot_de_passe="nouveau",
        confirmation_mot_de_passe="nouveau",
    )
    assert result.nouveau_code_recuperation != creation.code_recuperation
    assert service.connecter(identifiant="gerant", mot_de_passe="nouveau")
    with pytest.raises(AuthentificationError):
        service.reinitialiser_mot_de_passe(
            identifiant="gerant",
            code_recuperation=creation.code_recuperation,
            nouveau_mot_de_passe="encore",
            confirmation_mot_de_passe="encore",
        )
    engine.dispose()


def test_parametres_generaux_et_impression_sont_persistes(tmp_path):
    engine, factory = _database(tmp_path)
    creation = AuthService(session_factory=factory).creer_premier_gerant(
        nom_complet="Gerant Test",
        identifiant="gerant",
        mot_de_passe="secret",
        confirmation_mot_de_passe="secret",
    )
    gerant = _gerant(creation.utilisateur_id)
    service = ParametreService(session_factory=factory)
    valeurs = ParametresGeneraux(
        nom_pharmacie="Pharmacie Test",
        telephone="+243 000 000",
        adresse="Goma",
        seuil_expiration_jours=45,
        nom_imprimante="Thermique 80",
        largeur_ticket=80,
        impression_auto=False,
    )
    service.enregistrer(gerant, valeurs)
    assert service.obtenir(gerant) == valeurs
    engine.dispose()
