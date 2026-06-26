"""Tests for the deterministic config parsers (SPEC-017, ADR-020).

No AI calls. The Python parser must never execute the file it reads.
"""

from __future__ import annotations

import json

import pytest
from pipelinekit.ai.config_parsers import (
    AirbyteParser,
    FivetranParser,
    MigrationConfigParser,
    PythonParser,
)
from pipelinekit.core.errors import MigrationError

_AIRBYTE = {
    "connectionId": "abc-123",
    "name": "Postgres to Snowflake",
    "source": {
        "sourceName": "Postgres",
        "sourceType": "postgres",
        "connectionConfiguration": {"host": "db.example.com", "database": "analytics"},
    },
    "destination": {
        "destinationName": "Snowflake",
        "destinationType": "snowflake",
        "connectionConfiguration": {"database": "RAW"},
    },
    "syncCatalog": {
        "streams": [
            {
                "stream": {"name": "customers", "namespace": "public"},
                "config": {"syncMode": "incremental"},
            },
            {
                "stream": {"name": "orders", "namespace": "public"},
                "config": {"syncMode": "full_refresh"},
            },
        ]
    },
}

_FIVETRAN = {
    "id": "connector_xyz",
    "service": "Postgres",
    "schema": "public",
    "config": {"host": "db.example.com", "database": "analytics"},
    "sync_frequency": 360,
    "destination": {"service": "Snowflake"},
    "schemas": {
        "public": {
            "tables": {
                "customers": {"enabled": True},
                "orders": {"enabled": True},
                "audit_log": {"enabled": False},
            }
        }
    },
}

_PYTHON = """\
import dlt
from sqlalchemy import create_engine

engine = create_engine("postgresql://etl_user@db.example.com:5432/analytics")

pipeline = dlt.pipeline(
    pipeline_name="custom_load",
    destination="snowflake",
    dataset_name="raw",
)

TABLES = ["customers", "orders", "payments"]
"""


def test_airbyte_parser_extracts_source_destination_streams(tmp_path):
    """AirbyteParser.parse() extracts source/destination/streams from JSON."""
    path = tmp_path / "connection.json"
    path.write_text(json.dumps(_AIRBYTE), encoding="utf-8")
    result = AirbyteParser().parse(path)
    assert result["source_type"] == "postgres"
    assert result["destination_type"] == "snowflake"
    assert [s["name"] for s in result["streams"]] == ["customers", "orders"]
    assert result["sync_mode"] == "incremental"
    assert result["namespace"] == "public"


def test_airbyte_parser_flat_shape_reads_top_level_types(tmp_path):
    """A flat export (syncCatalog + top-level destinationType, no nested objects)
    is detected and its top-level types are read (regression: empty types)."""
    flat = {
        "sourceId": "abc-123",
        "destinationId": "def-456",
        "syncCatalog": {
            "streams": [
                {"stream": {"name": "customers"}, "config": {"syncMode": "append"}}
            ]
        },
        "destinationType": "snowflake",
    }
    path = tmp_path / "connection.json"
    path.write_text(json.dumps(flat), encoding="utf-8")
    assert AirbyteParser.can_parse(flat) is True
    result = AirbyteParser().parse(path)
    assert result["destination_type"] == "snowflake"
    assert [s["name"] for s in result["streams"]] == ["customers"]


def test_airbyte_parser_public_api_configurations_shape(tmp_path):
    """The public-API export (configurations, sourceId/destinationId, no
    syncCatalog/source/destination) is detected and its streams are read
    (regression: previously fell through to PK-MIGRATE-002)."""
    public = {
        "connectionId": "abc-123",
        "name": "pg to sf",
        "sourceId": "abc-123",
        "destinationId": "def-456",
        "configurations": {
            "streams": [
                {"name": "customers", "namespace": "public", "syncMode": "incremental"}
            ]
        },
        "schedule": {"scheduleType": "manual"},
    }
    path = tmp_path / "connection.json"
    path.write_text(json.dumps(public), encoding="utf-8")
    assert AirbyteParser.can_parse(public) is True
    assert MigrationConfigParser().parse(path)[0] == "airbyte"
    result = AirbyteParser().parse(path)
    assert result["streams"][0]["name"] == "customers"
    assert result["streams"][0]["sync_mode"] == "incremental"


def test_fivetran_parser_extracts_connector_schema_tables(tmp_path):
    """FivetranParser.parse() extracts connector/schema/tables (enabled only)."""
    path = tmp_path / "connector.json"
    path.write_text(json.dumps(_FIVETRAN), encoding="utf-8")
    result = FivetranParser().parse(path)
    assert result["connector_type"] == "postgres"
    assert result["destination_type"] == "snowflake"
    assert result["schema"] == "public"
    assert result["tables"] == ["customers", "orders"]  # audit_log disabled
    assert result["sync_frequency"] == 360


def test_python_parser_extracts_connection_hints_without_executing(tmp_path):
    """PythonParser.parse() extracts hints via AST, never executing the file."""
    path = tmp_path / "pipeline.py"
    path.write_text(_PYTHON, encoding="utf-8")
    result = PythonParser().parse(path)
    assert result["source_type"] == "postgres"
    assert result["destination_type"] == "snowflake"
    assert result["tables"] == ["customers", "orders", "payments"]
    assert result["confidence"] == "low"
    assert any("postgresql://" in c for c in result["connection_strings"])


def test_python_parser_raises_pk_migrate_005_on_syntax_error(tmp_path):
    """A Python file with a syntax error fails with PK-MIGRATE-005."""
    path = tmp_path / "broken.py"
    path.write_text("def oops(:\n    pass\n", encoding="utf-8")
    with pytest.raises(MigrationError) as exc_info:
        PythonParser().parse(path)
    assert exc_info.value.code == "PK-MIGRATE-005"


def test_router_detects_format_by_file_type(tmp_path):
    """MigrationConfigParser.parse() routes correctly by file type and content."""
    router = MigrationConfigParser()

    airbyte = tmp_path / "connection.json"
    airbyte.write_text(json.dumps(_AIRBYTE), encoding="utf-8")
    assert router.parse(airbyte)[0] == "airbyte"

    fivetran = tmp_path / "connector.json"
    fivetran.write_text(json.dumps(_FIVETRAN), encoding="utf-8")
    assert router.parse(fivetran)[0] == "fivetran"

    py = tmp_path / "pipeline.py"
    py.write_text(_PYTHON, encoding="utf-8")
    assert router.parse(py)[0] == "python"

    yaml_path = tmp_path / "pipelinekit.yaml"
    yaml_path.write_text("pipeline:\n  name: x\ningestion:\n  source: {}\n", "utf-8")
    assert router.parse(yaml_path)[0] == "pipelinekit"


def test_router_missing_file_raises_pk_migrate_001(tmp_path):
    """A missing config file raises PK-MIGRATE-001."""
    with pytest.raises(MigrationError) as exc_info:
        MigrationConfigParser().parse(tmp_path / "nope.json")
    assert exc_info.value.code == "PK-MIGRATE-001"


def test_router_unrecognized_format_raises_pk_migrate_002(tmp_path):
    """An unrecognised JSON shape raises PK-MIGRATE-002."""
    path = tmp_path / "mystery.json"
    path.write_text(json.dumps({"totally": "unknown"}), encoding="utf-8")
    with pytest.raises(MigrationError) as exc_info:
        MigrationConfigParser().parse(path)
    assert exc_info.value.code == "PK-MIGRATE-002"
