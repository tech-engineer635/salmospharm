from sqlalchemy.orm import sessionmaker

from app.database.connection import create_app_engine
from app.database.init_db import init_database
from app.database.models import (
    Alerte,
    Categorie,
    JournalActivite,
    LigneVente,
    LotProduit,
    MouvementStock,
    Produit,
    Utilisateur,
    Vente,
)
from app.repositories.alerte_repository import AlerteRepository
from app.repositories.categorie_repository import CategorieRepository
from app.repositories.journal_repository import JournalRepository
from app.repositories.lot_produit_repository import LotProduitRepository
from app.repositories.parametre_repository import ParametreRepository
from app.repositories.produit_repository import ProduitRepository
from app.repositories.stock_repository import StockRepository
from app.repositories.utilisateur_repository import UtilisateurRepository
from app.repositories.vente_repository import VenteRepository


def test_repositories_catalogue_lots_stock_ventes_et_journal(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)

    utilisateur_repo = UtilisateurRepository()
    categorie_repo = CategorieRepository()
    produit_repo = ProduitRepository()
    lot_repo = LotProduitRepository()
    stock_repo = StockRepository()
    vente_repo = VenteRepository()
    alerte_repo = AlerteRepository()
    journal_repo = JournalRepository()
    parametre_repo = ParametreRepository()

    with SessionLocal() as session:
        vendeur = utilisateur_repo.creer(
            session,
            Utilisateur(
                nom="Vendeur Test",
                email="vendeur",
                mot_de_passe_hash="hash",
                role="VENDEUR",
            ),
        )
        categorie = categorie_repo.creer(session, Categorie(nom="Tests", description="Categorie de test"))
        produit = produit_repo.creer(
            session,
            Produit(
                categorie_id=categorie.id,
                nom="Paracetamol Test",
                code_barres="TEST-001",
                prix_vente=1500,
                stock_minimum=2,
                actif=1,
            ),
        )
        lot_expire = lot_repo.creer(
            session,
            LotProduit(
                produit_id=produit.id,
                numero_lot="EXP",
                quantite=50,
                prix_achat=900,
                date_expiration="2026-01-01",
            ),
        )
        lot_proche = lot_repo.creer(
            session,
            LotProduit(
                produit_id=produit.id,
                numero_lot="A",
                quantite=5,
                prix_achat=900,
                date_expiration="2026-07-01",
            ),
        )
        lot_lointain = lot_repo.creer(
            session,
            LotProduit(
                produit_id=produit.id,
                numero_lot="B",
                quantite=10,
                prix_achat=900,
                date_expiration="2026-12-01",
            ),
        )
        mouvement = stock_repo.creer_mouvement(
            session,
            MouvementStock(
                produit_id=produit.id,
                lot_id=lot_proche.id,
                utilisateur_id=vendeur.id,
                type_mouvement="ENTREE",
                quantite=5,
                motif="Test repository",
            ),
        )
        vente = vente_repo.creer_vente(
            session,
            Vente(
                numero_vente="VTE-2026-000001",
                vendeur_id=vendeur.id,
                total=3000,
                montant_recu=5000,
            ),
        )
        ligne = vente_repo.creer_ligne(
            session,
            LigneVente(
                vente_id=vente.id,
                produit_id=produit.id,
                lot_id=lot_proche.id,
                quantite=2,
                prix_unitaire=1500,
                sous_total=3000,
            ),
        )
        alerte = alerte_repo.creer(
            session,
            Alerte(
                produit_id=produit.id,
                lot_id=lot_expire.id,
                type_alerte="PRODUIT_EXPIRE",
                message="Lot expire",
            ),
        )
        journal = journal_repo.creer(
            session,
            JournalActivite(
                utilisateur_id=vendeur.id,
                action="VENTE_VALIDEE",
                table_cible="ventes",
                element_id=vente.id,
                details="Vente test",
            ),
        )
        session.commit()

        lots_disponibles = lot_repo.lister_disponibles_par_produit(session, produit.id, "2026-06-22")

        assert utilisateur_repo.compter(session) == 1
        assert utilisateur_repo.chercher_par_email(session, "vendeur").id == vendeur.id
        assert categorie_repo.chercher_par_nom(session, "Tests").id == categorie.id
        assert produit_repo.chercher_par_code_barres(session, "TEST-001").id == produit.id
        assert [lot.numero_lot for lot in lots_disponibles] == ["A", "B"]
        assert stock_repo.calculer_stock_disponible(session, produit.id, "2026-06-22") == 15
        assert stock_repo.lister_mouvements_par_produit(session, produit.id)[0].id == mouvement.id
        assert vente_repo.chercher_par_numero(session, "VTE-2026-000001").id == vente.id
        assert vente_repo.dernier_numero_pour_annee(session, 2026) == "VTE-2026-000001"
        assert vente_repo.lister_lignes(session, vente.id)[0].id == ligne.id
        assert alerte_repo.chercher_non_lue(session, produit.id, lot_expire.id, "PRODUIT_EXPIRE").id == alerte.id
        assert journal_repo.lister_par_action(session, "VENTE_VALIDEE")[0].id == journal.id
        assert parametre_repo.obtenir_principal(session).devise == "CDF"

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
