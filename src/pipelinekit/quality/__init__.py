"""Quality Management System (QM) — coverage and quality measurement.

QM-4 (SPEC-022) adds deterministic, read-only quality coverage monitoring over
dbt ``schema.yml`` and Soda ``checks.yaml`` files. QM-6 (SPEC-024) adds volume
anomaly detection over recorded row counts in ``state.db``. Both are fully
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
]
