"""Export et restauration locale des donnees au format `.spharm`."""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import tempfile
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy.engine import Engine

from app.core.constants import (
    ACTION_BACKUP_EXPORTE,
    ACTION_BACKUP_IMPORTE,
    ACTION_ERREUR_IMPORT_BACKUP,
    APP_NAME,
    APP_VERSION,
    BACKUP_FORMAT_VERSION,
)
from app.core.exceptions import BackupInvalideError, SalmospharmError
from app.core.paths import (
    get_assets_dir,
    get_backups_dir,
    get_database_path,
    get_factures_dir,
    get_restore_marker_path,
)
from app.core.permissions import (
    PERMISSION_GERER_BACKUP,
    PERMISSION_IMPORTER_DONNEES,
    exiger_permission,
)
from app.database.connection import SessionLocal, engine
from app.services.auth_service import SessionUtilisateur
from app.services.journal_service import JournalService
from app.utils.file_utils import safe_extract_archive, sha256_file, validate_archive_members


DATABASE_ARCHIVE_PATH = "database/salmospharm.sqlite3"
REQUIRED_TABLES = {
    "utilisateurs",
    "categories",
    "produits",
    "lots_produits",
    "mouvements_stock",
    "ventes",
    "lignes_vente",
    "alertes",
    "journaux_activite",
    "parametres",
}


@dataclass(frozen=True)
class BackupInfo:
    path: Path
    created_at: str
    app_version: str
    backup_version: int
    database_size: int
    assets_included: bool
    factures_included: bool


@dataclass(frozen=True)
class BackupExportResult:
    path: Path
    size: int
    created_at: str


@dataclass(frozen=True)
class BackupImportResult:
    security_backup_path: Path
    restart_required: bool = True


