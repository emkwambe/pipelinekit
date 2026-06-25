"""Tests for DiagnosticsEngine (SPEC-005). Provider mocked — no real API calls."""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock

import pytest
from pipelinekit.ai.diagnostics import DiagnosticsEngine
from pipelinekit.ai.models import DiagnosticResult, RecommendedAction
from pipelinekit.config.schema import PipelineConfig
from pipelinekit.core.errors import LLMError
from pipelinekit.state import db


def _config() -> PipelineConfig:
    return PipelineConfig(
        **{
            "pipeline": {"name": "demo"},
            "runtime": {},
            "ingestion": {
                "source": {"type": "postgres"},
                "destination": {"type": "duckdb"},
            },
            "transformation": {},
            "contracts": {},
            "quality": {},
            "diagnostics": {"enabled": True, "provider": "anthropic"},
            "notifications": {},
        }
    )


def _seed(tmp_path, run_id: str = "run-diag0001") -> None:
    db.insert_run(run_id, "demo", cwd=tmp_path)
    db.update_run(
        run_id,
        "failed",
        1.0,
        error_code="PK-ADAPTER-001",
        error_msg="x",
        cwd=tmp_path,
    )


def _result(confidence: float = 0.9, can_auto_fix: bool = False) -> DiagnosticResult:
    return DiagnosticResult(
        status="diagnosed",
        finding_type="adapter_failure",
        confidence=confidence,
        evidence=[{"type": "error_code", "detail": "PK-ADAPTER-001"}],
        recommended_actions=[RecommendedAction(action="check connectivity")],
        can_auto_fix=can_auto_fix,
    )


def _provider(result) -> MagicMock:
    provider = MagicMock()
    provider.name = "anthropic"
    provider.diagnose.return_value = result
    return provider


def test_diagnose_returns_result(tmp_path):
    """diagnose() returns a DiagnosticResult from valid evidence."""
    _seed(tmp_path)
    engine = DiagnosticsEngine(_config(), _provider(_result()))
    result = engine.diagnose("run-diag0001", cwd=tmp_path)
    assert isinstance(result, DiagnosticResult)
    assert result.finding_type == "adapter_failure"
    assert result.run_id == "run-diag0001"


def test_diagnose_invalid_schema_raises_ai_002(tmp_path):
    """diagnose() raises LLMError(PK-AI-002) when output fails schema validation."""
    _seed(tmp_path)
    bad = MagicMock()
    bad.name = "anthropic"
    bad_result = MagicMock()
    bad_result.model_dump.return_value = {"status": "diagnosed"}  # missing fields
    bad.diagnose.return_value = bad_result
    engine = DiagnosticsEngine(_config(), bad)
    with pytest.raises(LLMError) as exc_info:
        engine.diagnose("run-diag0001", cwd=tmp_path)
    assert exc_info.value.code == "PK-AI-002"


def test_diagnose_stores_result(tmp_path):
    """diagnose() persists the result to the diagnostic_results table."""
    _seed(tmp_path)
    engine = DiagnosticsEngine(_config(), _provider(_result()))
    engine.diagnose("run-diag0001", cwd=tmp_path)
    with sqlite3.connect(db.get_db_path(tmp_path)) as conn:
        rows = conn.execute(
            "SELECT run_id, provider FROM diagnostic_results"
        ).fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "run-diag0001"
    assert rows[0][1] == "anthropic"


def test_low_confidence_marked_inconclusive(tmp_path):
    """A result below threshold is returned as status=inconclusive."""
    _seed(tmp_path)
    engine = DiagnosticsEngine(_config(), _provider(_result(confidence=0.3)))
    result = engine.diagnose("run-diag0001", cwd=tmp_path)
    assert result.status == "inconclusive"


def test_can_auto_fix_forced_false(tmp_path):
    """A provider returning can_auto_fix=True is corrected to False."""
    _seed(tmp_path)
    engine = DiagnosticsEngine(_config(), _provider(_result(can_auto_fix=True)))
    result = engine.diagnose("run-diag0001", cwd=tmp_path)
    assert result.can_auto_fix is False


def test_no_action_is_auto_executed(tmp_path):
    """The engine exposes no method that executes a recommended action."""
    engine = DiagnosticsEngine(_config(), _provider(_result()))
    method_names = [m for m in dir(engine) if not m.startswith("__")]
    forbidden = ("execute", "apply", "run_action", "fix", "remediate")
    assert not any(any(f in m.lower() for f in forbidden) for m in method_names)
