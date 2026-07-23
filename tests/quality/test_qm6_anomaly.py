"""Tests for QM-6 volume anomaly detection (SPEC-024).

Deterministic, no AI. Every test uses a ``tmp_path`` SQLite database — the real
``blueprints/`` directory and project ``state.db`` are never touched.
"""

from __future__ import annotations

from pathlib import Path

from pipelinekit.quality.anomaly import (
    RowCountSnapshot,
    check_volume_anomalies,
    compute_baseline,
    compute_deviation_pct,
    get_row_count_history,
    record_row_counts,
)


def _db(tmp_path: Path) -> str:
    """Return a path to an isolated state database for this test."""
    return str(tmp_path / "state.db")


def _seed_baseline(db_path: str, table: str = "charges", n: int = 5) -> None:
    """Record ``n`` baseline snapshots around 45,000 for ``table``."""
    for i in range(n):
        record_row_counts("test-bp", {table: 45000 + i * 100}, db_path)


def test_qm6_record_row_counts_creates_snapshots(tmp_path: Path) -> None:
    """record_row_counts creates RowCountSnapshot for each table."""
    db_path = _db(tmp_path)

    snapshots = record_row_counts("test-bp", {"charges": 45231}, db_path)

    assert len(snapshots) == 1
    snap = snapshots[0]
    assert isinstance(snap, RowCountSnapshot)
    assert snap.blueprint_name == "test-bp"
    assert snap.table_name == "charges"
    assert snap.row_count == 45231
    assert snap.recorded_at  # ISO timestamp populated


def test_qm6_record_row_counts_multiple_tables(tmp_path: Path) -> None:
    """record_row_counts handles a dict with multiple tables."""
    db_path = _db(tmp_path)

    snapshots = record_row_counts(
        "test-bp", {"charges": 45231, "customers": 12840}, db_path
    )

    assert len(snapshots) == 2
    by_table = {s.table_name: s.row_count for s in snapshots}
    assert by_table == {"charges": 45231, "customers": 12840}


def test_qm6_check_anomalies_returns_establishing_with_few_snapshots(
    tmp_path: Path,
) -> None:
    """status is ESTABLISHING when fewer than 3 snapshots exist."""
    db_path = _db(tmp_path)
    record_row_counts("test-bp", {"charges": 45000}, db_path)
    record_row_counts("test-bp", {"charges": 45100}, db_path)

    anomalies = check_volume_anomalies("test-bp", {"charges": 45050}, db_path)

    assert len(anomalies) == 1
    assert anomalies[0].status == "ESTABLISHING"
    assert anomalies[0].is_anomaly is False
    assert anomalies[0].snapshot_count == 2


def test_qm6_check_anomalies_no_anomaly_within_threshold(tmp_path: Path) -> None:
    """is_anomaly is False when deviation is within threshold."""
    db_path = _db(tmp_path)
    _seed_baseline(db_path)  # mean == 45,200

    anomalies = check_volume_anomalies(
        "test-bp", {"charges": 45300}, db_path, threshold_pct=20.0
    )

    assert anomalies[0].is_anomaly is False
    assert anomalies[0].status == "OK"
    assert anomalies[0].snapshot_count == 5


def test_qm6_check_anomalies_detects_drop_below_threshold(tmp_path: Path) -> None:
    """is_anomaly is True when count drops significantly below baseline."""
    db_path = _db(tmp_path)
    _seed_baseline(db_path)  # mean == 45,200

    anomalies = check_volume_anomalies(
        "test-bp", {"charges": 500}, db_path, threshold_pct=20.0
    )

    assert anomalies[0].is_anomaly is True
    assert anomalies[0].status == "ANOMALY"
    assert anomalies[0].deviation_pct < 0  # below baseline


def test_qm6_check_anomalies_detects_spike_above_threshold(tmp_path: Path) -> None:
    """is_anomaly is True when count spikes significantly above baseline."""
    db_path = _db(tmp_path)
    _seed_baseline(db_path)  # mean == 45,200

    anomalies = check_volume_anomalies(
        "test-bp", {"charges": 90000}, db_path, threshold_pct=20.0
    )

    assert anomalies[0].is_anomaly is True
    assert anomalies[0].status == "ANOMALY"
    assert anomalies[0].deviation_pct > 0  # above baseline


def test_qm6_check_anomalies_respects_custom_threshold(tmp_path: Path) -> None:
    """custom threshold_pct is used for comparison."""
    db_path = _db(tmp_path)
    _seed_baseline(db_path)  # mean == 45,200
    # 52,000 is ~15% above baseline: anomalous at 10%, fine at the 20% default.
    current = {"charges": 52000}

    strict = check_volume_anomalies("test-bp", current, db_path, threshold_pct=10.0)
    lenient = check_volume_anomalies("test-bp", current, db_path, threshold_pct=20.0)

    assert strict[0].is_anomaly is True
    assert strict[0].status == "ANOMALY"
    assert lenient[0].is_anomaly is False
    assert lenient[0].status == "OK"


def test_qm6_compute_baseline_returns_mean(tmp_path: Path) -> None:
    """compute_baseline returns the correct mean of snapshot row counts."""
    snapshots = [
        RowCountSnapshot("a", "bp", "charges", 100, "2026-01-01T00:00:00+00:00"),
        RowCountSnapshot("b", "bp", "charges", 200, "2026-01-02T00:00:00+00:00"),
        RowCountSnapshot("c", "bp", "charges", 300, "2026-01-03T00:00:00+00:00"),
    ]

    assert compute_baseline(snapshots) == 200.0
    assert compute_baseline([]) == 0.0


def test_qm6_compute_deviation_pct_is_correct() -> None:
    """compute_deviation_pct returns the correct percentage."""
    assert compute_deviation_pct(120, 100.0) == 20.0
    assert compute_deviation_pct(80, 100.0) == -20.0
    # A zero baseline has nothing to deviate from.
    assert compute_deviation_pct(500, 0.0) == 0.0


def test_qm6_get_row_count_history_returns_newest_first(tmp_path: Path) -> None:
    """get_row_count_history returns snapshots ordered newest first."""
    db_path = _db(tmp_path)
    for count in (100, 200, 300):
        record_row_counts("test-bp", {"charges": count}, db_path)

    history = get_row_count_history("test-bp", "charges", db_path)

    assert [s.row_count for s in history] == [300, 200, 100]
