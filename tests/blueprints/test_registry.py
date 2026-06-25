"""Tests for BlueprintRegistry (SPEC-006). All file system via tmp_path."""

from __future__ import annotations

import json

from pipelinekit.blueprints.registry import BlueprintRegistry

_BLUEPRINT = {
    "name": "postgres-to-snowflake",
    "version": "1.0.0",
    "source": {"type": "postgres", "dlt_source": "sql_database"},
    "destination": {"type": "snowflake", "dlt_destination": "snowflake"},
    "contracts": ["contracts/orders.yaml"],
}


def _install(blueprints_dir, name: str, data: dict) -> None:
    bp_dir = blueprints_dir / name
    bp_dir.mkdir(parents=True)
    (bp_dir / "blueprint.json").write_text(json.dumps(data), encoding="utf-8")


def test_list_empty_when_dir_absent(tmp_path):
    """list() returns [] when the blueprints directory does not exist."""
    registry = BlueprintRegistry(tmp_path / "nope")
    assert registry.list() == []


def test_list_returns_installed_blueprint(tmp_path):
    """list() returns metadata for a valid installed blueprint."""
    _install(tmp_path, "postgres-to-snowflake", _BLUEPRINT)
    blueprints = BlueprintRegistry(tmp_path).list()
    assert len(blueprints) == 1
    assert blueprints[0].name == "postgres-to-snowflake"


def test_get_returns_existing(tmp_path):
    """get() returns metadata for an installed blueprint."""
    _install(tmp_path, "postgres-to-snowflake", _BLUEPRINT)
    bp = BlueprintRegistry(tmp_path).get("postgres-to-snowflake")
    assert bp is not None
    assert bp.version == "1.0.0"


def test_get_returns_none_for_missing(tmp_path):
    """get() returns None for a blueprint that is not installed."""
    assert BlueprintRegistry(tmp_path).get("does-not-exist") is None


def test_malformed_blueprint_is_skipped(tmp_path):
    """A malformed blueprint.json is skipped, never fatal."""
    bad = tmp_path / "broken"
    bad.mkdir()
    (bad / "blueprint.json").write_text("{ not json", encoding="utf-8")
    _install(tmp_path, "postgres-to-snowflake", _BLUEPRINT)
    blueprints = BlueprintRegistry(tmp_path).list()
    assert [bp.name for bp in blueprints] == ["postgres-to-snowflake"]


def test_exists(tmp_path):
    """exists() reflects installation state."""
    _install(tmp_path, "postgres-to-snowflake", _BLUEPRINT)
    registry = BlueprintRegistry(tmp_path)
    assert registry.exists("postgres-to-snowflake") is True
    assert registry.exists("other") is False
