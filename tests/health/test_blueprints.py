"""Tests for BlueprintHealthChecker (SPEC-012). Reuses Phase 3 validation."""

from __future__ import annotations

import json
from pathlib import Path

from pipelinekit.health import ERROR, OK
from pipelinekit.health.blueprints import BlueprintHealthChecker

_VALID_BLUEPRINT = {
    "name": "demo-blueprint",
    "version": "1.0.0",
    "source": {"type": "postgres"},
    "destination": {"type": "snowflake"},
    "contracts": ["orders"],
}


def _install(base: Path, name: str, data: dict) -> None:
    bp_dir = base / "blueprints" / name
    bp_dir.mkdir(parents=True)
    (bp_dir / "blueprint.json").write_text(json.dumps(data), encoding="utf-8")


def test_ok_when_blueprint_valid(tmp_path):
    """A schema-valid blueprint → status ok."""
    _install(tmp_path, "demo-blueprint", _VALID_BLUEPRINT)
    result = BlueprintHealthChecker().check(cwd=tmp_path)
    assert result.status == OK
    assert "1 blueprint" in result.message


def test_error_when_blueprint_schema_fails(tmp_path):
    """A blueprint missing required fields → status error."""
    _install(tmp_path, "broken", {"name": "broken"})  # missing required fields
    result = BlueprintHealthChecker().check(cwd=tmp_path)
    assert result.status == ERROR
    assert any("broken" in d for d in result.details or [])


def test_ok_when_no_blueprints_installed(tmp_path):
    """No blueprints directory → status ok (not an error)."""
    result = BlueprintHealthChecker().check(cwd=tmp_path)
    assert result.status == OK
    assert "No blueprints" in result.message
