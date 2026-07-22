"""The single point of adapter instantiation.

The runtime calls this factory and never constructs adapters directly. This
keeps provider-selection logic in one place and keeps adapters replaceable
(SPEC-009).
"""

from __future__ import annotations

from pipelinekit.adapters.base import BaseAdapter
from pipelinekit.adapters.ingestion.dlt.adapter import DltIngestionAdapter
from pipelinekit.adapters.quality.soda.adapter import SodaQualityAdapter
from pipelinekit.adapters.transformation.dbt.adapter import DbtTransformationAdapter
from pipelinekit.config.schema import PipelineConfig

# dlt source types supported through the standard runtime path in Phase 2.
# This is intentionally a conservative release gate (SPEC-009): the dlt adapter
# can handle additional sources, but each one is enabled here only after it has
# been end-to-end verified. Salesforce and Stripe blueprints exist and can be
# proposed by AI, but the standard `pipelinekit run` path currently supports
# Postgres only.
_SUPPORTED_SOURCES = {"postgres"}


class AdapterFactory:
    """Creates adapter instances from a :class:`PipelineConfig`."""

    @staticmethod
    def create_ingestion(config: PipelineConfig) -> BaseAdapter | None:
        """Return a dlt ingestion adapter, or None if the source is unsupported."""
        if config.ingestion.source.type not in _SUPPORTED_SOURCES:
            return None
        return DltIngestionAdapter(config.ingestion)

    @staticmethod
    def create_transformation(config: PipelineConfig) -> BaseAdapter | None:
        """Return a dbt adapter, or None if transformation is disabled."""
        if not config.transformation.enabled:
            return None
        return DbtTransformationAdapter(config.transformation)

    @staticmethod
    def create_quality(config: PipelineConfig) -> BaseAdapter | None:
        """Return a Soda adapter, or None if quality is disabled."""
        if not config.quality.enabled:
            return None
        return SodaQualityAdapter(config.quality)