class BackupService:
    """Orchestre le backup SQLite, l'archive et le remplacement avec rollback."""

    def __init__(
        self,
        *,
        database_path: Path | None = None,
        backups_dir: Path | None = None,
        assets_dir: Path | None = None,
        factures_dir: Path | None = None,
        restore_marker_path: Path | None = None,
        database_engine: Engine = engine,
        session_factory=SessionLocal,
        journal_service: JournalService | None = None,
    ) -> None:
        self.database_path = database_path or get_database_path()
        self.backups_dir = backups_dir or get_backups_dir()
        self.assets_dir = assets_dir or get_assets_dir()
        self.factures_dir = factures_dir or get_factures_dir()
        self.restore_marker_path = restore_marker_path or get_restore_marker_path()
        self.database_engine = database_engine
        self.session_factory = session_factory
        self.journal_service = journal_service or JournalService()

    def exporter_backup(
        self,
        utilisateur: SessionUtilisateur,
        destination: str | Path | None = None,
    ) -> BackupExportResult:
        exiger_permission(utilisateur.role, PERMISSION_GERER_BACKUP)
        return self._exporter(
            destination=destination,
            utilisateur_id=utilisateur.utilisateur_id,
            journaliser=True,
        )

    def inspecter_backup(
        self,
        utilisateur: SessionUtilisateur,
        fichier: str | Path,
    ) -> BackupInfo:
        exiger_permission(utilisateur.role, PERMISSION_IMPORTER_DONNEES)
        return self._inspecter(Path(fichier))

    def importer_backup(
        self,
        utilisateur: SessionUtilisateur,
        fichier: str | Path,
    ) -> BackupImportResult:
        exiger_permission(utilisateur.role, PERMISSION_IMPORTER_DONNEES)
        source = Path(fichier)
        try:
            self._inspecter(source)
        except SalmospharmError:
            self._journaliser_erreur_import(utilisateur.utilisateur_id, source.name)
            raise

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        security_path = self.backups_dir / f"avant_import_{timestamp}.spharm"
        self._exporter(destination=security_path, utilisateur_id=None, journaliser=False)

        self.backups_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="restore_", dir=self.backups_dir) as temp_name:
            temp_dir = Path(temp_name)
            extracted = temp_dir / "incoming"
            with zipfile.ZipFile(source, "r") as archive:
                safe_extract_archive(archive, extracted)
            incoming_db = extracted / DATABASE_ARCHIVE_PATH
            self._validate_sqlite_database(incoming_db)
            self._replace_with_rollback(extracted, incoming_db, temp_dir)

        self.restore_marker_path.parent.mkdir(parents=True, exist_ok=True)
        self.restore_marker_path.write_text(
            json.dumps(
                {
                    "action": ACTION_BACKUP_IMPORTE,
                    "source": source.name,
                    "security_backup": str(security_path),
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                },
                ensure_ascii=True,
                indent=2,
            ),
            encoding="utf-8",
        )
        return BackupImportResult(security_backup_path=security_path)

    def finaliser_import_apres_redemarrage(self) -> bool:
        """Journalise l'import dans la base restauree puis retire le marqueur."""

        if not self.restore_marker_path.is_file():
            return False
        try:
            marker = json.loads(self.restore_marker_path.read_text(encoding="utf-8"))
            with self.session_factory() as session:
                self.journal_service.journaliser(
                    session,
                    action=ACTION_BACKUP_IMPORTE,
                    utilisateur_id=None,
                    table_cible="parametres",
                    details=(
                        f"Sauvegarde importee : {marker.get('source', 'inconnue')}. "
                        f"Sauvegarde de securite : {marker.get('security_backup', '')}."
                    ),
                )
                session.commit()
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            raise BackupInvalideError("Impossible de finaliser la restauration.") from exc
        self.restore_marker_path.unlink(missing_ok=True)
        return True

    def _exporter(
        self,
        *,
        destination: str | Path | None,
        utilisateur_id: int | None,
        journaliser: bool,
    ) -> BackupExportResult:
        if not self.database_path.is_file():
            raise BackupInvalideError("La base de donnees locale est introuvable.")

        created_at = datetime.now().isoformat(timespec="seconds")
        default_name = f"salmospharm_backup_{datetime.now():%Y-%m-%d_%H-%M}.spharm"
        output = Path(destination) if destination else self.backups_dir / default_name
        if output.suffix.lower() != ".spharm":
            output = output.with_suffix(".spharm")
        output.parent.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="backup_", dir=self.backups_dir) as temp_name:
            temp_dir = Path(temp_name)
            snapshot = temp_dir / "salmospharm.sqlite3"
            self._sqlite_backup(self.database_path, snapshot)
            self._validate_sqlite_database(snapshot)
            manifest = self._build_manifest(snapshot, created_at)
            archive_temp = temp_dir / "backup.spharm"
            with zipfile.ZipFile(archive_temp, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.write(snapshot, DATABASE_ARCHIVE_PATH)
                self._add_directory(archive, self.assets_dir, "assets")
                self._add_directory(archive, self.factures_dir, "factures")
                archive.writestr(
                    "manifest.json",
                    json.dumps(manifest, ensure_ascii=True, indent=2),
                )
            if journaliser:
                self._journaliser_export(utilisateur_id, output.name)
            staged_output = output.with_name(f".{output.name}.{uuid.uuid4().hex}.tmp")
            shutil.copy2(archive_temp, staged_output)
            os.replace(staged_output, output)
        return BackupExportResult(path=output, size=output.stat().st_size, created_at=created_at)

    def _inspecter(self, path: Path) -> BackupInfo:
        if path.suffix.lower() != ".spharm" or not path.is_file():
            raise BackupInvalideError("Ce fichier de sauvegarde n'est pas valide.")
        try:
            with zipfile.ZipFile(path, "r") as archive:
                validate_archive_members(archive)
                if "manifest.json" not in archive.namelist() or DATABASE_ARCHIVE_PATH not in archive.namelist():
                    raise BackupInvalideError("La sauvegarde est incomplete.")
                manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
                self._validate_manifest(manifest)
                with tempfile.TemporaryDirectory(prefix="inspect_") as temp_name:
                    database = Path(temp_name) / "salmospharm.sqlite3"
                    with archive.open(DATABASE_ARCHIVE_PATH) as source, database.open("wb") as output:
                        shutil.copyfileobj(source, output)
                    if sha256_file(database) != manifest["database"]["sha256"]:
                        raise BackupInvalideError("La base de la sauvegarde a ete modifiee.")
                    self._validate_sqlite_database(database)
        except (zipfile.BadZipFile, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            if isinstance(exc, BackupInvalideError):
                raise
            raise BackupInvalideError("Ce fichier de sauvegarde n'est pas valide.") from exc
        return BackupInfo(
            path=path,
            created_at=str(manifest["date_creation"]),
            app_version=str(manifest["version_application"]),
            backup_version=int(manifest["version_backup"]),
            database_size=int(manifest["database"]["taille"]),
            assets_included=bool(manifest["assets_presents"]),
            factures_included=bool(manifest["factures_presentes"]),
        )

    def _replace_with_rollback(self, extracted: Path, incoming_db: Path, temp_dir: Path) -> None:
        rollback_db = temp_dir / "rollback.sqlite3"
        rollback_assets = temp_dir / "rollback_assets"
        rollback_factures = temp_dir / "rollback_factures"
        staged_db = self.database_path.with_name(f".restore-{uuid.uuid4().hex}.sqlite3")
        shutil.copy2(incoming_db, staged_db)
        if self.assets_dir.exists():
            shutil.copytree(self.assets_dir, rollback_assets)
        if self.factures_dir.exists():
            shutil.copytree(self.factures_dir, rollback_factures)

        self.database_engine.dispose(close=True)
        try:
            if self.database_path.exists():
                os.replace(self.database_path, rollback_db)
            os.replace(staged_db, self.database_path)
            self._restore_optional_directory(extracted / "assets", self.assets_dir)
            self._restore_optional_directory(extracted / "factures", self.factures_dir)
            self._validate_sqlite_database(self.database_path)
        except Exception:
            staged_db.unlink(missing_ok=True)
            if rollback_db.exists():
                self.database_path.unlink(missing_ok=True)
                os.replace(rollback_db, self.database_path)
            self._restore_rollback_directory(rollback_assets, self.assets_dir)
            self._restore_rollback_directory(rollback_factures, self.factures_dir)
            raise BackupInvalideError(
                "La restauration a echoue. Les donnees precedentes ont ete conservees."
            )

    @staticmethod
    def _sqlite_backup(source_path: Path, destination_path: Path) -> None:
        source = sqlite3.connect(f"file:{source_path.as_posix()}?mode=ro", uri=True)
        destination = sqlite3.connect(destination_path)
        try:
            source.backup(destination)
        finally:
            destination.close()
            source.close()

    @staticmethod
    def _validate_sqlite_database(path: Path) -> None:
        try:
            connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
            integrity = connection.execute("PRAGMA integrity_check").fetchone()
            foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
        except sqlite3.DatabaseError as exc:
            raise BackupInvalideError("La base SQLite de la sauvegarde est corrompue.") from exc
        finally:
            if "connection" in locals():
                connection.close()
        if not integrity or integrity[0] != "ok" or foreign_keys:
            raise BackupInvalideError("La base SQLite de la sauvegarde est incoherente.")
        if not REQUIRED_TABLES.issubset(tables):
            raise BackupInvalideError("La sauvegarde ne contient pas le schema SALMOSPHARM attendu.")

    def _build_manifest(self, snapshot: Path, created_at: str) -> dict:
        assets_present = self.assets_dir.is_dir() and any(self.assets_dir.rglob("*"))
        factures_presentes = self.factures_dir.is_dir() and any(self.factures_dir.rglob("*"))
        return {
            "application": APP_NAME,
            "version_application": APP_VERSION,
            "version_backup": BACKUP_FORMAT_VERSION,
            "date_creation": created_at,
            "database": {
                "presente": True,
                "chemin": DATABASE_ARCHIVE_PATH,
                "taille": snapshot.stat().st_size,
                "sha256": sha256_file(snapshot),
            },
            "assets_presents": assets_present,
            "factures_presentes": factures_presentes,
        }

    @staticmethod
    def _validate_manifest(manifest: dict) -> None:
        if manifest.get("application") != APP_NAME:
            raise BackupInvalideError("Cette sauvegarde appartient a une autre application.")
        if manifest.get("version_backup") != BACKUP_FORMAT_VERSION:
            raise BackupInvalideError("Cette version de sauvegarde n'est pas compatible.")
        database = manifest.get("database")
        if not isinstance(database, dict) or not database.get("presente"):
            raise BackupInvalideError("La sauvegarde ne contient pas de base de donnees.")
        if database.get("chemin") != DATABASE_ARCHIVE_PATH:
            raise BackupInvalideError("Le manifeste de la sauvegarde est invalide.")
        if not isinstance(database.get("sha256"), str) or not isinstance(database.get("taille"), int):
            raise BackupInvalideError("Le manifeste de la sauvegarde est invalide.")

    @staticmethod
    def _add_directory(archive: zipfile.ZipFile, source: Path, archive_root: str) -> None:
        if not source.is_dir():
            return
        for path in source.rglob("*"):
            if path.is_file():
                archive.write(path, (Path(archive_root) / path.relative_to(source)).as_posix())

    @staticmethod
    def _restore_optional_directory(source: Path, target: Path) -> None:
        if not source.is_dir():
            return
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)

    @staticmethod
    def _restore_rollback_directory(source: Path, target: Path) -> None:
        if target.exists():
            shutil.rmtree(target)
        if source.exists():
            shutil.copytree(source, target)

    def _journaliser_export(self, utilisateur_id: int | None, filename: str) -> None:
        with self.session_factory() as session:
            self.journal_service.journaliser(
                session,
                action=ACTION_BACKUP_EXPORTE,
                utilisateur_id=utilisateur_id,
                table_cible="parametres",
                details=f"Sauvegarde exportee : {filename}.",
            )
            session.commit()

    def _journaliser_erreur_import(self, utilisateur_id: int | None, filename: str) -> None:
        try:
            with self.session_factory() as session:
                self.journal_service.journaliser(
                    session,
                    action=ACTION_ERREUR_IMPORT_BACKUP,
                    utilisateur_id=utilisateur_id,
                    table_cible="parametres",
                    details=f"Echec de validation du backup : {filename}.",
                )
                session.commit()
        except Exception:
            pass
