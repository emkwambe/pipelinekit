"""Tests for PipelineRunner (SPEC-003)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pipelinekit.adapters.factory import AdapterFactory
from pipelinekit.config.schema import PipelineConfig
from pipelinekit.runtime.result import PipelineStatus, StepResult
from pipelinekit.runtime.runner import PipelineRunner
from pipelinekit.state import db


def _config(name: str = "demo") -> PipelineConfig:
    return PipelineConfig(
        **{
            "pipeline": {"name": name},
            "runtime": {},
            "ingestion": {
                "source": {"type": "postgres"},
                "destination": {"type": "duckdb"},
            },
            "transformation": {},
            "contracts": {},
            "quality": {},
            "diagnostics": {},
            "notifications": {},
        }
    )


def _adapter_returning(step_result: StepResult) -> MagicMock:
    adapter = MagicMock()
    adapter.execute.return_value = step_result
    adapter.validate.return_value = step_result
    return adapter


def test_run_success(tmp_path, monkeypatch):
    """run() returns SUCCESS when every step passes, and records the run."""
    monkeypatch.chdir(tmp_path)
    ingestion = _adapter_returning(
        StepResult("ingestion", PipelineStatus.SUCCESS, 0.1, rows_processed=10)
    )
    with (
        patch.object(AdapterFactory, "create_ingestion", return_value=ingestion),
        patch.object(AdapterFactory, "create_transformation", return_value=None),
        patch.object(AdapterFactory, "create_quality", return_value=None),
    ):
        result = PipelineRunner(_config()).run()

    assert result.status == PipelineStatus.SUCCESS
    assert result.succeeded()
    assert len(result.steps) == 1
    runs = db.get_recent_runs(cwd=tmp_path)
    assert runs[0]["status"] == "success"


def test_run_failed(tmp_path, monkeypatch):
    """run() returns FAILED and propagates the step error when a step fails."""
    monkeypatch.chdir(tmp_path)
    ingestion = _adapter_returning(
        StepResult(
            "ingestion",
            PipelineStatus.FAILED,
            0.1,
            error_code="PK-ADAPTER-002",
            error_msg="connection lost",
        )
    )
    with (
        patch.object(AdapterFactory, "create_ingestion", return_value=ingestion),
        patch.object(AdapterFactory, "create_transformation", return_value=None),
        patch.object(AdapterFactory, "create_quality", return_value=None),
    ):
        result = PipelineRunner(_config()).run()

    assert result.status == PipelineStatus.FAILED
    assert result.error_code == "PK-ADAPTER-002"


def test_run_always_updates_state_on_exception(tmp_path, monkeypatch):
    """run() updates the run record even when adapter creation raises."""
    monkeypatch.chdir(tmp_path)
    with (
        patch.object(
            AdapterFactory, "create_ingestion", side_effect=RuntimeError("boom")
        ),
        patch.object(AdapterFactory, "create_transformation", return_value=None),
        patch.object(AdapterFactory, "create_quality", return_value=None),
    ):
        result = PipelineRunner(_config()).run()

    assert result.status == PipelineStatus.FAILED
    runs = db.get_recent_runs(cwd=tmp_path)
    assert runs[0]["status"] != "pending"
    assert runs[0]["status"] == "failed"


def test_validate_valid(tmp_path, monkeypatch):
    """validate() returns VALID when adapters report valid connectivity."""
    monkeypatch.chdir(tmp_path)
    ingestion = _adapter_returning(StepResult("ingestion", PipelineStatus.VALID, 0.1))
    with (
        patch.object(AdapterFactory, "create_ingestion", return_value=ingestion),
        patch.object(AdapterFactory, "create_transformation", return_value=None),
        patch.object(AdapterFactory, "create_quality", return_value=None),
    ):
        result = PipelineRunner(_config()).validate()

    assert result.status == PipelineStatus.VALID


def test_validate_invalid(tmp_path, monkeypatch):
    """validate() returns INVALID when an adapter reports a connectivity failure."""
    monkeypatch.chdir(tmp_path)
    ingestion = _adapter_returning(
        StepResult(
            "ingestion",
            PipelineStatus.INVALID,
            0.1,
            error_code="PK-ADAPTER-001",
            error_msg="unreachable",
        )
    )
    with (
        patch.object(AdapterFactory, "create_ingestion", return_value=ingestion),
        patch.object(AdapterFactory, "create_transformation", return_value=None),
        patch.object(AdapterFactory, "create_quality", return_value=None),
    ):
        result = PipelineRunner(_config()).validate()

    assert result.status == PipelineStatus.INVALID
    assert result.error_code == "PK-ADAPTER-001"


def test_run_step_exception_mapped_to_runtime_error(tmp_path, monkeypatch):
    """A raising adapter.execute() is caught and mapped to PK-RUNTIME-001."""
    monkeypatch.chdir(tmp_path)
    ingestion = MagicMock()
    ingestion.execute.side_effect = Exception("kaboom")
    with (
        patch.object(AdapterFactory, "create_ingestion", return_value=ingestion),
        patch.object(AdapterFactory, "create_transformation", return_value=None),
        patch.object(AdapterFactory, "create_quality", return_value=None),
    ):
        result = PipelineRunner(_config()).run()

    assert result.status == PipelineStatus.FAILED
    assert result.steps[0].error_code == "PK-RUNTIME-001"


def test_validate_step_exception_mapped_to_adapter_error(tmp_path, monkeypatch):
    """A raising adapter.validate() is caught and mapped to PK-ADAPTER-001."""
    monkeypatch.chdir(tmp_path)
    ingestion = MagicMock()
    ingestion.validate.side_effect = Exception("nope")
    with (
        patch.object(AdapterFactory, "create_ingestion", return_value=ingestion),
        patch.object(AdapterFactory, "create_transformation", return_value=None),
        patch.object(AdapterFactory, "create_quality", return_value=None),
    ):
        result = PipelineRunner(_config()).validate()

    assert result.status == PipelineStatus.INVALID
    assert result.steps[0].error_code == "PK-ADAPTER-001"
