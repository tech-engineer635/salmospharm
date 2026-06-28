"""Gestion centralisee des chemins locaux de SALMOSPHARM."""

from __future__ import annotations

import os
from pathlib import Path


APP_DATA_DIR_NAME = "SALMOSPHARM"
DATABASE_FILE_NAME = "salmospharm.sqlite3"


def get_local_appdata_dir() -> Path:
    """Retourne le dossier AppData/Local de l'utilisateur Windows."""
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        return Path(local_appdata)

    return Path.home() / "AppData" / "Local"


def get_user_data_dir() -> Path:
    return get_local_appdata_dir() / APP_DATA_DIR_NAME


def get_data_dir() -> Path:
    return get_user_data_dir() / "data"


def get_backups_dir() -> Path:
    return get_user_data_dir() / "backups"


def get_logs_dir() -> Path:
    return get_user_data_dir() / "logs"


def get_factures_dir() -> Path:
    return get_user_data_dir() / "factures"


def get_exports_dir() -> Path:
    return get_user_data_dir() / "exports"


def get_assets_dir() -> Path:
    return get_user_data_dir() / "assets"


def get_config_dir() -> Path:
    return get_user_data_dir() / "config"


def get_restore_marker_path() -> Path:
    return get_config_dir() / "restore_pending.json"


def get_database_path() -> Path:
    return get_data_dir() / DATABASE_FILE_NAME


def iter_app_directories() -> tuple[Path, ...]:
    return (
        get_user_data_dir(),
        get_data_dir(),
        get_backups_dir(),
        get_logs_dir(),
        get_factures_dir(),
        get_exports_dir(),
        get_assets_dir(),
        get_config_dir(),
    )


def ensure_app_directories() -> None:
    for directory in iter_app_directories():
        directory.mkdir(parents=True, exist_ok=True)


def ensure_app_dirs() -> None:
    """Alias conserve pour correspondre aux documents projet."""
    ensure_app_directories()
