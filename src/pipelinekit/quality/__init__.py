"""Quality Management System (QM) — coverage and quality measurement.

QM-4 (SPEC-022) adds deterministic, read-only quality coverage monitoring over
dbt ``schema.yml`` and Soda ``checks.yaml`` files. QM-6 (SPEC-024) adds volume
anomaly detection over recorded row counts in ``state.db``. QM-7 (SPEC-029) adds
schema drift detection between contracts and ``schema.yml``. All are fully
deterministic — no AI, no warehouse connection.
"""

from __future__ import annotations

from pipelinekit.quality.anomaly import (
    RowCountSnapshot,
    VolumeAnomaly,
    check_volume_anomalies,
    compute_baseline,
    compute_deviation_pct,
    get_row_count_history,
    record_row_counts,
)
from pipelinekit.quality.coverage import (
    BlueprintCoverage,
    ColumnCoverage,
    CoverageReport,
    ModelCoverage,
    SodaCoverage,
    compute_blueprint_coverage,
    compute_coverage_report,
    scan_dbt_coverage,
    scan_soda_coverage,
)
from pipelinekit.quality.drift import (
    DriftItem,
    DriftReport,
    DriftType,
    TableDriftResult,
    check_all_drift,
    check_blueprint_drift,
)
from pipelinekit.quality.scorecard import (
    BlueprintScore,
    ComponentScore,
    ScorecardReport,
    compute_blueprint_score,
    compute_scorecard,
    get_rating,
)

__all__ = [
    "ColumnCoverage",
    "ModelCoverage",
    "SodaCoverage",
    "BlueprintCoverage",
    "CoverageReport",
    "scan_dbt_coverage",
    "scan_soda_coverage",
    "compute_blueprint_coverage",
    "compute_coverage_report",
    # QM-6 — volume anomaly detection (SPEC-024)
    "RowCountSnapshot",
    "VolumeAnomaly",
    "record_row_counts",
    "check_volume_anomalies",
    "get_row_count_history",
    "compute_baseline",
    "compute_deviation_pct",
    # QM-7 — schema drift detection (SPEC-029)
    "DriftType",
    "DriftItem",
    "TableDriftResult",
    "DriftReport",
    "check_blueprint_drift",
    "check_all_drift",
    # QM-8 — composite quality scorecard (SPEC-030)
    "ComponentScore",
    "BlueprintScore",
    "ScorecardReport",
    "compute_blueprint_score",
    "compute_scorecard",
    "get_rating",
]
