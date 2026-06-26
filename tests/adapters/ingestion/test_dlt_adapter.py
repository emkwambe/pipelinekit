"""Tests for DltIngestionAdapter (SPEC-009). dlt is mocked — no real database."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pipelinekit.adapters.ingestion.dlt.adapter import DltIngestionAdapter
from pipelinekit.config.schema import IngestionSection, SourceConfig


def _ingestion_config() -> IngestionSection:
    return IngestionSection(
        source=SourceConfig(type="postgres", host="localhost", port=5432),
        destination=SourceConfig(type="duckdb"),
    )


def test_execute_returns_success_step_result():
    """execute() returns a success StepResult when the dlt run succeeds."""
    with patch("dlt.pipeline") as mock_pipeline:
        mock_pipeline.return_value.run.return_value = MagicMock(load_packages=[])
        adapter = DltIngestionAdapter(_ingestion_config())
        adapter.initialize()
        result = adapter.execute()

    assert result.status.value == "success"
    assert result.step == "ingestion"


def test_execute_maps_exception_to_adapter_002():
    """execute() maps a dlt exception to PK-ADAPTER-002."""
    with patch("dlt.pipeline", side_effect=Exception("connection blew up")):
        adapter = DltIngestionAdapter(_ingestion_config())
        result = adapter.execute()

    assert result.status.value == "failed"
    assert result.error_code == "PK-ADAPTER-002"


def test_validate_valid_on_connectivity_success():
    """validate() returns valid when the source is reachable (mocked)."""
    adapter = DltIngestionAdapter(_ingestion_config())
    with patch.object(adapter, "_check_connectivity", return_value=None):
        result = adapter.validate()

    assert result.status.value == "valid"


def test_validate_invalid_on_connectivity_failure():
    """validate() returns invalid with PK-ADAPTER-001 when unreachable (mocked)."""
    adapter = DltIngestionAdapter(_ingestion_config())
    with patch.object(
        adapter, "_check_connectivity", side_effect=OSError("connection refused")
    ):
        result = adapter.validate()

    assert result.status.value == "invalid"
    assert result.error_code == "PK-ADAPTER-001"


def test_status_returns_structured_dict():
    """status() returns a structured dict describing the adapter."""
    adapter = DltIngestionAdapter(_ingestion_config())
    status = adapter.status()
    assert status["adapter"] == "dlt"
    assert status["step"] == "ingestion"
    assert status["source"] == "postgres"


def test_execute_reports_real_row_counts():
    """execute() reports real data-table row counts from the dlt trace.

    dlt load_info reports completed jobs, not rows; the adapter reads the actual
    per-table counts from last_trace.last_normalize_info.row_counts and excludes
    dlt bookkeeping tables (_dlt_*).
    """
    with patch("dlt.pipeline") as mock_pipeline:
        pipe = mock_pipeline.return_value
        pipe.run.return_value = MagicMock(load_packages=[])
        pipe.last_trace.last_normalize_info.row_counts = {
            "orders": 3,
            "_dlt_pipeline_state": 1,
        }
        adapter = DltIngestionAdapter(_ingestion_config())
        result = adapter.execute()

    assert result.status.value == "success"
    assert result.rows_processed == 3
