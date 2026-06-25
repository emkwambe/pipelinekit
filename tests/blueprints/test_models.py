"""Tests for blueprint models (SPEC-006)."""

from __future__ import annotations

import pytest
from pipelinekit.blueprints.models import (
    BlueprintDestination,
    BlueprintMetadata,
    BlueprintSource,
)
from pydantic import ValidationError


def _valid_blueprint_dict() -> dict:
    return {
        "name": "postgres-to-snowflake",
        "version": "1.0.0",
        "description": "Postgres to Snowflake",
        "source": {"type": "postgres", "dlt_source": "sql_database"},
        "destination": {"type": "snowflake", "dlt_destination": "snowflake"},
        "contracts": ["contracts/orders.yaml"],
        "kpis": ["Daily Orders"],
    }


def test_valid_blueprint_loads():
    """A valid blueprint dict loads into BlueprintMetadata."""
    bp = BlueprintMetadata(**_valid_blueprint_dict())
    assert bp.name == "postgres-to-snowflake"
    assert bp.source.type == "postgres"
    assert bp.destination.dlt_destination == "snowflake"
    assert bp.deploy_time_minutes == 60


def test_missing_required_field_raises():
    """Omitting a required field raises ValidationError."""
    data = _valid_blueprint_dict()
    del data["source"]
    with pytest.raises(ValidationError):
        BlueprintMetadata(**data)


def test_source_and_destination_models_load():
    """BlueprintSource and BlueprintDestination load from dicts."""
    source = BlueprintSource(type="postgres", dlt_source="sql_database")
    dest = BlueprintDestination(type="snowflake", dlt_destination="snowflake")
    assert source.dlt_source == "sql_database"
    assert dest.type == "snowflake"
