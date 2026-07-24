"""Architecture Management System (AM) — dependency analysis.

AM-4 (SPEC-026) adds deterministic blueprint dependency mapping and impact
reporting. Dependencies are discovered by statically reading blueprint files
(contracts, dbt ``sources.yml``, ``blueprint.json``) and stored in ``state.db``.
AM-5 (SPEC-037) adds read-only architecture drift detection that verifies those
documented dependencies still hold against the blueprint files on disk. No AI,
no warehouse, no execution.
"""

from __future__ import annotations

from pipelinekit.architecture.dependency import (
    VALID_DEPENDENCY_TYPES,
    BlueprintDependency,
    ImpactReport,
    add_dependency,
    get_dependencies,
    get_impact_report,
    remove_dependency,
    scan_dependencies,
)
from pipelinekit.architecture.drift import (
    ArchitectureDriftReport,
    DependencyDrift,
    check_dependency_still_holds,
    detect_architecture_drift,
)

__all__ = [
    "VALID_DEPENDENCY_TYPES",
    "BlueprintDependency",
    "ImpactReport",
    "scan_dependencies",
    "add_dependency",
    "get_dependencies",
    "remove_dependency",
    "get_impact_report",
    # AM-5 — architecture drift detection (SPEC-037)
    "DependencyDrift",
    "ArchitectureDriftReport",
    "check_dependency_still_holds",
    "detect_architecture_drift",
]
