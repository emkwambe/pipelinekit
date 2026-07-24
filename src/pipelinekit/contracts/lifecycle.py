"""DC-11 — contract lifecycle management (SPEC-036, ADR-037).

Adds formal lifecycle states to data contracts: ``DRAFT → ACTIVE → DEPRECATED →
RETIRED``, with emergency exits to ``RETIRED``. State is stored per
blueprint/contract in ``state.db`` (``dc_contract_lifecycle``). This provides SOC
2 evidence of controlled contract evolution and lets teams deprecate a contract
before removing it. Deterministic — no AI.

Transitions only move forward (or straight to ``RETIRED``); an invalid transition
raises ``ContractError(PK-DC-013)``. A contract with no recorded state is
implicitly ``DRAFT``.

See: SPEC-036, ADR-037.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from pipelinekit.core.errors import ContractError
from pipelinekit.state import db

DRAFT = "DRAFT"
ACTIVE = "ACTIVE"
DEPRECATED = "DEPRECATED"
RETIRED = "RETIRED"

VALID_STATES = {DRAFT, ACTIVE, DEPRECATED, RETIRED}

# Allowed forward transitions. RETIRED is terminal. There is no going backwards.
_TRANSITIONS: dict[str, set[str]] = {
    DRAFT: {ACTIVE, RETIRED},
    ACTIVE: {DEPRECATED, RETIRED},
    DEPRECATED: {RETIRED},
    RETIRED: set(),
}


@dataclass
class ContractLifecycleState:
    """The lifecycle state of a single contract."""

    id: str
    blueprint_name: str
    contract_file: str
    state: str  # DRAFT | ACTIVE | DEPRECATED | RETIRED
    changed_by: str | None
    change_reason: str | None
    created_at: str
    updated_at: str


def _utc_now() -> str:
    """Return the current time as a timezone-aware ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _row_to_state(row: dict) -> ContractLifecycleState:
    """Rebuild a ``ContractLifecycleState`` from a stored row."""
    return ContractLifecycleState(
        id=row["id"],
        blueprint_name=row["blueprint_name"],
        contract_file=row["contract_file"],
        state=row["state"],
        changed_by=row["changed_by"],
        change_reason=row["change_reason"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def set_lifecycle_state(
    blueprint_name: str,
    contract_file: str,
    new_state: str,
    changed_by: str | None,
    reason: str | None,
    db_path: str,
) -> ContractLifecycleState:
    """Transition a contract to ``new_state`` after validating the transition.

    A contract with no recorded state is treated as ``DRAFT``. Preserves ``id``
    and ``created_at`` when updating.

    Raises:
        ContractError: ``PK-DC-013`` if ``new_state`` is unknown or the
            transition from the current state is not allowed.
    """
    target = new_state.strip().upper()
    if target not in VALID_STATES:
        raise ContractError(
            "PK-DC-013",
            f"Invalid lifecycle state: {new_state!r}. "
            f"Must be one of: {', '.join(sorted(VALID_STATES))}.",
            {"state": new_state},
        )

    existing = db.get_lifecycle_state(blueprint_name, contract_file, db_path)
    current = existing["state"] if existing is not None else DRAFT
    if target not in _TRANSITIONS[current]:
        raise ContractError(
            "PK-DC-013",
            f"Invalid lifecycle transition {current} -> {target}. "
            "Allowed: DRAFT->ACTIVE, ACTIVE->DEPRECATED, DEPRECATED->RETIRED "
            "(or straight to RETIRED); no going backwards.",
            {"from": current, "to": target},
        )

    now = _utc_now()
    if existing is not None:
        state_id = existing["id"]
        created_at = existing["created_at"]
    else:
        state_id = str(uuid.uuid4())
        created_at = now

    lifecycle = ContractLifecycleState(
        id=state_id,
        blueprint_name=blueprint_name,
        contract_file=contract_file,
        state=target,
        changed_by=changed_by,
        change_reason=reason,
        created_at=created_at,
        updated_at=now,
    )
    db.upsert_lifecycle_state(lifecycle, db_path)
    return lifecycle


def get_lifecycle_state(
    blueprint_name: str, contract_file: str, db_path: str
) -> ContractLifecycleState | None:
    """Return a contract's lifecycle state, or None (implicitly DRAFT) if unset."""
    row = db.get_lifecycle_state(blueprint_name, contract_file, db_path)
    return _row_to_state(row) if row is not None else None


def get_all_lifecycle_states(db_path: str) -> list[ContractLifecycleState]:
    """Return every recorded contract lifecycle state."""
    return [_row_to_state(row) for row in db.get_all_lifecycle_states(db_path)]
