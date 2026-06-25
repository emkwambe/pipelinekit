"""Tests for the PipelineConfig Pydantic schema (SPEC-002)."""

from __future__ import annotations

import pytest
from pipelinekit.config.schema import PipelineConfig
from pydantic import ValidationError


def _valid_config_dict() -> dict:
    """Return a minimal, fully valid configuration dictionary."""
    return {
        "pipeline": {"name": "demo"},
        "runtime": {"environment": "local"},
        "ingestion": {
            "source": {"type": "postgres"},
            "destination": {"type": "snowflake"},
        },
        "transformation": {},
        "contracts": {},
        "quality": {},
        "diagnostics": {},
        "notifications": {},
    }


def test_valid_config_loads():
    """A full valid dict loads into PipelineConfig without error."""
    config = PipelineConfig(**_valid_config_dict())
    assert config.pipeline.name == "demo"
    assert config.ingestion.source.type == "postgres"


def test_missing_pipeline_section_fails():
    """PipelineConfig raises when the pipeline section is absent."""
    data = _valid_config_dict()
    del data["pipeline"]
    with pytest.raises(ValidationError):
        PipelineConfig(**data)


def test_missing_ingestion_section_fails():
    """PipelineConfig raises when the ingestion section is absent."""
    data = _valid_config_dict()
    del data["ingestion"]
    with pytest.raises(ValidationError):
        PipelineConfig(**data)


def test_default_values_applied():
    """Optional fields receive their documented defaults."""
    config = PipelineConfig(**_valid_config_dict())
    assert config.pipeline.version == "0.1.0"
    assert config.pipeline.description == ""
    assert config.transformation.enabled is False
    assert config.transformation.project_dir == "./transform"
    assert config.contracts.enabled is True
    assert config.diagnostics.provider == "none"
    assert config.notifications.channels == []
