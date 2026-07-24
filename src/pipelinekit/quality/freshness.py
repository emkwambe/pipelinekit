"""QM-5 — freshness SLA enforcement for pipeline tables (SPEC-034, ADR-035).

Stores a per-blueprint/table freshness requirement (``max_hours``) in
``state.db`` and checks it against the newest contract snapshot timestamp in
``dc_contract_versions`` (DC-8). Unlike OM-4 freshness SLOs (organizational
targets), QM-5 freshness checks are quality gates suitable for CI.

Read-only checks, deterministic — no AI, no warehouse. A table with no contract
snapshot yields ``NO_DATA`` (never an error).

See: SPEC-034, ADR-035.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from pipelinekit.state import db


@dataclass
class FreshnessRequirement:
    """A per-blueprint/table maximum data age, in hours."""

    id: str
    blueprint_name: str
    table_name: str
    max_hours: float
    created_at: str
    updated_at: str


@dataclass
class FreshnessCheckResult:
    """The outcome of checking one table against its freshness requirement."""

    blueprint_name: str
    table_name: str
    last_updated: str | None  # ISO timestamp from dc_contract_versions
    hours_since_update: float | None
    max_hours: float
    is_fresh: bool
    status: str  # "FRESH" | "STALE" | "NO_DATA"


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


def _row_to_requirement(row: dict) -> FreshnessRequirement:
    """Rebuild a ``FreshnessRequirement`` from a stored row."""
    return FreshnessRequirement(
        id=row["id"],
        blueprint_name=row["blueprint_name"],
        table_name=row["table_name"],
        max_hours=row["max_hours"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def set_freshness_requirement(
    blueprint_name: str,
    table_name: str,
    max_hours: float,
    db_path: str,
) -> FreshnessRequirement:
    """Set or update the freshness requirement for a blueprint/table.

    Preserves ``id`` and ``created_at`` when updating an existing requirement.
    """
    existing = db.get_freshness_req(blueprint_name, table_name, db_path)
    now = _utc_now()
    if existing is not None:
        req_id = existing["id"]
        created_at = existing["created_at"]
    else:
        req_id = str(uuid.uuid4())
        created_at = now

    requirement = FreshnessRequirement(
        id=req_id,
        blueprint_name=blueprint_name,
        table_name=table_name,
        max_hours=max_hours,
        created_at=created_at,
        updated_at=now,
    )
    db.upsert_freshness_req(requirement, db_path)
    return requirement


def get_freshness_requirements(
    blueprint_name: str, db_path: str
) -> list[FreshnessRequirement]:
    """Return every freshness requirement for a blueprint."""
    return [
        _row_to_requirement(row)
        for row in db.get_all_freshness_reqs(db_path)
        if row["blueprint_name"] == blueprint_name
    ]


def remove_freshness_requirement(
    blueprint_name: str, table_name: str, db_path: str
) -> bool:
    """Remove a freshness requirement. True if one existed and was removed."""
    return db.delete_freshness_req(blueprint_name, table_name, db_path)


def _latest_contract_time(
    blueprint_name: str, table_name: str, db_path: str
) -> str | None:
    """Return the newest contract ``created_at`` for a blueprint/table, or None.

    Matches a contract file to the table by filename (``charges.yaml`` → the
    ``charges`` table): exact stem match first, else a substring match (LIKE
    ``%table%``). Uses the DC-8 latest-per-contract reader.
    """
    latest: str | None = None
    for row in db.get_latest_contracts_for_blueprint(blueprint_name, db_path):
        contract_file = row["contract_file"]
        if Path(contract_file).stem == table_name or table_name in contract_file:
            created_at = row["created_at"]
            if latest is None or created_at > latest:
                latest = created_at
    return latest


def check_freshness(blueprint_name: str, db_path: str) -> list[FreshnessCheckResult]:
    """Check every freshness requirement for a blueprint against contract data.

    For each requirement, finds the newest matching contract snapshot: no
    snapshot → ``NO_DATA``; otherwise ``FRESH`` if the data is within
    ``max_hours``, else ``STALE``. Read-only; never raises on a violation.
    """
    results: list[FreshnessCheckResult] = []
    for requirement in get_freshness_requirements(blueprint_name, db_path):
        last_updated = _latest_contract_time(
            blueprint_name, requirement.table_name, db_path
        )
        if last_updated is None:
            results.append(
                FreshnessCheckResult(
                    blueprint_name=blueprint_name,
                    table_name=requirement.table_name,
                    last_updated=None,
                    hours_since_update=None,
                    max_hours=requirement.max_hours,
                    is_fresh=False,
                    status="NO_DATA",
                )
            )
            continue

        updated_at = _parse_iso(last_updated)
        hours_since = (datetime.now(timezone.utc) - updated_at).total_seconds() / 3600
        is_fresh = hours_since <= requirement.max_hours
        results.append(
            FreshnessCheckResult(
                blueprint_name=blueprint_name,
                table_name=requirement.table_name,
                last_updated=last_updated,
                hours_since_update=hours_since,
                max_hours=requirement.max_hours,
                is_fresh=is_fresh,
                status="FRESH" if is_fresh else "STALE",
            )
        )
    return results
