"""Tests for AI-7 EMS context injection (SPEC-032).

Deterministic, no AI, read-only. Every test uses a ``tmp_path`` SQLite database
and ``monkeypatch.chdir`` so ``blueprints/`` resolution is isolated — the real
``blueprints/`` directory and project ``state.db`` are never touched.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pipelinekit.ai.ems_context import (
    EMSContext,
    assemble_ems_context,
    format_ems_context_for_prompt,
)
from pipelinekit.observability.slo import set_slo
from pipelinekit.quality.anomaly import record_row_counts


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    """Chdir into an isolated temp project root; return (tmp_path, db_path)."""
    monkeypatch.chdir(tmp_path)
    return tmp_path, str(tmp_path / "state.db")


def _seed_slo_violation(db_path: str) -> None:
    """Register a row_count SLO of 1000 and record a low count (500) → VIOLATED."""
    set_slo("test-bp", "charges", "row_count", 1000.0, "rows", db_path)
    record_row_counts("test-bp", {"charges": 500}, db_path)


def test_ai7_assemble_ems_context_returns_empty_when_no_data(
    env: tuple[Path, str],
) -> None:
    """assemble_ems_context has_data=False when state.db has no EMS signals."""
    _, db_path = env

    ctx = assemble_ems_context("test-bp", db_path)

    assert isinstance(ctx, EMSContext)
    assert ctx.has_data is False
    assert ctx.quality_score is None
    assert ctx.summary == "No EMS data available for this blueprint"


def test_ai7_assemble_ems_context_captures_slo_violations(
    env: tuple[Path, str],
) -> None:
    """SLO violations are captured in EMSContext when OM-4 data shows one."""
    _, db_path = env
    _seed_slo_violation(db_path)

    ctx = assemble_ems_context("test-bp", db_path)

    assert ctx.has_data is True
    assert len(ctx.slo_violations) == 1
    assert ctx.slo_violations[0]["table"] == "charges"
    assert ctx.slo_violations[0]["type"] == "row_count"
    assert ctx.slo_violations[0]["status"] == "VIOLATED"


def test_ai7_assemble_ems_context_captures_volume_anomalies(
    env: tuple[Path, str],
) -> None:
    """Volume anomalies are captured when the latest count deviates sharply."""
    _, db_path = env
    for _ in range(5):
        record_row_counts("test-bp", {"charges": 45000}, db_path)
    record_row_counts("test-bp", {"charges": 500}, db_path)  # 98%+ drop

    ctx = assemble_ems_context("test-bp", db_path)

    assert ctx.has_data is True
    assert len(ctx.volume_anomalies) == 1
    assert ctx.volume_anomalies[0]["table"] == "charges"
    assert ctx.volume_anomalies[0]["current"] == 500


def test_ai7_assemble_ems_context_never_raises(env: tuple[Path, str]) -> None:
    """assemble_ems_context returns a valid EMSContext even on a broken db_path."""
    tmp_path, _ = env
    broken_db = str(tmp_path / "no_such_dir" / "state.db")

    ctx = assemble_ems_context("test-bp", broken_db)

    assert isinstance(ctx, EMSContext)
    assert ctx.has_data is False


def test_ai7_format_ems_context_returns_empty_when_no_data() -> None:
    """format_ems_context_for_prompt returns '' when has_data is False."""
    ctx = EMSContext(
        blueprint_name="test-bp",
        quality_score=None,
        quality_rating=None,
        has_data=False,
        summary="No EMS data available for this blueprint",
    )

    assert format_ems_context_for_prompt(ctx) == ""


def test_ai7_format_ems_context_includes_slo_violations() -> None:
    """Formatted context includes the SLO violation section and details."""
    ctx = EMSContext(
        blueprint_name="test-bp",
        quality_score=42.0,
        quality_rating="Poor",
        slo_violations=[
            {
                "table": "charges",
                "type": "freshness",
                "threshold": 6.0,
                "current": 8.0,
                "status": "VIOLATED",
            }
        ],
        has_data=True,
        summary="EMS signals: 1 SLO violation(s)",
    )

    out = format_ems_context_for_prompt(ctx)

    assert "SLO Violations (OM-4)" in out
    assert "charges" in out
    assert "freshness" in out
    assert "VIOLATED" in out


def test_ai7_format_ems_context_includes_volume_anomalies() -> None:
    """Formatted context includes the volume anomaly section and numbers."""
    ctx = EMSContext(
        blueprint_name="test-bp",
        quality_score=None,
        quality_rating=None,
        volume_anomalies=[
            {
                "table": "charges",
                "current": 500,
                "baseline": 45000.0,
                "deviation_pct": -98.9,
            }
        ],
        has_data=True,
        summary="EMS signals: 1 volume anomaly(ies)",
    )

    out = format_ems_context_for_prompt(ctx)

    assert "Volume Anomalies (QM-6)" in out
    assert "charges" in out
    assert "500" in out
    assert "45,000" in out


def test_ai7_ems_summary_describes_issues(env: tuple[Path, str]) -> None:
    """The summary field describes active EMS issues in one line."""
    _, db_path = env
    _seed_slo_violation(db_path)

    ctx = assemble_ems_context("test-bp", db_path)

    assert ctx.summary.startswith("EMS signals:")
    assert "SLO violation" in ctx.summary
