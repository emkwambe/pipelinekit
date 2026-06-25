"""Pydantic v2 models for ``pipelinekit.yaml``.

The schema is the authoritative validator for PipelineKit configuration. All
eight sections are required; missing any of them is a validation failure
(surfaced as ``PK-CONFIG-001`` by the loader).

See: SPEC-002, contracts/pipeline.yaml, docs/reference/Configuration-Schema.md.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


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
    model serves heterogeneous backends (postgres, snowflake, bigquery, duckdb).
    Credential fields are first-class (ADR-017): ``pipelinekit.yaml`` is the
    single source of credential truth, populated via ``${VAR}`` interpolation in
    the loader. The model never stores secrets at rest — values arrive from the
    environment at load time (BYOK, ADR-005).
    """

    model_config = ConfigDict(populate_by_name=True)

    type: str
    # Postgres / MySQL
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    tables: Optional[list[str]] = None
    # Snowflake
    account: Optional[str] = None
    warehouse: Optional[str] = None
    schema_name: Optional[str] = Field(None, alias="schema")
    # BigQuery
    project: Optional[str] = None
    location: Optional[str] = None
    # DuckDB
    path: Optional[str] = None


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
    """Notification settings.

    Phase 1 shipped ``enabled`` and ``channels``. Phase 3 adds the fields the
    notification dispatcher needs (provider, sender, recipients, and which
    events to notify on). The Resend API key is never stored here — it is read
    from the ``RESEND_API_KEY`` environment variable (ADR-005, BYOK).
    """

    enabled: bool = False
    channels: list[str] = []
    provider: str = "resend"
    from_address: str = ""
    recipients: list[str] = []
    notify_on: list[str] = ["pipeline_failed", "contract_violated"]


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
