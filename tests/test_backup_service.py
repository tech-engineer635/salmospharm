import json
import os
import zipfile
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.core.constants import (
    ACTION_BACKUP_EXPORTE,
    ACTION_BACKUP_IMPORTE,
    ACTION_SAUVEGARDE_AUTO_CREEE,
    ROLE_GERANT,
    ROLE_VENDEUR,
)
from app.core.exceptions import BackupInvalideError, PermissionRefuseeError
from app.database.connection import create_app_engine
from app.database.init_db import init_database
from app.database.models import JournalActivite, Parametre, Produit, Utilisateur
from app.services.auth_service import SessionUtilisateur
from app.services.backup_service import AutomaticBackupManager, BackupService


def test_export_spharm_contient_base_manifest_assets_et_factures(tmp_path):
    engine, SessionLocal, service = _environment(tmp_path)
    gerant = _create_user(SessionLocal, ROLE_GERANT, "gerant@test.local")
    _create_product(SessionLocal, "Paracetamol")
    service.assets_dir.mkdir(parents=True)
    service.factures_dir.mkdir(parents=True)
    (service.assets_dir / "logo-client.png").write_bytes(b"logo")
    (service.factures_dir / "ticket.pdf").write_bytes(b"pdf")

    result = service.exporter_backup(gerant, tmp_path / "export.spharm")
    info = service.inspecter_backup(gerant, result.path)

    with zipfile.ZipFile(result.path) as archive:
        names = set(archive.namelist())
        manifest = json.loads(archive.read("manifest.json"))
    with SessionLocal() as session:
        actions = list(
            session.execute(
                select(JournalActivite).where(JournalActivite.action == ACTION_BACKUP_EXPORTE)
            ).scalars()
        )

    engine.dispose()

    assert "database/salmospharm.sqlite3" in names
    assert "assets/logo-client.png" in names
    assert "factures/ticket.pdf" in names
    assert manifest["application"] == "SALMOSPHARM 133"
    assert len(manifest["database"]["sha256"]) == 64
    assert info.assets_included and info.factures_included
    assert actions


def test_import_restaure_donnees_fichiers_et_journal_apres_redemarrage(tmp_path):
    engine, SessionLocal, service = _environment(tmp_path)
    gerant = _create_user(SessionLocal, ROLE_GERANT, "gerant@test.local")
    _create_product(SessionLocal, "Produit sauvegarde")
    service.assets_dir.mkdir(parents=True)
    (service.assets_dir / "logo.png").write_text("ancien", encoding="utf-8")
    backup = service.exporter_backup(gerant, tmp_path / "source.spharm").path

    _create_product(SessionLocal, "Produit apres backup")
    (service.assets_dir / "logo.png").write_text("modifie", encoding="utf-8")

    result = service.importer_backup(gerant, backup)
    finalised = service.finaliser_import_apres_redemarrage()

    with SessionLocal() as session:
        products = {
            product.nom for product in session.execute(select(Produit)).scalars()
        }
        imported_actions = list(
            session.execute(
                select(JournalActivite).where(JournalActivite.action == ACTION_BACKUP_IMPORTE)
            ).scalars()
        )

    engine.dispose()

    assert result.restart_required
    assert result.security_backup_path.exists()
    assert products == {"Produit sauvegarde"}
    assert (service.assets_dir / "logo.png").read_text(encoding="utf-8") == "ancien"
    assert finalised
    assert imported_actions
    assert not service.restore_marker_path.exists()


def test_backup_refuse_vendeur_et_archive_dangereuse(tmp_path):
    engine, SessionLocal, service = _environment(tmp_path)
    vendeur = _create_user(SessionLocal, ROLE_VENDEUR, "vendeur@test.local")
    malicious = tmp_path / "danger.spharm"
    with zipfile.ZipFile(malicious, "w") as archive:
        archive.writestr("../attaque.txt", "interdit")
        archive.writestr("manifest.json", "{}")

    with pytest.raises(PermissionRefuseeError):
        service.exporter_backup(vendeur, tmp_path / "interdit.spharm")
    with pytest.raises(PermissionRefuseeError):
        service.inspecter_backup(vendeur, malicious)

    gerant = _create_user(SessionLocal, ROLE_GERANT, "gerant@test.local")
    with pytest.raises(BackupInvalideError):
        service.inspecter_backup(gerant, malicious)

    engine.dispose()


def test_import_revient_aux_donnees_actuelles_si_remplacement_fichier_echoue(tmp_path, monkeypatch):
    engine, SessionLocal, service = _environment(tmp_path)
    gerant = _create_user(SessionLocal, ROLE_GERANT, "gerant@test.local")
    _create_product(SessionLocal, "Produit archive")
    backup = service.exporter_backup(gerant, tmp_path / "source.spharm").path
    _create_product(SessionLocal, "Produit actuel")

    original_restore = service._restore_optional_directory
    calls = {"count": 0}

    def fail_once(source: Path, target: Path):
        calls["count"] += 1
        if calls["count"] == 1:
            raise OSError("simulation")
        return original_restore(source, target)

    monkeypatch.setattr(service, "_restore_optional_directory", fail_once)

    with pytest.raises(BackupInvalideError):
        service.importer_backup(gerant, backup)

    with SessionLocal() as session:
        products = {
            product.nom for product in session.execute(select(Produit)).scalars()
        }

    engine.dispose()

    assert products == {"Produit archive", "Produit actuel"}


