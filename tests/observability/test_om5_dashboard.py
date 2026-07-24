"""Tests for OM-5 SLO compliance dashboard (SPEC-035).

Deterministic, no AI. Every test uses a ``tmp_path`` SQLite database — the real
``blueprints/`` directory and project ``state.db`` are never touched.
"""

from __future__ import annotations

from pathlib import Path

from pipelinekit.observability.slo import (
    check_slos,
    get_slo_compliance_summary,
    set_slo,
)
from pipelinekit.quality.anomaly import record_row_counts
from pipelinekit.state import db


def _db(tmp_path: Path) -> str:
    """Return a path to an isolated state database for this test."""
    return str(tmp_path / "state.db")


def _seed_run(
    db_path: str,
    status: str,
    blueprint: str = "test-bp",
    table: str = "charges",
    slo_type: str = "row_count",
) -> None:
    """Insert one SLO run with a given status into ``om_slo_runs``."""
    current = None if status == "NO_DATA" else 500.0
    db.insert_slo_run(blueprint, table, slo_type, status, current, 1000.0, db_path)


def test_om5_check_slos_saves_run_to_db(tmp_path: Path) -> None:
    """check_slos persists each evaluated result to om_slo_runs."""
    db_path = _db(tmp_path)
    set_slo("test-bp", "charges", "row_count", 1000.0, "rows", db_path)
    record_row_counts("test-bp", {"charges": 500}, db_path)

    results = check_slos("test-bp", db_path)
    assert results[0].status == "VIOLATED"

    history = db.get_slo_run_history("test-bp", db_path)
    assert len(history) == 1
    assert history[0]["status"] == "VIOLATED"
    assert history[0]["table_name"] == "charges"
    assert history[0]["slo_type"] == "row_count"


def test_om5_get_slo_compliance_summary_returns_percentage(tmp_path: Path) -> None:
    """Compliance is the share of OK runs: 3 OK + 1 VIOLATED = 75%."""
    db_path = _db(tmp_path)
    for _ in range(3):
        _seed_run(db_path, "OK")
    _seed_run(db_path, "VIOLATED")

    summary = get_slo_compliance_summary("test-bp", db_path)

    assert len(summary) == 1
    assert summary[0]["blueprint"] == "test-bp"
    assert summary[0]["table"] == "charges"
    assert summary[0]["type"] == "row_count"
    assert summary[0]["compliance_pct"] == 75.0
    assert summary[0]["run_count"] == 4


def test_om5_dashboard_shows_100_when_always_compliant(tmp_path: Path) -> None:
    """All-OK runs yield 100% compliance."""
    db_path = _db(tmp_path)
    for _ in range(5):
        _seed_run(db_path, "OK")

    summary = get_slo_compliance_summary("test-bp", db_path)

    assert summary[0]["compliance_pct"] == 100.0


def test_om5_dashboard_shows_0_when_always_violated(tmp_path: Path) -> None:
    """All-VIOLATED runs yield 0% compliance."""
    db_path = _db(tmp_path)
    for _ in range(5):
        _seed_run(db_path, "VIOLATED")

    summary = get_slo_compliance_summary("test-bp", db_path)

    assert summary[0]["compliance_pct"] == 0.0


def test_om5_dashboard_respects_window_parameter(tmp_path: Path) -> None:
    """Only the last ``window`` runs are considered."""
    db_path = _db(tmp_path)
    for _ in range(5):
        _seed_run(db_path, "OK")
    for _ in range(5):
        _seed_run(db_path, "VIOLATED")  # newest 5 are violated

    narrow = get_slo_compliance_summary("test-bp", db_path, window=3)
    wide = get_slo_compliance_summary("test-bp", db_path, window=10)

    assert narrow[0]["compliance_pct"] == 0.0  # 3 newest all VIOLATED
    assert wide[0]["compliance_pct"] == 50.0  # 5 OK / 10


def test_om5_dashboard_empty_when_no_runs(tmp_path: Path) -> None:
    """No saved runs yields an empty summary."""
    db_path = _db(tmp_path)

    assert get_slo_compliance_summary("test-bp", db_path) == []


def test_om5_run_history_ordered_newest_first(tmp_path: Path) -> None:
    """get_slo_run_history returns runs newest first."""
    db_path = _db(tmp_path)
    _seed_run(db_path, "OK")
    _seed_run(db_path, "VIOLATED")
    _seed_run(db_path, "NO_DATA")

    history = db.get_slo_run_history("test-bp", db_path)

    assert [r["status"] for r in history] == ["NO_DATA", "VIOLATED", "OK"]


def test_om5_compliance_excludes_no_data_results(tmp_path: Path) -> None:
    """NO_DATA runs are excluded from the compliance calculation."""
    db_path = _db(tmp_path)
    _seed_run(db_path, "OK")
    _seed_run(db_path, "OK")
    _seed_run(db_path, "NO_DATA")

    summary = get_slo_compliance_summary("test-bp", db_path)

    assert summary[0]["compliance_pct"] == 100.0  # 2 OK / 2 evaluated
    assert summary[0]["run_count"] == 2  # NO_DATA not counted
