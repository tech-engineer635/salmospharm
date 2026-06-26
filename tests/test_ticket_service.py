from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.core.constants import ACTION_ERREUR_IMPRESSION, ACTION_FACTURE_IMPRIMEE, ROLE_GERANT, ROLE_VENDEUR
from app.core.exceptions import ImprimanteIndisponibleError, PermissionRefuseeError
from app.database.connection import create_app_engine
from app.database.init_db import init_database
from app.database.models import JournalActivite, LotProduit, Parametre, Produit, Utilisateur
from app.services.auth_service import SessionUtilisateur
from app.services.impression_service import ImpressionService
from app.services.ticket_service import TicketService
from app.services.vente_service import LignePanierPayload, VentePayload, VenteService


def test_generer_ticket_depuis_vente_validee_sans_table_facture(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    vendeur = _creer_utilisateur(SessionLocal, ROLE_VENDEUR, nom="Jean K.")
    produit_id = _creer_produit(SessionLocal, nom="Paracetamol 500mg", prix_vente=1000)
    _creer_lot(SessionLocal, produit_id=produit_id, quantite=5)
    vente = VenteService(session_factory=SessionLocal).valider_vente(
        vendeur,
        VentePayload(lignes=[LignePanierPayload(produit_id=produit_id, quantite=2)], montant_recu=2500),
        date_reference=date(2026, 6, 26),
    )
    service = TicketService(session_factory=SessionLocal)

    ticket = service.generer_ticket(vendeur, vente.vente_id)

    engine.dispose()

    assert ticket.numero_vente == "VTE-2026-000001"
    assert ticket.vendeur_nom == "Jean K."
    assert ticket.nom_pharmacie == "SALMOSPHARM 133"
    assert ticket.devise == "CDF"
    assert ticket.total == 2000
    assert ticket.monnaie_rendue == 500
    assert [(line.produit_nom, line.quantite, line.sous_total) for line in ticket.lignes] == [
        ("Paracetamol 500mg", 2, 2000)
    ]


def test_vendeur_ne_peut_generer_que_son_propre_ticket(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    vendeur = _creer_utilisateur(SessionLocal, ROLE_VENDEUR, nom="Jean K.", email="jean@test.local")
    autre_vendeur = _creer_utilisateur(SessionLocal, ROLE_VENDEUR, nom="Alice M.", email="alice@test.local")
    produit_id = _creer_produit(SessionLocal, nom="Amoxicilline 500mg", prix_vente=1000)
    _creer_lot(SessionLocal, produit_id=produit_id, quantite=3)
    vente = VenteService(session_factory=SessionLocal).valider_vente(
        vendeur,
        VentePayload(lignes=[LignePanierPayload(produit_id=produit_id, quantite=1)], montant_recu=1000),
        date_reference=date(2026, 6, 26),
    )
    service = TicketService(session_factory=SessionLocal)

    with pytest.raises(PermissionRefuseeError):
        service.generer_ticket(autre_vendeur, vente.vente_id)

    engine.dispose()


def test_ticket_pdf_et_journal_impression(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    vendeur = _creer_utilisateur(SessionLocal, ROLE_VENDEUR)
    produit_id = _creer_produit(SessionLocal, nom="Vitamine C 500mg", prix_vente=750)
    _creer_lot(SessionLocal, produit_id=produit_id, quantite=2)
    vente = VenteService(session_factory=SessionLocal).valider_vente(
        vendeur,
        VentePayload(lignes=[LignePanierPayload(produit_id=produit_id, quantite=1)], montant_recu=1000),
        date_reference=date(2026, 6, 26),
    )
    service = TicketService(session_factory=SessionLocal)
    ticket = service.generer_ticket(vendeur, vente.vente_id)
    pdf_path = tmp_path / "ticket.pdf"

    service.exporter_pdf(ticket, pdf_path)
    service.journaliser_impression(vendeur, ticket)

    with SessionLocal() as session:
        journal = session.execute(select(JournalActivite).where(JournalActivite.action == ACTION_FACTURE_IMPRIMEE)).scalar_one()

    engine.dispose()

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0
    assert journal.table_cible == "ventes"
    assert journal.element_id == ticket.vente_id


def test_impression_service_formate_58_80_et_refuse_imprimante_absente(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    vendeur = _creer_utilisateur(SessionLocal, ROLE_VENDEUR)
    produit_id = _creer_produit(SessionLocal, nom="Ibuprofene 400mg", prix_vente=900)
    _creer_lot(SessionLocal, produit_id=produit_id, quantite=2)
    vente = VenteService(session_factory=SessionLocal).valider_vente(
        vendeur,
        VentePayload(lignes=[LignePanierPayload(produit_id=produit_id, quantite=1)], montant_recu=1000),
        date_reference=date(2026, 6, 26),
    )
    ticket = TicketService(session_factory=SessionLocal).generer_ticket(vendeur, vente.vente_id)
    service = ImpressionService()

    texte_80 = service.formater_ticket(ticket)
    ticket_58 = ticket.__class__(**{**ticket.__dict__, "largeur_ticket": 58})
    texte_58 = service.formater_ticket(ticket_58)

    with pytest.raises(ImprimanteIndisponibleError):
        service.imprimer_ticket(ticket)

    engine.dispose()

    assert "SALMOSPHARM 133" in texte_80
    assert "TOTAL" in texte_80
    assert len(texte_58.splitlines()[0]) == 32
    assert len(texte_80.splitlines()[0]) == 42


def test_erreur_impression_est_journalisee_sans_modifier_la_vente(tmp_path):
    engine, SessionLocal = _create_test_session_factory(tmp_path)
    vendeur = _creer_utilisateur(SessionLocal, ROLE_VENDEUR)
    produit_id = _creer_produit(SessionLocal, nom="Omeprazole 20mg", prix_vente=700)
    lot_id = _creer_lot(SessionLocal, produit_id=produit_id, quantite=2)
    vente = VenteService(session_factory=SessionLocal).valider_vente(
        vendeur,
        VentePayload(lignes=[LignePanierPayload(produit_id=produit_id, quantite=1)], montant_recu=1000),
        date_reference=date(2026, 6, 26),
    )
    service = TicketService(session_factory=SessionLocal)
    ticket = service.generer_ticket(vendeur, vente.vente_id)

    service.journaliser_erreur_impression(vendeur, ticket, "Aucune imprimante n'est configuree.")

    with SessionLocal() as session:
        lot = session.get(LotProduit, lot_id)
        journal = session.execute(select(JournalActivite).where(JournalActivite.action == ACTION_ERREUR_IMPRESSION)).scalar_one()

    engine.dispose()

    assert lot.quantite == 1
    assert journal.element_id == vente.vente_id


def _create_test_session_factory(tmp_path):
    database_path = tmp_path / "salmospharm.sqlite3"
    engine = create_app_engine(database_path)
    init_database(database_engine=engine)
    with sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)() as session:
        parametre = session.execute(select(Parametre)).scalar_one()
        parametre.nom_pharmacie = "SALMOSPHARM 133"
        parametre.telephone = "+243 97 123 45 67"
        parametre.adresse = "Goma, Nord-Kivu"
        parametre.largeur_ticket = 80
        parametre.impression_auto = 0
        session.commit()
    return engine, sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)


def _creer_utilisateur(SessionLocal, role: str, *, nom: str | None = None, email: str | None = None) -> SessionUtilisateur:
    with SessionLocal() as session:
        utilisateur = Utilisateur(
            nom=nom or f"Utilisateur {role}",
            email=email or f"{role.lower()}-{id(SessionLocal)}@test.local",
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


def _creer_produit(SessionLocal, *, nom: str, prix_vente: int) -> int:
    with SessionLocal() as session:
        produit = Produit(nom=nom, code_barres=f"{nom}-code", prix_vente=prix_vente, stock_minimum=0, actif=1)
        session.add(produit)
        session.commit()
        return produit.id


def _creer_lot(SessionLocal, *, produit_id: int, quantite: int) -> int:
    with SessionLocal() as session:
        lot = LotProduit(
            produit_id=produit_id,
            numero_lot=f"LOT-{produit_id}",
            quantite=quantite,
            prix_achat=500,
            date_expiration="2026-08-01",
        )
        session.add(lot)
        session.commit()
        return lot.id
