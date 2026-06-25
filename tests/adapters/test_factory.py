"""Tests for AdapterFactory (SPEC-009)."""

from __future__ import annotations

from pipelinekit.adapters.factory import AdapterFactory
from pipelinekit.adapters.ingestion.dlt.adapter import DltIngestionAdapter
from pipelinekit.adapters.quality.soda.adapter import SodaQualityAdapter
from pipelinekit.adapters.transformation.dbt.adapter import DbtTransformationAdapter
from pipelinekit.config.schema import PipelineConfig


def _config(
    source_type: str = "postgres",
    transformation_enabled: bool = False,
    quality_enabled: bool = False,
) -> PipelineConfig:
    return PipelineConfig(
        **{
            "pipeline": {"name": "demo"},
            "runtime": {},
            "ingestion": {
                "source": {"type": source_type},
                "destination": {"type": "duckdb"},
            },
            "transformation": {"enabled": transformation_enabled},
            "contracts": {},
            "quality": {"enabled": quality_enabled},
            "diagnostics": {},
            "notifications": {},
        }
    )


def test_factory_creates_dlt_ingestion_for_postgres():
    """Factory returns a DltIngestionAdapter for a postgres source."""
    adapter = AdapterFactory.create_ingestion(_config(source_type="postgres"))
    assert isinstance(adapter, DltIngestionAdapter)


def test_factory_returns_none_for_unsupported_source():
    """Factory returns None for an unsupported ingestion source type."""
    assert AdapterFactory.create_ingestion(_config(source_type="oracle")) is None


def test_factory_returns_none_for_disabled_transformation():
    """Factory returns None for transformation when disabled."""
    assert (
        AdapterFactory.create_transformation(_config(transformation_enabled=False))
        is None
    )


def test_factory_returns_none_for_disabled_quality():
    """Factory returns None for quality when disabled."""
    assert AdapterFactory.create_quality(_config(quality_enabled=False)) is None


def test_factory_creates_enabled_transformation_and_quality():
    """Factory returns the right adapters when the steps are enabled."""
    config = _config(transformation_enabled=True, quality_enabled=True)
    assert isinstance(
        AdapterFactory.create_transformation(config), DbtTransformationAdapter
    )
    assert isinstance(AdapterFactory.create_quality(config), SodaQualityAdapter)
