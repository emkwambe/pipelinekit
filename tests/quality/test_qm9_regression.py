"""Tests for QM-9 quality regression testing (SPEC-038).

Deterministic, no AI. Every test uses a ``tmp_path`` SQLite database — the real
``blueprints/`` directory and project ``state.db`` are never touched. Regression
logic is exercised by seeding ``qm_scorecard_snapshots`` directly; the auto-save
path is exercised through ``compute_blueprint_score`` against a minimal fixture.
"""

from __future__ import annotations

from pathlib import Path

from pipelinekit.quality.regression import check_regression
from pipelinekit.quality.scorecard import compute_blueprint_score
from pipelinekit.state import db


def _dbp(tmp_path: Path) -> str:
    """Return a path to an isolated state database for this test."""
    return str(tmp_path / "state.db")


def _seed(
    db_path: str,
    blueprint: str = "test-bp",
    *,
    coverage: float = 80.0,
    composite: float = 80.0,
    volume: float = 100.0,
    drift: float = 100.0,
    ownership: float = 100.0,
    rating: str = "Good",
) -> None:
    """Insert one scorecard snapshot with explicit component scores."""
    db.insert_scorecard_snapshot(
        blueprint, composite, coverage, volume, drift, ownership, rating, db_path
    )


def _install(tmp_path: Path, name: str) -> str:
    """Create a minimal installed blueprint and return its directory path."""
    bp = tmp_path / "blueprints" / name
    models = bp / "transform" / "models" / "staging"
    models.mkdir(parents=True)
    (bp / "blueprint.json").write_text(f'{{"name": "{name}"}}', encoding="utf-8")
    (models / "schema.yml").write_text(
        "version: 2\nmodels:\n  - name: orders\n"
        "    columns:\n      - name: order_id\n        tests: [unique, not_null]\n",
        encoding="utf-8",
    )
    return str(bp)


def test_qm9_compute_score_saves_snapshot(tmp_path: Path) -> None:
    """compute_blueprint_score persists a snapshot to qm_scorecard_snapshots."""
    db_path = _dbp(tmp_path)
    bp_dir = _install(tmp_path, "orders-bp")

    score = compute_blueprint_score("orders-bp", bp_dir, db_path)

    history = db.get_scorecard_history("orders-bp", db_path)
    assert len(history) == 1
    assert history[0]["blueprint_name"] == "orders-bp"
    assert history[0]["composite_score"] == score.composite_score
    assert history[0]["rating"] == score.rating


def test_qm9_check_regression_returns_clean_when_stable(tmp_path: Path) -> None:
    """Stable snapshots produce no regression."""
    db_path = _dbp(tmp_path)
    for _ in range(4):
        _seed(db_path, coverage=80.0, composite=80.0)

    report = check_regression("test-bp", db_path)

    assert report.is_regression is False
    assert report.regressions == []


def test_qm9_check_regression_detects_coverage_drop(tmp_path: Path) -> None:
    """A coverage drop beyond the threshold is flagged as coverage_drop."""
    db_path = _dbp(tmp_path)
    _seed(db_path, coverage=90.0)
    _seed(db_path, coverage=90.0)
    _seed(db_path, coverage=70.0)  # latest

    report = check_regression("test-bp", db_path)

    assert report.is_regression is True
    types = {r.regression_type for r in report.regressions}
    assert "coverage_drop" in types


def test_qm9_check_regression_detects_score_drop(tmp_path: Path) -> None:
    """A composite score drop beyond the threshold is flagged as score_drop."""
    db_path = _dbp(tmp_path)
    _seed(db_path, composite=85.0)
    _seed(db_path, composite=85.0)
    _seed(db_path, composite=70.0)  # latest

    report = check_regression("test-bp", db_path)

    types = {r.regression_type for r in report.regressions}
    assert "score_drop" in types


def test_qm9_check_regression_detects_drift_introduced(tmp_path: Path) -> None:
    """A drop in drift score (new drift) is flagged as drift_introduced."""
    db_path = _dbp(tmp_path)
    _seed(db_path, drift=100.0)
    _seed(db_path, drift=100.0)
    _seed(db_path, drift=0.0)  # latest — drift appeared

    report = check_regression("test-bp", db_path)

    types = {r.regression_type for r in report.regressions}
    assert "drift_introduced" in types


def test_qm9_check_regression_insufficient_data_returns_no_regression(
    tmp_path: Path,
) -> None:
    """Fewer than two snapshots means no baseline — never a regression."""
    db_path = _dbp(tmp_path)
    _seed(db_path, coverage=10.0, composite=10.0)  # single snapshot

    report = check_regression("test-bp", db_path)

    assert report.is_regression is False


def test_qm9_threshold_configurable(tmp_path: Path) -> None:
    """The same 7-point drop regresses at threshold 5 but not at threshold 10."""
    db_path = _dbp(tmp_path)
    _seed(db_path, coverage=90.0)
    _seed(db_path, coverage=90.0)
    _seed(db_path, coverage=83.0)  # latest — dropped 7 points

    assert check_regression("test-bp", db_path, threshold=5.0).is_regression is True
    assert check_regression("test-bp", db_path, threshold=10.0).is_regression is False


def test_qm9_window_configurable(tmp_path: Path) -> None:
    """The window controls how many previous snapshots form the baseline."""
    db_path = _dbp(tmp_path)
    _seed(db_path, coverage=70.0)  # oldest
    _seed(db_path, coverage=70.0)
    _seed(db_path, coverage=90.0)  # immediate previous
    _seed(db_path, coverage=82.0)  # latest

    # window=1: baseline is just the 90 snapshot -> 82 < 85 -> regression.
    assert check_regression("test-bp", db_path, window=1).is_regression is True
    # window=3: baseline avg (90+70+70)/3 = 76.7 -> 82 is above -> clean.
    assert check_regression("test-bp", db_path, window=3).is_regression is False


def test_qm9_get_scorecard_history_returns_newest_first(tmp_path: Path) -> None:
    """get_scorecard_history returns snapshots newest first."""
    db_path = _dbp(tmp_path)
    _seed(db_path, composite=10.0)
    _seed(db_path, composite=20.0)
    _seed(db_path, composite=30.0)  # newest

    history = db.get_scorecard_history("test-bp", db_path)

    assert [s["composite_score"] for s in history] == [30.0, 20.0, 10.0]