def test_sauvegarde_quotidienne_est_creee_une_seule_fois_par_jour(tmp_path):
    engine, SessionLocal, service = _environment(tmp_path)

    first = service.executer_sauvegarde_quotidienne()
    second = service.executer_sauvegarde_quotidienne()

    with SessionLocal() as session:
        parametre = session.execute(select(Parametre)).scalar_one()
        actions = list(
            session.execute(
                select(JournalActivite).where(
                    JournalActivite.action == ACTION_SAUVEGARDE_AUTO_CREEE
                )
            ).scalars()
        )

    engine.dispose()

    assert first.created and first.path is not None and first.path.exists()
    assert first.path.name.startswith("auto_")
    assert not second.created and second.reason == "deja_effectuee"
    assert parametre.derniere_sauvegarde
    assert len(actions) == 1


def test_sauvegarde_fermeture_exige_une_modification(tmp_path):
    engine, SessionLocal, service = _environment(tmp_path)
    empreinte = service.empreinte_donnees()

    unchanged = service.executer_sauvegarde_fermeture(empreinte)
    _create_product(SessionLocal, "Produit modifie")
    changed = service.executer_sauvegarde_fermeture(empreinte)

    engine.dispose()

    assert not unchanged.created and unchanged.reason == "aucune_modification"
    assert changed.created and changed.reason == "fermeture"
    assert changed.path is not None and changed.path.exists()


def test_configuration_auto_est_persistante_et_reservee_au_gerant(tmp_path):
    engine, SessionLocal, service = _environment(tmp_path)
    gerant = _create_user(SessionLocal, ROLE_GERANT, "gerant-auto@test.local")
    vendeur = _create_user(SessionLocal, ROLE_VENDEUR, "vendeur-auto@test.local")

    configuration = service.configurer_sauvegarde_automatique(
        gerant,
        activee=False,
        frequence="FERMETURE",
    )
    result = service.executer_sauvegarde_quotidienne()

    with pytest.raises(PermissionRefuseeError):
        service.configurer_sauvegarde_automatique(
            vendeur,
            activee=True,
            frequence="QUOTIDIENNE",
        )

    engine.dispose()

    assert not configuration.activee
    assert configuration.frequence == "FERMETURE"
    assert not result.created and result.reason == "configuration_inactive"


def test_retention_conserve_15_archives_internes_et_export_manuel(tmp_path):
    engine, _SessionLocal, service = _environment(tmp_path)
    service.backups_dir.mkdir(parents=True)
    for index in range(18):
        archive = service.backups_dir / f"auto_2026-06-01_00-00-{index:02d}.spharm"
        archive.write_bytes(str(index).encode("ascii"))
        os.utime(archive, (index + 1, index + 1))
    manual = service.backups_dir / "sauvegarde_client.spharm"
    manual.write_bytes(b"manual")

    deleted = service.nettoyer_anciennes_sauvegardes()
    remaining_internal = list(service.backups_dir.glob("auto_*.spharm"))

    engine.dispose()

    assert len(deleted) == 3
    assert len(remaining_internal) == 15
    assert manual.exists()


def test_gestionnaire_cycle_de_vie_sauvegarde_une_seule_fois_a_la_fermeture(tmp_path):
    engine, SessionLocal, service = _environment(tmp_path)
    manager = AutomaticBackupManager(service)

    manager.enregistrer_utilisation()
    _create_product(SessionLocal, "Produit apres connexion")
    first_close = manager.fermer_application()
    second_close = manager.fermer_application()

    engine.dispose()

    assert first_close.created and first_close.reason == "fermeture"
    assert not second_close.created and second_close.reason == "deja_traitee"


def _environment(tmp_path):
    database_path = tmp_path / "app" / "data" / "salmospharm.sqlite3"
    database_path.parent.mkdir(parents=True)
    engine = create_app_engine(database_path)
    init_database(database_engine=engine)
    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )
    service = BackupService(
        database_path=database_path,
        backups_dir=tmp_path / "app" / "backups",
        assets_dir=tmp_path / "app" / "assets",
        factures_dir=tmp_path / "app" / "factures",
        restore_marker_path=tmp_path / "app" / "config" / "restore_pending.json",
        database_engine=engine,
        session_factory=SessionLocal,
    )
    return engine, SessionLocal, service


def _create_user(SessionLocal, role: str, email: str) -> SessionUtilisateur:
    with SessionLocal() as session:
        user = Utilisateur(
            nom=email.split("@")[0],
            email=email,
            mot_de_passe_hash="hash",
            role=role,
            actif=1,
        )
        session.add(user)
        session.commit()
        return SessionUtilisateur(user.id, user.nom, user.email, user.role)


def _create_product(SessionLocal, name: str) -> None:
    with SessionLocal() as session:
        session.add(
            Produit(
                nom=name,
                code_barres=name,
                prix_vente=1000,
                stock_minimum=0,
                actif=1,
            )
        )
        session.commit()
