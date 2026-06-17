from pathlib import Path

from app.core.paths import (
    get_assets_dir,
    get_backups_dir,
    get_data_dir,
    get_database_path,
    get_exports_dir,
    get_factures_dir,
    get_logs_dir,
    get_user_data_dir,
    ensure_app_directories,
)


def test_ensure_app_directories_creates_expected_tree(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    ensure_app_directories()

    expected_directories = (
        get_user_data_dir(),
        get_data_dir(),
        get_backups_dir(),
        get_logs_dir(),
        get_factures_dir(),
        get_exports_dir(),
        get_assets_dir(),
    )

    for directory in expected_directories:
        assert directory.is_dir()

    assert get_database_path() == Path(tmp_path) / "SALMOSPHARM" / "data" / "salmospharm.sqlite3"
    assert not get_database_path().exists()
