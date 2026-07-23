"""AM-4 — blueprint dependency analysis and impact reporting (SPEC-026).

Maps how installed blueprints relate to each other so engineers can answer
"if I change this blueprint, what else breaks?". Discovery is static — it reads
blueprint files on disk (contracts, dbt ``sources.yml``, ``blueprint.json``); no
execution, no AI, no warehouse. Dependency edges live in ``state.db``
(``am_dependencies`` table) — organizational state, not blueprint state
(ADR-027, mirrors ADR-024).

An edge ``from -> to`` means ``to`` depends on ``from``: ``from`` is the upstream
producer and ``to`` is the downstream consumer affected when ``from`` changes.

Three dependency types:

* ``contract`` — ``from``'s contract output table is referenced by ``to``'s
  ingestion config (``blueprint.json``).
* ``dbt_source`` — ``to``'s ``sources.yml`` references a table ``from`` produces.
* ``manual`` — an engineer explicitly declared the relationship.

Auto-detection returning ``[]`` is a valid result: the current blueprints are
independent pipelines.

See: SPEC-026, ADR-027.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from pipelinekit.core.errors import ArchitectureError
from pipelinekit.state import db

BLUEPRINTS_DIR = "blueprints"

VALID_DEPENDENCY_TYPES = {"contract", "dbt_source", "manual"}


@dataclass
class BlueprintDependency:
    """A single directed dependency edge between two blueprints."""

    id: str
    from_blueprint: str
    to_blueprint: str
    dependency_type: str  # contract | dbt_source | manual
    reason: str | None
    detected_at: str  # ISO timestamp with timezone


@dataclass
class ImpactReport:
    """The blueprints affected when a given blueprint changes."""

    blueprint_name: str
    affected_blueprints: list[BlueprintDependency]
    total_affected: int


def _utc_now() -> str:
    """Return the current time as a timezone-aware ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _row_to_dependency(row: dict) -> BlueprintDependency:
    """Rebuild a ``BlueprintDependency`` from a stored ``am_dependencies`` row."""
    return BlueprintDependency(
        id=row["id"],
        from_blueprint=row["from_blueprint"],
        to_blueprint=row["to_blueprint"],
        dependency_type=row["dependency_type"],
        reason=row["reason"],
        detected_at=row["detected_at"],
    )


def _blueprint_installed(blueprints_dir: str, name: str) -> bool:
    """Return True if ``{blueprints_dir}/{name}/`` exists."""
    return (Path(blueprints_dir) / name).is_dir()


def _validate_dependency_type(dependency_type: str) -> None:
    """Raise ``PK-AM-002`` if ``dependency_type`` is not recognized."""
    if dependency_type not in VALID_DEPENDENCY_TYPES:
        raise ArchitectureError(
            "PK-AM-002",
            f"Invalid dependency type: {dependency_type!r}. "
            f"Must be one of: {', '.join(sorted(VALID_DEPENDENCY_TYPES))}.",
            {"dependency_type": dependency_type},
        )


# --- Static file scanning -------------------------------------------------


