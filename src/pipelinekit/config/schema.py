"""Pydantic v2 models for ``pipelinekit.yaml``.

The schema is the authoritative validator for PipelineKit configuration. All
eight sections are required; missing any of them is a validation failure
(surfaced as ``PK-CONFIG-001`` by the loader).

See: SPEC-002, contracts/pipeline.yaml, docs/reference/Configuration-Schema.md.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class PipelineSection(BaseModel):
    """Pipeline identity. ``name`` is contract-required."""

    name: str
    version: str = "0.1.0"
    description: str = ""


class RuntimeSection(BaseModel):
    """Execution environment. Contract-required section."""

    environment: str = "local"


class SourceConfig(BaseModel):
    """Connection descriptor for an ingestion source or destination.

    Only ``type`` is required; the remaining fields are optional so the same
    model serves heterogeneous backends (e.g. postgres vs snowflake).
    """

    type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    account: Optional[str] = None


class IngestionSection(BaseModel):
    """Source and destination connection descriptors. Contract-required."""

    source: SourceConfig
    destination: SourceConfig


class TransformationSection(BaseModel):
    """Transformation settings. Contract-required section."""

    enabled: bool = False
    project_dir: str = "./transform"


class ContractsSection(BaseModel):
    """Data-contract settings. Contract-required section."""

    enabled: bool = True
    directory: str = "./contracts"


class QualitySection(BaseModel):
    """Data-quality settings."""

    enabled: bool = False
    checks_dir: str = "./quality"


class DiagnosticsSection(BaseModel):
    """AI diagnostics settings. Contract-required section."""

    enabled: bool = False
    provider: str = "none"


class NotificationsSection(BaseModel):
    """Notification settings."""

    enabled: bool = False
    channels: list[str] = []


class PipelineConfig(BaseModel):
    """The complete PipelineKit configuration — all eight sections required."""

    pipeline: PipelineSection
    runtime: RuntimeSection
    ingestion: IngestionSection
    transformation: TransformationSection
    contracts: ContractsSection
    quality: QualitySection
    diagnostics: DiagnosticsSection
    notifications: NotificationsSection
