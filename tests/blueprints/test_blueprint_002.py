"""Tests for Blueprint #002 (Salesforce → Snowflake), SPEC-013.

Validates the blueprint's metadata, registry visibility, and reference config.
No live Salesforce API — these exercise structure only.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pipelinekit.blueprints.models import BlueprintMetadata
from pipelinekit.blueprints.registry import BlueprintRegistry
from pipelinekit.blueprints.validator import BlueprintValidator
from pipelinekit.config.loader import _interpolate_env_vars
from pipelinekit.config.schema import PipelineConfig

_REPO = Path(__file__).resolve().parents[2]
_BLUEPRINTS = _REPO / "blueprints"
_SF = _BLUEPRINTS / "salesforce-to-snowflake"

_SF_ENV = (
    "SALESFORCE_USERNAME",
    "SALESFORCE_PASSWORD",
    "SALESFORCE_SECURITY_TOKEN",
    "SNOWFLAKE_ACCOUNT",
    "SNOWFLAKE_USER",
    "SNOWFLAKE_PASSWORD",
    "SNOWFLAKE_DATABASE",
    "SNOWFLAKE_WAREHOUSE",
)


def test_blueprint_002_validates_against_schema():
    """blueprint.json validates against schemas/blueprint.schema.json."""
    BlueprintValidator().validate(_SF)  # raises BlueprintError on invalid


def test_blueprint_info_returns_correct_metadata():
    """The registry resolves salesforce-to-snowflake with correct metadata."""
    meta = BlueprintRegistry(_BLUEPRINTS).get("salesforce-to-snowflake")
    assert isinstance(meta, BlueprintMetadata)
    assert meta.name == "salesforce-to-snowflake"
    assert meta.version == "1.0.0"
    assert meta.source.type == "salesforce"
    assert meta.destination.type == "snowflake"
    assert "contracts/opportunities.yaml" in meta.contracts


def test_blueprint_list_shows_both_blueprints():
    """The registry lists both Blueprint #001 and #002."""
    names = {b.name for b in BlueprintRegistry(_BLUEPRINTS).list()}
    assert "postgres-to-snowflake" in names
    assert "salesforce-to-snowflake" in names


def test_example_yaml_loads_through_pipelineconfig(monkeypatch):
    """pipelinekit.example.yaml loads cleanly with ${VAR} interpolation."""
    for var in _SF_ENV:
        monkeypatch.setenv(var, "x")
    raw = _interpolate_env_vars(
        yaml.safe_load((_SF / "pipelinekit.example.yaml").read_text(encoding="utf-8"))
    )
    config = PipelineConfig(**raw)
    assert config.ingestion.source.type == "salesforce"
    assert config.ingestion.source.username == "x"
    assert config.ingestion.source.security_token == "x"
    assert config.ingestion.destination.type == "snowflake"
    assert config.ingestion.destination.warehouse == "x"
