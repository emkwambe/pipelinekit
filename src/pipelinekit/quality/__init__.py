"""Quality Management System (QM) — coverage and quality measurement.

QM-4 (SPEC-022) adds deterministic, read-only quality coverage monitoring over
dbt ``schema.yml`` and Soda ``checks.yaml`` files. No AI, no warehouse, no state
writes.
"""

from __future__ import annotations

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
]
