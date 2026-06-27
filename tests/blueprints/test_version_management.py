"""Tests for Blueprint Version Management (SPEC-018). Registry calls mocked.

Covers RemoteRegistry.outdated() / upgrade() / rollback(): version comparison,
backup-before-write, the already-latest guard, dry-run safety, and the
no-backup rollback guard. No network is touched.
"""

from __future__ import annotations

import io
import json
import zipfile
from unittest.mock import patch

import pytest
from pipelinekit.blueprints.remote import BlueprintCatalog, RemoteRegistry
from pipelinekit.core.errors import RegistryError
from pipelinekit.state import db


def _catalog(postgres_version: str) -> dict:
    """A catalog with postgres at ``postgres_version`` (with a changelog)."""
    return {
        "version": "1.0",
        "updated_at": "2026-06-26T00:00:00Z",
        "blueprints": [
            {
                "name": "postgres-to-snowflake",
                "version": postgres_version,
                "description": "Postgres to Snowflake",
                "source": "postgres",
                "destination": "snowflake",
                "verified": True,
                "verified_at": "2026-06-26",
                "verified_by": "mpingo-systems",
                "downloads": 0,
                "tags": ["postgres", "sql"],
                "url": (
                    "https://registry.pipelinekit.dev/v1/blueprints/"
                    f"postgres-to-snowflake-{postgres_version}.zip"
                ),
                "changelog": {postgres_version: ["Test changelog line"]},
            }
        ],
    }


def _blueprint_json(version: str) -> str:
    return json.dumps(
        {
            "name": "postgres-to-snowflake",
            "version": version,
            "source": {"type": "postgres", "dlt_source": "sql_database"},
            "destination": {"type": "snowflake", "dlt_destination": "snowflake"},
            "contracts": ["contracts/orders.yaml"],
        }
    )


def _make_zip(version: str) -> bytes:
    """Build an in-memory blueprint zip with all (lenient) required assets."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("blueprint.json", _blueprint_json(version))
        for path in (
            "ingestion/pipeline.py",
            "transform/dbt_project.yml",
            "contracts/orders.yaml",
            "quality/checks.yaml",
            "alerts/config.yaml",
            "docs/README.md",
            "docs/runbook.md",
        ):
            zf.writestr(path, "x\n")
    return buf.getvalue()


def _registry(tmp_path) -> RemoteRegistry:
    return RemoteRegistry(cache_dir=tmp_path / "cache")


def _seed_installed(tmp_path, version: str = "1.0.0") -> None:
    """Record postgres as installed at ``version`` in this project's state."""
    db.insert_installed_blueprint(
        "postgres-to-snowflake",
        version,
        "postgres",
        "snowflake",
        True,
        "https://registry.pipelinekit.dev/v1/blueprints/"
        f"postgres-to-snowflake-{version}.zip",
        cwd=tmp_path,
    )


def _seed_blueprint_on_disk(tmp_path, version: str = "1.0.0") -> None:
    """Write a minimal installed blueprint dir at the given version."""
    bp = tmp_path / "blueprints" / "postgres-to-snowflake"
    bp.mkdir(parents=True, exist_ok=True)
    (bp / "blueprint.json").write_text(_blueprint_json(version), encoding="utf-8")


def test_outdated_returns_correct_comparison(tmp_path):
    """outdated() flags an installed blueprint with a newer registry version."""
    registry = _registry(tmp_path)
    registry._write_cache(BlueprintCatalog.from_dict(_catalog("1.1.0")))
    _seed_installed(tmp_path, "1.0.0")
    result = registry.outdated(cwd=tmp_path)
    assert len(result) == 1
    assert result[0]["name"] == "postgres-to-snowflake"
    assert result[0]["installed_version"] == "1.0.0"
    assert result[0]["registry_version"] == "1.1.0"
    assert result[0]["outdated"] is True


def test_outdated_empty_when_all_current(tmp_path):
    """outdated() returns an empty list when every blueprint is current."""
    registry = _registry(tmp_path)
    registry._write_cache(BlueprintCatalog.from_dict(_catalog("1.0.0")))
    _seed_installed(tmp_path, "1.0.0")
    assert registry.outdated(cwd=tmp_path) == []


def test_upgrade_backs_up_before_writing_new_version(tmp_path):
    """upgrade() backs up the existing blueprint, then writes the new version."""
    registry = _registry(tmp_path)
    registry._write_cache(BlueprintCatalog.from_dict(_catalog("1.1.0")))
    _seed_installed(tmp_path, "1.0.0")
    _seed_blueprint_on_disk(tmp_path, "1.0.0")

    with patch.object(registry, "_http_get", return_value=_make_zip("1.1.0")):
        new_version = registry.upgrade("postgres-to-snowflake", yes=True, cwd=tmp_path)

    assert new_version == "1.1.0"
    backup = (
        tmp_path
        / ".pipelinekit"
        / "backups"
        / "postgres-to-snowflake-1.0.0"
        / "blueprint.json"
    )
    assert backup.is_file()
    assert '"version": "1.0.0"' in backup.read_text(encoding="utf-8")
    installed = tmp_path / "blueprints" / "postgres-to-snowflake" / "blueprint.json"
    assert '"version": "1.1.0"' in installed.read_text(encoding="utf-8")


def test_upgrade_raises_pk_registry_006_when_already_latest(tmp_path):
    """upgrade() raises PK-REGISTRY-006 when already at the latest version."""
    registry = _registry(tmp_path)
    registry._write_cache(BlueprintCatalog.from_dict(_catalog("1.0.0")))
    _seed_installed(tmp_path, "1.0.0")
    with pytest.raises(RegistryError) as exc_info:
        registry.upgrade("postgres-to-snowflake", yes=True, cwd=tmp_path)
    assert exc_info.value.code == "PK-REGISTRY-006"


def test_upgrade_dry_run_writes_nothing(tmp_path):
    """upgrade(dry_run=True) returns the target version but writes no files."""
    registry = _registry(tmp_path)
    registry._write_cache(BlueprintCatalog.from_dict(_catalog("1.1.0")))
    _seed_installed(tmp_path, "1.0.0")
    _seed_blueprint_on_disk(tmp_path, "1.0.0")

    with patch.object(
        registry, "_http_get", side_effect=AssertionError("must not download")
    ):
        target = registry.upgrade("postgres-to-snowflake", dry_run=True, cwd=tmp_path)

    assert target == "1.1.0"
    assert not (tmp_path / ".pipelinekit" / "backups").exists()
    installed = tmp_path / "blueprints" / "postgres-to-snowflake" / "blueprint.json"
    assert '"version": "1.0.0"' in installed.read_text(encoding="utf-8")


def test_rollback_raises_pk_registry_007_when_no_backup(tmp_path):
    """rollback() raises PK-REGISTRY-007 when no backup exists for the blueprint."""
    registry = _registry(tmp_path)
    with pytest.raises(RegistryError) as exc_info:
        registry.rollback("postgres-to-snowflake", cwd=tmp_path)
    assert exc_info.value.code == "PK-REGISTRY-007"
