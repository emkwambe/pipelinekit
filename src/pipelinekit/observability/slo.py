"""OM-4 — Service Level Objective (SLO) definition and evaluation (SPEC-025).

Defines measurable targets for installed blueprints and evaluates them against
data already in ``state.db`` — no warehouse connection, no AI. Three SLO types:

* ``freshness`` — newest contract snapshot must be younger than N hours
  (reads DC-8 ``dc_contract_versions``).
* ``row_count`` — latest recorded row count must be at least N rows
  (reads QM-6 ``qm_row_counts``).
* ``coverage`` — a dbt model's test coverage must be at least N percent
  (runs QM-4 ``scan_dbt_coverage``).

SLO definitions live in ``state.db`` (``om_slos`` table) — organizational state,
not blueprint state (ADR-026, mirrors ADR-024). Evaluation never raises on a
violation: a breached SLO is reported as ``VIOLATED`` and a missing data source
as ``NO_DATA``. Only an invalid SLO type raises (``PK-OM-002``).

See: SPEC-025, ADR-026.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from pipelinekit.core.errors import ObservabilityError
from pipelinekit.quality.coverage import scan_dbt_coverage
from pipelinekit.state import db

BLUEPRINTS_DIR = "blueprints"

VALID_SLO_TYPES = {"freshness", "row_count", "coverage"}


@dataclass
class SLODefinition:
    """A single Service Level Objective for one blueprint/table."""

    id: str
    blueprint_name: str
    table_name: str
    slo_type: str  # freshness | row_count | coverage
    threshold: float  # hours (freshness) | rows (row_count) | percent (coverage)
    unit: str | None  # "hours" | "rows" | "percent" | None
    created_at: str
    updated_at: str


@dataclass
class SLOResult:
    """The outcome of evaluating one SLO against current state."""

    slo: SLODefinition
    current_value: float | None
    is_met: bool
    status: str  # "OK" | "VIOLATED" | "NO_DATA"
    message: str


def _utc_now() -> str:
    """Return the current time as a timezone-aware ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(timestamp: str) -> datetime:
    """Parse an ISO timestamp, tolerating a trailing ``Z`` and naive values.

    DC-8 stores ``created_at`` as ``...Z``; other callers use ``isoformat`` with
    a ``+00:00`` offset. A naive value is assumed to be UTC.
    """
    normalized = timestamp[:-1] + "+00:00" if timestamp.endswith("Z") else timestamp
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _row_to_slo(row: dict) -> SLODefinition:
    """Rebuild an ``SLODefinition`` from a stored ``om_slos`` row."""
    return SLODefinition(
        id=row["id"],
        blueprint_name=row["blueprint_name"],
        table_name=row["table_name"],
        slo_type=row["slo_type"],
        threshold=row["threshold"],
        unit=row["unit"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _validate_slo_type(slo_type: str) -> None:
    """Raise ``PK-OM-002`` if ``slo_type`` is not a recognized SLO type."""
    if slo_type not in VALID_SLO_TYPES:
        raise ObservabilityError(
            "PK-OM-002",
            f"Invalid SLO type: {slo_type!r}. "
            f"Must be one of: {', '.join(sorted(VALID_SLO_TYPES))}.",
            {"slo_type": slo_type},
        )


def set_slo(
    blueprint_name: str,
    table_name: str,
    slo_type: str,
    threshold: float,
    unit: str | None,
    db_path: str,
) -> SLODefinition:
    """Assign or update an SLO for a blueprint/table.

    Raises:
        ObservabilityError: ``PK-OM-002`` if ``slo_type`` is invalid.
    """
    _validate_slo_type(slo_type)

    existing = _find_slo(blueprint_name, table_name, slo_type, db_path)
    now = _utc_now()
    if existing is not None:
        slo_id = existing.id
        created_at = existing.created_at
    else:
        slo_id = str(uuid.uuid4())
        created_at = now

    slo = SLODefinition(
        id=slo_id,
        blueprint_name=blueprint_name,
        table_name=table_name,
        slo_type=slo_type,
        threshold=threshold,
        unit=unit,
        created_at=created_at,
        updated_at=now,
    )
    db.upsert_slo(slo, db_path)
    return slo


def get_slos(blueprint_name: str, db_path: str) -> list[SLODefinition]:
    """Return every SLO defined for a blueprint."""
    return [_row_to_slo(row) for row in db.get_slos(blueprint_name, db_path)]


def get_all_slos(db_path: str) -> list[SLODefinition]:
    """Return every SLO across all blueprints."""
    return [_row_to_slo(row) for row in db.get_all_slos(db_path)]


def remove_slo(
    blueprint_name: str,
    table_name: str,
    slo_type: str,
    db_path: str,
) -> bool:
    """Remove one SLO. Return True if it existed and was removed.

    Raises:
        ObservabilityError: ``PK-OM-002`` if ``slo_type`` is invalid.
    """
    _validate_slo_type(slo_type)
    return db.delete_slo(blueprint_name, table_name, slo_type, db_path)


def _find_slo(
    blueprint_name: str, table_name: str, slo_type: str, db_path: str
) -> SLODefinition | None:
    """Return the SLO matching the triple, or None."""
    for slo in get_slos(blueprint_name, db_path):
        if slo.table_name == table_name and slo.slo_type == slo_type:
            return slo
    return None


def check_slos(blueprint_name: str, db_path: str) -> list[SLOResult]:
    """Evaluate every SLO for a blueprint against current ``state.db`` data.

    Never raises on a breach: a violated SLO yields ``status="VIOLATED"`` and a
    missing data source yields ``status="NO_DATA"``.
    """
    results: list[SLOResult] = []
    for slo in get_slos(blueprint_name, db_path):
        if slo.slo_type == "freshness":
            results.append(_check_freshness(slo, db_path))
        elif slo.slo_type == "row_count":
            results.append(_check_row_count(slo, db_path))
        elif slo.slo_type == "coverage":
            results.append(_check_coverage(slo))
        # No else: only VALID_SLO_TYPES can be stored (set_slo validates).
    return results


def _no_data(slo: SLODefinition, message: str) -> SLOResult:
    """Build a ``NO_DATA`` result for an SLO with no evaluable source."""
    return SLOResult(
        slo=slo,
        current_value=None,
        is_met=False,
        status="NO_DATA",
        message=message,
    )


def _evaluated(
    slo: SLODefinition, current_value: float, is_met: bool, message: str
) -> SLOResult:
    """Build an OK/VIOLATED result from an evaluated SLO."""
    return SLOResult(
        slo=slo,
        current_value=current_value,
        is_met=is_met,
        status="OK" if is_met else "VIOLATED",
        message=message,
    )


def _check_freshness(slo: SLODefinition, db_path: str) -> SLOResult:
    """Evaluate a freshness SLO against the newest contract snapshot."""
    row = db.get_latest_contract_version_for_blueprint(slo.blueprint_name, db_path)
    if row is None:
        return _no_data(slo, "No contract snapshot found for freshness evaluation.")

    created_at = _parse_iso(row["created_at"])
    hours_ago = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600
    is_met = hours_ago < slo.threshold
    message = f"Last snapshot {hours_ago:.1f}h ago " f"(SLO: < {slo.threshold:g}h)"
    return _evaluated(slo, hours_ago, is_met, message)


def _check_row_count(slo: SLODefinition, db_path: str) -> SLOResult:
    """Evaluate a row_count SLO against the latest recorded count."""
    history = db.get_row_count_history(slo.blueprint_name, slo.table_name, 1, db_path)
    if not history:
        return _no_data(slo, "No recorded row count for row_count evaluation.")

    row_count = float(history[0]["row_count"])
    is_met = row_count >= slo.threshold
    message = f"Latest count {row_count:,.0f} (SLO: >= {slo.threshold:g})"
    return _evaluated(slo, row_count, is_met, message)


def _check_coverage(slo: SLODefinition) -> SLOResult:
    """Evaluate a coverage SLO against dbt test coverage for the model."""
    blueprint_dir = Path(BLUEPRINTS_DIR) / slo.blueprint_name
    models = scan_dbt_coverage(str(blueprint_dir))
    match = next((m for m in models if m.name == slo.table_name), None)
    if match is None:
        return _no_data(
            slo, f"No dbt model named {slo.table_name!r} for coverage evaluation."
        )

    is_met = match.coverage_pct >= slo.threshold
    message = f"Coverage {match.coverage_pct:.1f}% (SLO: >= {slo.threshold:g}%)"
    return _evaluated(slo, match.coverage_pct, is_met, message)
