"""QM-6 — volume anomaly detection (SPEC-024).

Records row counts for pipeline tables after each run and detects when the
current count deviates significantly from the rolling baseline. Purely
deterministic — no AI, no warehouse connection. Snapshots live in ``state.db``
(``qm_row_counts`` table); the baseline is the mean of the last ``window``
recorded counts, and a deviation beyond ``threshold_pct`` is flagged.

A table needs at least ``_MIN_SNAPSHOTS`` snapshots before detection activates;
until then its status is ``ESTABLISHING`` and it is never an anomaly.

See: SPEC-024, ADR-025.
"""

from __future__ import annotations

from dataclasses import dataclass

from pipelinekit.state import db

# Minimum snapshots required before anomaly detection activates (ADR-025).
_MIN_SNAPSHOTS = 3


@dataclass
class RowCountSnapshot:
    """A single recorded row count for one table of one blueprint."""

    id: str
    blueprint_name: str
    table_name: str
    row_count: int
    recorded_at: str  # ISO timestamp with timezone


@dataclass
class VolumeAnomaly:
    """The result of comparing a current count against its baseline."""

    blueprint_name: str
    table_name: str
    current_count: int
    baseline_avg: float
    deviation_pct: float  # positive = above baseline, negative = below
    is_anomaly: bool
    threshold_pct: float  # threshold used for detection
    snapshot_count: int  # number of snapshots in the baseline window
    status: str  # "OK" | "ANOMALY" | "ESTABLISHING"


def _row_to_snapshot(row: dict) -> RowCountSnapshot:
    """Rebuild a ``RowCountSnapshot`` from a stored ``qm_row_counts`` row."""
    return RowCountSnapshot(
        id=row["id"],
        blueprint_name=row["blueprint_name"],
        table_name=row["table_name"],
        row_count=row["row_count"],
        recorded_at=row["recorded_at"],
    )


def record_row_counts(
    blueprint_name: str,
    table_counts: dict[str, int],
    db_path: str,
) -> list[RowCountSnapshot]:
    """Record row counts for multiple tables in one call.

    ``table_counts`` example: ``{"charges": 45231, "customers": 12840}``.
    Returns the freshly created snapshots, in the order the tables were given.
    """
    snapshots: list[RowCountSnapshot] = []
    for table_name, row_count in table_counts.items():
        db.insert_row_count(blueprint_name, table_name, row_count, db_path)
        # Read the just-inserted snapshot back so callers get its id/timestamp.
        history = db.get_row_count_history(blueprint_name, table_name, 1, db_path)
        if history:
            snapshots.append(_row_to_snapshot(history[0]))
    return snapshots


def check_volume_anomalies(
    blueprint_name: str,
    current_counts: dict[str, int],
    db_path: str,
    threshold_pct: float = 20.0,
    window: int = 7,
) -> list[VolumeAnomaly]:
    """Compare ``current_counts`` against the rolling baseline per table.

    For each table in ``current_counts``:

    * Get the last ``window`` snapshots from the database.
    * If fewer than three snapshots exist: ``status = "ESTABLISHING"`` and
      ``is_anomaly = False``.
    * Otherwise: ``baseline_avg`` is the mean of those snapshots,
      ``deviation_pct = (current - baseline_avg) / baseline_avg * 100``, and
      ``is_anomaly`` is ``abs(deviation_pct) > threshold_pct``.

    Returns one ``VolumeAnomaly`` per table in ``current_counts``.
    """
    anomalies: list[VolumeAnomaly] = []
    for table_name, current in current_counts.items():
        snapshots = get_row_count_history(
            blueprint_name, table_name, db_path, limit=window
        )
        snapshot_count = len(snapshots)
        baseline_avg = compute_baseline(snapshots)
        deviation_pct = compute_deviation_pct(current, baseline_avg)

        if snapshot_count < _MIN_SNAPSHOTS:
            status = "ESTABLISHING"
            is_anomaly = False
        else:
            is_anomaly = abs(deviation_pct) > threshold_pct
            status = "ANOMALY" if is_anomaly else "OK"

        anomalies.append(
            VolumeAnomaly(
                blueprint_name=blueprint_name,
                table_name=table_name,
                current_count=current,
                baseline_avg=baseline_avg,
                deviation_pct=deviation_pct,
                is_anomaly=is_anomaly,
                threshold_pct=threshold_pct,
                snapshot_count=snapshot_count,
                status=status,
            )
        )
    return anomalies


def get_row_count_history(
    blueprint_name: str,
    table_name: str,
    db_path: str,
    limit: int = 10,
) -> list[RowCountSnapshot]:
    """Return historical row counts for a table, newest first (QM-6).

    Wraps the state-layer reader and returns typed ``RowCountSnapshot`` objects.
    Note the argument order differs from ``db.get_row_count_history``.
    """
    rows = db.get_row_count_history(blueprint_name, table_name, limit, db_path)
    return [_row_to_snapshot(row) for row in rows]


def compute_baseline(snapshots: list[RowCountSnapshot]) -> float:
    """Return the mean row count across ``snapshots``; ``0.0`` if empty."""
    if not snapshots:
        return 0.0
    return sum(s.row_count for s in snapshots) / len(snapshots)


def compute_deviation_pct(current: int, baseline: float) -> float:
    """Return the percentage deviation of ``current`` from ``baseline``.

    Formula: ``(current - baseline) / baseline * 100``. Returns ``0.0`` when
    ``baseline`` is ``0.0`` (no baseline to deviate from).
    """
    if baseline == 0.0:
        return 0.0
    return (current - baseline) / baseline * 100
