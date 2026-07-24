"""AM-5 — architecture drift detection for blueprint dependencies (SPEC-037).

AM-4 maps how blueprints depend on each other and stores the edges in
``am_dependencies``. AM-5 asks a different question: do those documented
dependencies *still hold* against the blueprint files on disk today?

A dependency drifts when the relationship that justified it can no longer be
observed statically. Drift is reported by type:

* ``BLUEPRINT_MISSING`` — one endpoint of a non-manual dependency is no longer
  installed (its ``blueprints/<name>/`` directory is gone).
* ``DEPENDENCY_BROKEN`` — both blueprints are installed but the producing table
  the edge was built on is no longer referenced downstream.

The check mirrors AM-4's own detection so a ``contract`` / ``dbt_source`` edge is
considered valid under exactly the condition that would have detected it:

* ``contract`` — a table the upstream blueprint produces still appears in the
  downstream blueprint's ingestion config (``blueprint.json``).
* ``dbt_source`` — a table the upstream produces is still referenced by the
  downstream's ``sources.yml``.
* ``manual`` — always valid; a human declared it, so AM-5 never second-guesses it.

AM-5 is read-only and deterministic — no AI, no warehouse, no writes. It reports
drift; it never repairs it.

See: SPEC-037, ADR-038.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from pipelinekit.architecture.dependency import (
    BlueprintDependency,
    _ingestion_tables,
    _producer_tables,
    _source_tables,
    get_dependencies,
)


@dataclass
class DependencyDrift:
    """A single documented dependency that no longer holds."""

    from_blueprint: str
    to_blueprint: str
    dependency_type: str
    documented_reason: str | None
    drift_type: str  # DEPENDENCY_BROKEN | BLUEPRINT_MISSING
    detail: str


@dataclass
class ArchitectureDriftReport:
    """The drift outcome across every documented dependency."""

    drifted_dependencies: list[DependencyDrift]
    clean_dependencies: int
    total_dependencies: int
    generated_at: str


def check_dependency_still_holds(dep: BlueprintDependency, blueprints_dir: str) -> bool:
    """Return True if a documented dependency still holds against files on disk.

    ``manual`` edges are always valid. For ``contract`` / ``dbt_source`` edges,
    both blueprint directories must exist and the upstream producer table must
    still be referenced by the downstream (ingestion config / ``sources.yml``
    respectively). A missing blueprint directory means the edge does not hold.
    """
    if dep.dependency_type == "manual":
        return True

    root = Path(blueprints_dir)
    from_dir = root / dep.from_blueprint
    to_dir = root / dep.to_blueprint
    if not from_dir.is_dir() or not to_dir.is_dir():
        return False

    producers = _producer_tables(from_dir)
    if dep.dependency_type == "contract":
        return bool(producers & _ingestion_tables(to_dir))
    if dep.dependency_type == "dbt_source":
        return bool(producers & _source_tables(to_dir))
    # Unknown type — do not raise a false alarm.
    return True


def detect_architecture_drift(
    blueprints_dir: str, db_path: str
) -> ArchitectureDriftReport:
    """Check every documented dependency for drift against blueprint files.

    Manual edges are always clean. For other edges, a missing endpoint directory
    is reported as ``BLUEPRINT_MISSING``; an edge whose producing table is no
    longer referenced downstream is ``DEPENDENCY_BROKEN``.
    """
    generated_at = datetime.now(timezone.utc).isoformat()
    dependencies = get_dependencies(db_path)
    root = Path(blueprints_dir)

    drifted: list[DependencyDrift] = []
    clean = 0
    for dep in dependencies:
        if dep.dependency_type == "manual":
            clean += 1
            continue

        from_missing = not (root / dep.from_blueprint).is_dir()
        to_missing = not (root / dep.to_blueprint).is_dir()
        if from_missing or to_missing:
            missing = [
                name
                for name, gone in (
                    (dep.from_blueprint, from_missing),
                    (dep.to_blueprint, to_missing),
                )
                if gone
            ]
            drifted.append(
                DependencyDrift(
                    from_blueprint=dep.from_blueprint,
                    to_blueprint=dep.to_blueprint,
                    dependency_type=dep.dependency_type,
                    documented_reason=dep.reason,
                    drift_type="BLUEPRINT_MISSING",
                    detail=f"blueprint not installed: {', '.join(missing)}",
                )
            )
        elif not check_dependency_still_holds(dep, blueprints_dir):
            drifted.append(
                DependencyDrift(
                    from_blueprint=dep.from_blueprint,
                    to_blueprint=dep.to_blueprint,
                    dependency_type=dep.dependency_type,
                    documented_reason=dep.reason,
                    drift_type="DEPENDENCY_BROKEN",
                    detail=(
                        f"{dep.from_blueprint} no longer provides a table "
                        f"referenced by {dep.to_blueprint}"
                    ),
                )
            )
        else:
            clean += 1

    return ArchitectureDriftReport(
        drifted_dependencies=drifted,
        clean_dependencies=clean,
        total_dependencies=len(dependencies),
        generated_at=generated_at,
    )