def _producer_tables(blueprint_dir: Path) -> set[str]:
    """Return the table names a blueprint produces (from ``contracts/*.yaml``).

    Each contract file declares the table it governs via its ``table:`` field.
    Unreadable or malformed contract files are skipped, never raised.
    """
    tables: set[str] = set()
    contracts_dir = blueprint_dir / "contracts"
    if not contracts_dir.is_dir():
        return tables
    for path in sorted(contracts_dir.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            continue
        table = data.get("table") if isinstance(data, dict) else None
        if isinstance(table, str) and table:
            tables.add(table)
    return tables


def _source_tables(blueprint_dir: Path) -> set[str]:
    """Return the source table names a blueprint consumes (``sources.yml``).

    Walks every ``sources.yml`` under ``transform/models/`` and collects each
    ``sources[].tables[].name``. Unreadable or malformed files are skipped.
    """
    tables: set[str] = set()
    models_dir = blueprint_dir / "transform" / "models"
    if not models_dir.is_dir():
        return tables
    for path in sorted(models_dir.rglob("sources.yml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            continue
        for source in (data.get("sources") or []) if isinstance(data, dict) else []:
            for table in source.get("tables") or []:
                name = table.get("name") if isinstance(table, dict) else None
                if isinstance(name, str) and name:
                    tables.add(name)
    return tables


def _ingestion_tables(blueprint_dir: Path) -> set[str]:
    """Return the source table names declared in ``blueprint.json`` ingestion.

    Looks for an explicit ``tables`` list at the top level or under ``source``.
    Current blueprints declare ingestion by connector type, not table names, so
    this is usually empty — that is expected.
    """
    tables: set[str] = set()
    path = blueprint_dir / "blueprint.json"
    if not path.is_file():
        return tables
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return tables
    if not isinstance(data, dict):
        return tables
    candidates = data.get("tables")
    source = data.get("source")
    if isinstance(source, dict) and source.get("tables"):
        candidates = source.get("tables")
    for entry in candidates or []:
        if isinstance(entry, str) and entry:
            tables.add(entry)
        elif isinstance(entry, dict) and isinstance(entry.get("name"), str):
            tables.add(entry["name"])
    return tables


def scan_dependencies(blueprints_dir: str, db_path: str) -> list[BlueprintDependency]:
    """Auto-detect dependencies between installed blueprints and store them.

    For each ordered pair of distinct blueprints ``(A, B)``:

    * ``contract`` — a table ``A`` produces (its contract ``table:``) appears in
      ``B``'s ingestion config (``blueprint.json``).
    * ``dbt_source`` — a table ``A`` produces is referenced by ``B``'s
      ``sources.yml`` sources.

    Returns the detected edges (empty when the blueprints are independent — a
    valid result). Detected edges are persisted to ``am_dependencies``.
    """
    root = Path(blueprints_dir)
    if not root.is_dir():
        return []

    names = sorted(entry.name for entry in root.iterdir() if entry.is_dir())
    producers = {name: _producer_tables(root / name) for name in names}
    sources = {name: _source_tables(root / name) for name in names}
    ingestion = {name: _ingestion_tables(root / name) for name in names}

    detected: list[BlueprintDependency] = []
    for producer in names:
        for consumer in names:
            if producer == consumer:
                continue
            contract_match = sorted(producers[producer] & ingestion[consumer])
            if contract_match:
                detected.append(
                    _make_dependency(
                        producer,
                        consumer,
                        "contract",
                        f"{consumer} ingests {', '.join(contract_match)} "
                        f"produced by {producer}",
                    )
                )
            source_match = sorted(producers[producer] & sources[consumer])
            if source_match:
                detected.append(
                    _make_dependency(
                        producer,
                        consumer,
                        "dbt_source",
                        f"{consumer} sources.yml references "
                        f"{', '.join(source_match)} produced by {producer}",
                    )
                )

    for dep in detected:
        db.insert_dependency(dep, db_path)
    return detected


def _make_dependency(
    from_blueprint: str, to_blueprint: str, dependency_type: str, reason: str | None
) -> BlueprintDependency:
    """Construct a ``BlueprintDependency`` with a fresh id and timestamp."""
    return BlueprintDependency(
        id=str(uuid.uuid4()),
        from_blueprint=from_blueprint,
        to_blueprint=to_blueprint,
        dependency_type=dependency_type,
        reason=reason,
        detected_at=_utc_now(),
    )


# --- Manual management + queries ------------------------------------------


def add_dependency(
    from_blueprint: str,
    to_blueprint: str,
    dependency_type: str,
    reason: str | None,
    blueprints_dir: str,
    db_path: str,
) -> BlueprintDependency:
    """Add a dependency edge manually.

    Raises:
        ArchitectureError: ``PK-AM-002`` if ``dependency_type`` is invalid,
            ``PK-AM-001`` if either blueprint is not installed.
    """
    _validate_dependency_type(dependency_type)
    for name in (from_blueprint, to_blueprint):
        if not _blueprint_installed(blueprints_dir, name):
            raise ArchitectureError(
                "PK-AM-001",
                f"Blueprint not found: {name}",
                {"blueprint_name": name},
            )

    dep = _make_dependency(from_blueprint, to_blueprint, dependency_type, reason)
    db.insert_dependency(dep, db_path)
    return dep


def get_dependencies(db_path: str) -> list[BlueprintDependency]:
    """Return every stored dependency edge."""
    return [_row_to_dependency(row) for row in db.get_all_dependencies(db_path)]


def remove_dependency(from_blueprint: str, to_blueprint: str, db_path: str) -> bool:
    """Remove the dependency between two blueprints. True if one existed."""
    return db.delete_dependency(from_blueprint, to_blueprint, db_path)


def get_impact_report(blueprint_name: str, db_path: str) -> ImpactReport:
    """Return the blueprints affected when ``blueprint_name`` changes.

    These are the edges whose ``from_blueprint`` is ``blueprint_name``; each
    ``to_blueprint`` is a downstream consumer that may be affected.
    """
    affected = [
        _row_to_dependency(row)
        for row in db.get_dependencies_from(blueprint_name, db_path)
    ]
    return ImpactReport(
        blueprint_name=blueprint_name,
        affected_blueprints=affected,
        total_affected=len(affected),
    )
