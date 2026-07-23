"""Architecture Management System (AM) — dependency analysis.

AM-4 (SPEC-026) adds deterministic blueprint dependency mapping and impact
reporting. Dependencies are discovered by statically reading blueprint files
(contracts, dbt ``sources.yml``, ``blueprint.json``) and stored in ``state.db``.
No AI, no warehouse, no execution.
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

__all__ = [
    "VALID_DEPENDENCY_TYPES",
    "BlueprintDependency",
    "ImpactReport",
    "scan_dependencies",
    "add_dependency",
    "get_dependencies",
    "remove_dependency",
    "get_impact_report",
]
