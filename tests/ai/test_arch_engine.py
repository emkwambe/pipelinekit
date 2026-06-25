"""Tests for ArchitectureEngine (SPEC-011). Provider mocked — no real API calls."""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock

import pytest
from pipelinekit.ai.arch_engine import ArchitectureEngine
from pipelinekit.ai.arch_models import (
    ADRComplianceCheck,
    ArchitectureRecommendation,
    ArchitectureResult,
    ArchitectureTradeoff,
)
from pipelinekit.config.loader import write_default_config
from pipelinekit.config.schema import PipelineConfig
from pipelinekit.core.errors import LLMError
from pipelinekit.state import db
from typer.testing import CliRunner

from pipelinekit.cli.architect import architect_app  # isort: skip


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


def _seed(tmp_path, count: int = 6) -> None:
    for i in range(count):
        run_id = f"run-eng{i:04d}"
        db.insert_run(run_id, "demo", cwd=tmp_path)
        db.update_run(run_id, "failed" if i % 2 else "success", 1.0 + i, cwd=tmp_path)


def _result(can_auto_apply: bool = False) -> ArchitectureResult:
    return ArchitectureResult(
        reasoning_type="tool_selection",
        confidence=0.85,
        current_state={"description": "dbt"},
        recommendation=ArchitectureRecommendation(
            action="switch dbt to sqlmesh", rationale="reliability"
        ),
        tradeoffs=[
            ArchitectureTradeoff(
                dimension="cost",
                current="dbt",
                proposed="sqlmesh",
                direction="neutral",
                evidence="both Apache 2.0",
            )
        ],
        evidence=[{"type": "run", "detail": "PK-ADAPTER-002"}],
        adr_compliance=[ADRComplianceCheck(adr_id="ADR-005", compliant=True)],
        can_auto_apply=can_auto_apply,
    )


def _provider(result) -> MagicMock:
    provider = MagicMock()
    provider.name = "anthropic"
    provider.architect.return_value = result
    return provider


def test_analyze_returns_result(tmp_path):
    """analyze() returns an ArchitectureResult from a mocked provider."""
    _seed(tmp_path)
    engine = ArchitectureEngine(_config(), _provider(_result()))
    result = engine.analyze("tool_selection", cwd=tmp_path)
    assert isinstance(result, ArchitectureResult)
    assert result.reasoning_type == "tool_selection"


def test_can_auto_apply_forced_false(tmp_path):
    """A provider returning can_auto_apply=True is corrected to False."""
    _seed(tmp_path)
    engine = ArchitectureEngine(_config(), _provider(_result(can_auto_apply=True)))
    result = engine.analyze("tool_selection", cwd=tmp_path)
    assert result.can_auto_apply is False


def test_invalid_schema_raises_ai_002(tmp_path):
    """analyze() raises LLMError(PK-AI-002) when output fails schema validation."""
    _seed(tmp_path)
    bad_result = MagicMock()
    bad_result.model_dump.return_value = {"reasoning_type": "tool_selection"}  # partial
    engine = ArchitectureEngine(_config(), _provider(bad_result))
    with pytest.raises(LLMError) as exc_info:
        engine.analyze("tool_selection", cwd=tmp_path)
    assert exc_info.value.code == "PK-AI-002"


def test_result_stored_in_state(tmp_path):
    """analyze() persists the result to the architecture_results table."""
    _seed(tmp_path)
    engine = ArchitectureEngine(_config(), _provider(_result()))
    engine.analyze("tool_selection", question="dbt or sqlmesh?", cwd=tmp_path)
    with sqlite3.connect(db.get_db_path(tmp_path)) as conn:
        rows = conn.execute(
            "SELECT reasoning_type, provider, can_auto_apply FROM architecture_results"
        ).fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "tool_selection"
    assert rows[0][1] == "anthropic"
    assert rows[0][2] == 0  # can_auto_apply persisted as False


def test_diagnostics_disabled_exits_gracefully(tmp_path, monkeypatch):
    """architect analyze exits 0 with guidance when diagnostics are disabled."""
    write_default_config(tmp_path)  # diagnostics.enabled defaults to false
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(architect_app, ["analyze", "anything"])
    assert result.exit_code == 0
    assert "disabled" in result.stdout.lower()
