"""Utilitaires de fichiers pour les archives locales SALMOSPHARM."""

from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path, PurePosixPath

from app.core.exceptions import BackupInvalideError


MAX_BACKUP_FILES = 5_000
MAX_BACKUP_UNCOMPRESSED_BYTES = 2 * 1024 * 1024 * 1024
ALLOWED_BACKUP_ROOTS = {"database", "assets", "factures"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_archive_members(archive: zipfile.ZipFile) -> None:
    """Refuse les chemins dangereux, liens et contenus hors format."""

    members = archive.infolist()
    if len(members) > MAX_BACKUP_FILES:
        raise BackupInvalideError("Cette sauvegarde contient trop de fichiers.")
    if sum(item.file_size for item in members) > MAX_BACKUP_UNCOMPRESSED_BYTES:
        raise BackupInvalideError("Cette sauvegarde est trop volumineuse.")

    for item in members:
        path = PurePosixPath(item.filename)
        if path.is_absolute() or ".." in path.parts or "\\" in item.filename:
            raise BackupInvalideError("Cette sauvegarde contient un chemin non autorise.")
        if item.filename == "manifest.json":
            continue
        if not path.parts or path.parts[0] not in ALLOWED_BACKUP_ROOTS:
            raise BackupInvalideError("Cette sauvegarde contient un fichier non autorise.")
        unix_mode = item.external_attr >> 16
        if unix_mode and (unix_mode & 0o170000) == 0o120000:
            raise BackupInvalideError("Les liens symboliques sont interdits dans une sauvegarde.")


def safe_extract_archive(archive: zipfile.ZipFile, destination: Path) -> None:
    validate_archive_members(archive)
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    for item in archive.infolist():
        target = (destination / PurePosixPath(item.filename)).resolve()
        if target != root and root not in target.parents:
            raise BackupInvalideError("Cette sauvegarde contient un chemin non autorise.")
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(item) as source, target.open("wb") as output:
            shutil.copyfileobj(source, output)
