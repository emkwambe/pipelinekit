"""Integration-shaped tests for DltIngestionAdapter credential wiring (ADR-017).

dlt is mocked throughout — no real database connection and no live dlt source.
These cover the Sprint 6-2a additions: Postgres conn-string building, validate()
connectivity mapping, and execute() exception mapping.
"""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

from pipelinekit.adapters.ingestion.dlt.adapter import DltIngestionAdapter
from pipelinekit.config.schema import IngestionSection, SourceConfig


def _adapter(source: SourceConfig, dest: SourceConfig) -> DltIngestionAdapter:
    return DltIngestionAdapter(IngestionSection(source=source, destination=dest))


def test_build_postgres_conn_str():
    """The Postgres connection string is assembled from SourceConfig fields."""
    source = SourceConfig(
        type="postgres",
        host="db.example.com",
        port=5433,
        database="analytics",
        user="admin",
        password="secret",
    )
    adapter = _adapter(source, SourceConfig(type="duckdb"))
    conn = adapter._build_postgres_conn_str(source)
    assert conn == "postgresql://admin:secret@db.example.com:5433/analytics"


def test_build_postgres_conn_str_defaults_port():
    """Port defaults to 5432 when unset."""
    source = SourceConfig(
        type="postgres",
        host="localhost",
        database="d",
        user="u",
        password="p",
    )
    adapter = _adapter(source, SourceConfig(type="duckdb"))
    assert adapter._build_postgres_conn_str(source).endswith("@localhost:5432/d")


def test_build_snowflake_credentials():
    """Snowflake credentials are assembled from SourceConfig; schema defaults raw."""
    dest = SourceConfig(
        type="snowflake",
        account="acct",
        user="u",
        password="p",
        database="db",
        warehouse="wh",
    )
    adapter = _adapter(SourceConfig(type="postgres"), dest)
    creds = adapter._build_snowflake_credentials(dest)
    assert creds == {
        "account": "acct",
        "user": "u",
        "password": "p",
        "database": "db",
        "warehouse": "wh",
        "schema": "raw",
    }


def test_validate_returns_invalid_on_unreachable_host():
    """validate() maps a TCP connectivity failure to PK-ADAPTER-001."""
    adapter = _adapter(
        SourceConfig(type="postgres", host="10.255.255.1", port=1),
        SourceConfig(type="duckdb"),
    )
    with patch.object(adapter, "_check_connectivity", side_effect=OSError("refused")):
        result = adapter.validate()
    assert result.status.value == "invalid"
    assert result.error_code == "PK-ADAPTER-001"


def test_execute_maps_dlt_exception_to_pk_code():
    """execute() maps a dlt ConfigFieldMissingException-style failure to ADAPTER-002."""
    adapter = _adapter(
        SourceConfig(type="postgres", host="localhost", port=5432),
        SourceConfig(type="duckdb"),
    )
    with patch("dlt.pipeline", side_effect=Exception("Missing field credentials")):
        result = adapter.execute()
    assert result.status.value == "failed"
    assert result.error_code == "PK-ADAPTER-002"
    assert "dlt ingestion failed" in result.error_msg


def test_execute_builds_real_source_when_tables_present():
    """execute() builds a sql_database source from config when tables are declared.

    The dlt ``sql_database`` source needs the SQLAlchemy extra at runtime, so the
    submodule is injected via ``sys.modules`` rather than imported for real.
    """
    adapter = _adapter(
        SourceConfig(
            type="postgres",
            host="localhost",
            port=5432,
            database="analytics",
            user="u",
            password="p",
            tables=["orders"],
        ),
        SourceConfig(type="duckdb"),
    )
    fake_module = ModuleType("dlt.sources.sql_database")
    mock_sql_database = MagicMock()
    fake_module.sql_database = mock_sql_database  # type: ignore[attr-defined]

    with (
        patch("dlt.pipeline") as mock_pipeline,
        patch.dict(sys.modules, {"dlt.sources.sql_database": fake_module}),
    ):
        mock_pipeline.return_value.run.return_value = type(
            "LI", (), {"load_packages": []}
        )()
        adapter.initialize()
        result = adapter.execute()

    mock_sql_database.assert_called_once()
    conn_arg = mock_sql_database.call_args.args[0]
    assert conn_arg == "postgresql://u:p@localhost:5432/analytics"
    mock_sql_database.return_value.with_resources.assert_called_once_with("orders")
    assert result.status.value == "success"
