"""CLI tests for blueprint outdated / upgrade / rollback (SPEC-018).

RemoteRegistry is mocked — no network, no filesystem mutation.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pipelinekit.blueprints.remote import BlueprintCatalog, CatalogEntry
from pipelinekit.cli.main import app
from pipelinekit.core.errors import RegistryError
from typer.testing import CliRunner

runner = CliRunner()


def _entry(version: str = "1.1.0") -> CatalogEntry:
    return CatalogEntry(
        name="postgres-to-snowflake",
        version=version,
        description="Postgres to Snowflake",
        source="postgres",
        destination="snowflake",
        verified=True,
        verified_at="2026-06-26",
        verified_by="mpingo-systems",
        downloads=0,
        tags=["postgres"],
        url="https://registry.pipelinekit.dev/v1/blueprints/postgres-to-snowflake-1.1.0.zip",
        changelog={version: ["Improved contracts — freshness SLA"]},
    )


def _registry_mock() -> MagicMock:
    reg = MagicMock()
    reg.fetch_catalog.return_value = BlueprintCatalog(
        version="1.0", updated_at="", blueprints=[_entry()]
    )
    return reg


def test_outdated_table_shows_update_available(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reg = _registry_mock()
    reg.version_status.return_value = [
        {
            "name": "postgres-to-snowflake",
            "installed_version": "1.0.0",
            "registry_version": "1.1.0",
            "outdated": True,
        }
    ]
    with patch("pipelinekit.cli.blueprint.RemoteRegistry", return_value=reg):
        result = runner.invoke(app, ["blueprint", "outdated"])
    assert result.exit_code == 0
    assert "Update available" in result.stdout
    assert "can be upgraded" in result.stdout


def test_outdated_all_current(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reg = _registry_mock()
    reg.version_status.return_value = [
        {
            "name": "postgres-to-snowflake",
            "installed_version": "1.0.0",
            "registry_version": "1.0.0",
            "outdated": False,
        }
    ]
    with patch("pipelinekit.cli.blueprint.RemoteRegistry", return_value=reg):
        result = runner.invoke(app, ["blueprint", "outdated"])
    assert result.exit_code == 0
    assert "All blueprints are up to date" in result.stdout


def test_outdated_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reg = _registry_mock()
    reg.version_status.return_value = [
        {
            "name": "postgres-to-snowflake",
            "installed_version": "1.0.0",
            "registry_version": "1.1.0",
            "outdated": True,
        }
    ]
    with patch("pipelinekit.cli.blueprint.RemoteRegistry", return_value=reg):
        result = runner.invoke(app, ["blueprint", "outdated", "--json"])
    assert result.exit_code == 0
    assert "checked_at" in result.stdout
    assert "postgres-to-snowflake" in result.stdout


def test_upgrade_dry_run(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reg = _registry_mock()
    reg.version_status.return_value = [
        {
            "name": "postgres-to-snowflake",
            "installed_version": "1.0.0",
            "registry_version": "1.1.0",
            "outdated": True,
        }
    ]
    reg.upgrade.return_value = "1.1.0"
    with patch("pipelinekit.cli.blueprint.RemoteRegistry", return_value=reg):
        result = runner.invoke(
            app, ["blueprint", "upgrade", "postgres-to-snowflake", "--dry-run"]
        )
    assert result.exit_code == 0
    assert "Would upgrade" in result.stdout
    assert "No files written" in result.stdout


def test_upgrade_already_latest_reports_pk_registry_006(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reg = _registry_mock()
    reg.version_status.return_value = []
    reg.upgrade.side_effect = RegistryError(
        "PK-REGISTRY-006", "postgres-to-snowflake is already at the latest version.", {}
    )
    with patch("pipelinekit.cli.blueprint.RemoteRegistry", return_value=reg):
        result = runner.invoke(app, ["blueprint", "upgrade", "postgres-to-snowflake"])
    assert result.exit_code == 1
    assert "PK-REGISTRY-006" in result.stdout


def test_upgrade_applies_with_yes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reg = _registry_mock()
    reg.version_status.return_value = [
        {
            "name": "postgres-to-snowflake",
            "installed_version": "1.0.0",
            "registry_version": "1.1.0",
            "outdated": True,
        }
    ]
    reg.upgrade.return_value = "1.1.0"
    with patch("pipelinekit.cli.blueprint.RemoteRegistry", return_value=reg):
        result = runner.invoke(
            app, ["blueprint", "upgrade", "postgres-to-snowflake", "--yes"]
        )
    assert result.exit_code == 0
    assert "upgraded to v1.1.0" in result.stdout
    assert "Changes in 1.1.0" in result.stdout


def test_rollback_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reg = _registry_mock()
    reg.rollback.return_value = "1.0.0"
    with patch("pipelinekit.cli.blueprint.RemoteRegistry", return_value=reg):
        result = runner.invoke(app, ["blueprint", "rollback", "postgres-to-snowflake"])
    assert result.exit_code == 0
    assert "rolled back to v1.0.0" in result.stdout


def test_rollback_no_backup_reports_pk_registry_007(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reg = _registry_mock()
    reg.rollback.side_effect = RegistryError(
        "PK-REGISTRY-007", "No backup found for postgres-to-snowflake.", {}
    )
    with patch("pipelinekit.cli.blueprint.RemoteRegistry", return_value=reg):
        result = runner.invoke(app, ["blueprint", "rollback", "postgres-to-snowflake"])
    assert result.exit_code == 1
    assert "PK-REGISTRY-007" in result.stdout
