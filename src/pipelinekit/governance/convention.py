"""GM-2 — naming convention enforcement for blueprint governance (SPEC-028).

Defines regex-based naming conventions per scope (blueprint, table, column,
contract file) and checks installed blueprints against them. Conventions live in
``state.db`` (``gm_conventions``) — organizational state, not blueprint state
(ADR-029, mirrors ADR-024). Checking is read-only and deterministic — no AI, no
warehouse — and violations are warnings only; GM-2 never blocks execution.

A name PASSES a scope if it matches at least one registered convention for that
scope (``re.fullmatch``); a name with no matching convention is a violation.

See: SPEC-028, ADR-029.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from pipelinekit.core.errors import GovernanceError
from pipelinekit.quality.coverage import scan_dbt_coverage
from pipelinekit.state import db

BLUEPRINTS_DIR = "blueprints"

VALID_SCOPES = {"blueprint", "table", "column", "contract_file"}


@dataclass
class NamingConvention:
    """A regex naming convention scoped to one kind of name."""

    id: str
    scope: str  # blueprint | table | column | contract_file
    pattern: str  # regex pattern
    description: str | None
    created_at: str


@dataclass
class ConventionViolation:
    """A single name that matched no convention for its scope."""

    name: str  # the name that violated
    scope: str
    pattern: str
    convention_id: str
    description: str | None


@dataclass
class ConventionCheckResult:
    """The outcome of checking one blueprint against all conventions."""

    blueprint_name: str
    violations: list[ConventionViolation]
    checked_count: int
    violation_count: int
    is_compliant: bool


def _utc_now() -> str:
    """Return the current time as a timezone-aware ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _row_to_convention(row: dict) -> NamingConvention:
    """Rebuild a ``NamingConvention`` from a stored ``gm_conventions`` row."""
    return NamingConvention(
        id=row["id"],
        scope=row["scope"],
        pattern=row["pattern"],
        description=row["description"],
        created_at=row["created_at"],
    )


def add_convention(
    scope: str,
    pattern: str,
    description: str | None,
    db_path: str,
) -> NamingConvention:
    """Add a naming convention after validating its scope and regex.

    Raises:
        GovernanceError: ``PK-GM-003`` if ``scope`` is invalid,
            ``PK-GM-004`` if ``pattern`` is not valid regex.
    """
    if scope not in VALID_SCOPES:
        raise GovernanceError(
            "PK-GM-003",
            f"Invalid convention scope: {scope!r}. "
            f"Must be one of: {', '.join(sorted(VALID_SCOPES))}.",
            {"scope": scope},
        )
    try:
        re.compile(pattern)
    except re.error as exc:
        raise GovernanceError(
            "PK-GM-004",
            f"Invalid regex pattern: {pattern!r} ({exc})",
            {"pattern": pattern, "detail": str(exc)},
        ) from exc

    convention = NamingConvention(
        id=str(uuid.uuid4()),
        scope=scope,
        pattern=pattern,
        description=description,
        created_at=_utc_now(),
    )
    db.insert_convention(convention, db_path)
    return convention


def get_conventions(db_path: str) -> list[NamingConvention]:
    """Return every registered naming convention."""
    return [_row_to_convention(row) for row in db.get_conventions(db_path)]


def remove_convention(convention_id: str, db_path: str) -> bool:
    """Remove a convention by id. Return True if one existed and was removed."""
    return db.delete_convention(convention_id, db_path)


def extract_names_for_scope(
    blueprint_name: str,
    scope: str,
    blueprints_dir: str,
) -> list[str]:
    """Extract all names of ``scope`` from a blueprint's files.

    * ``blueprint`` — the blueprint name itself.
    * ``table`` — dbt model names from ``schema.yml`` (via ``scan_dbt_coverage``).
    * ``column`` — de-duplicated column names across all dbt models.
    * ``contract_file`` — ``*.yaml`` filenames under ``contracts/``.

    Returns an empty list when the underlying files do not exist.
    """
    if scope == "blueprint":
        return [blueprint_name]

    blueprint_dir = Path(blueprints_dir) / blueprint_name

    if scope == "table":
        return [model.name for model in scan_dbt_coverage(str(blueprint_dir))]

    if scope == "column":
        names: list[str] = []
        for model in scan_dbt_coverage(str(blueprint_dir)):
            names.extend(col.name for col in model.columns)
        # De-duplicate while preserving first-seen order.
        return list(dict.fromkeys(names))

    if scope == "contract_file":
        contracts_dir = blueprint_dir / "contracts"
        if not contracts_dir.is_dir():
            return []
        return [path.name for path in sorted(contracts_dir.glob("*.yaml"))]

    return []


def check_blueprint_conventions(
    blueprint_name: str,
    blueprints_dir: str,
    db_path: str,
) -> ConventionCheckResult:
    """Check a blueprint's names against all registered conventions.

    For every scope that has at least one convention, each name of that scope is
    checked against all conventions for the scope; a name matching none is a
    violation. Returns a fully-compliant (empty) result when no conventions are
    defined. Read-only — never blocks execution.
    """
    conventions = get_conventions(db_path)
    if not conventions:
        return ConventionCheckResult(
            blueprint_name=blueprint_name,
            violations=[],
            checked_count=0,
            violation_count=0,
            is_compliant=True,
        )

    by_scope: dict[str, list[NamingConvention]] = {}
    for convention in conventions:
        by_scope.setdefault(convention.scope, []).append(convention)

    violations: list[ConventionViolation] = []
    checked = 0
    for scope, scope_conventions in by_scope.items():
        for name in extract_names_for_scope(blueprint_name, scope, blueprints_dir):
            checked += 1
            if any(re.fullmatch(c.pattern, name) for c in scope_conventions):
                continue
            # Report against the first convention for this scope.
            first = scope_conventions[0]
            violations.append(
                ConventionViolation(
                    name=name,
                    scope=scope,
                    pattern=first.pattern,
                    convention_id=first.id,
                    description=first.description,
                )
            )

    return ConventionCheckResult(
        blueprint_name=blueprint_name,
        violations=violations,
        checked_count=checked,
        violation_count=len(violations),
        is_compliant=len(violations) == 0,
    )
