"""Tests for BlueprintValidator (SPEC-006). Validates against the real schema."""

from __future__ import annotations

import json

import pytest
from pipelinekit.blueprints.validator import BlueprintValidator
from pipelinekit.core.errors import BlueprintError

_VALID = {
    "name": "postgres-to-snowflake",
    "version": "1.0.0",
    "source": {"type": "postgres", "dlt_source": "sql_database"},
    "destination": {"type": "snowflake", "dlt_destination": "snowflake"},
    "contracts": ["contracts/orders.yaml"],
}


def test_valid_blueprint_passes(tmp_path):
    """A valid blueprint.json passes validation without raising."""
    (tmp_path / "blueprint.json").write_text(json.dumps(_VALID), encoding="utf-8")
    BlueprintValidator().validate(tmp_path)


def test_invalid_blueprint_raises_001(tmp_path):
    """A blueprint missing required fields raises PK-BLUEPRINT-001."""
    incomplete = {
        "name": "x",
        "version": "1.0.0",
    }  # missing source/destination/contracts
    (tmp_path / "blueprint.json").write_text(json.dumps(incomplete), encoding="utf-8")
    with pytest.raises(BlueprintError) as exc_info:
        BlueprintValidator().validate(tmp_path)
    assert exc_info.value.code == "PK-BLUEPRINT-001"


def test_missing_blueprint_raises_002(tmp_path):
    """A missing blueprint.json raises PK-BLUEPRINT-002."""
    with pytest.raises(BlueprintError) as exc_info:
        BlueprintValidator().validate(tmp_path)
    assert exc_info.value.code == "PK-BLUEPRINT-002"


def test_invalid_json_raises_001(tmp_path):
    """A malformed blueprint.json raises PK-BLUEPRINT-001."""
    (tmp_path / "blueprint.json").write_text("{ not json", encoding="utf-8")
    with pytest.raises(BlueprintError) as exc_info:
        BlueprintValidator().validate(tmp_path)
    assert exc_info.value.code == "PK-BLUEPRINT-001"


def test_shipped_blueprint_001_validates():
    """The shipped Blueprint #001 validates against the schema."""
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    blueprint_dir = repo_root / "blueprints" / "postgres-to-snowflake"
    BlueprintValidator().validate(blueprint_dir)
