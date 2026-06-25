"""Pydantic models for blueprint metadata (``blueprint.json``).

See: SPEC-006, schemas/blueprint.schema.json.
"""

from __future__ import annotations

from pydantic import BaseModel


class BlueprintSource(BaseModel):
    """The ingestion source a blueprint reads from."""

    type: str
    dlt_source: str


class BlueprintDestination(BaseModel):
    """The destination a blueprint loads into."""

    type: str
    dlt_destination: str


class BlueprintMetadata(BaseModel):
    """Canonical metadata describing one installed blueprint."""

    name: str
    version: str
    description: str = ""
    source: BlueprintSource
    destination: BlueprintDestination
    contracts: list[str] = []
    tags: list[str] = []
    kpis: list[str] = []
    deploy_time_minutes: int = 60
    time_to_trusted_data_hours: int = 24
