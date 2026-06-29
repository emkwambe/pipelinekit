"""GM-1 — ownership assignment for installed blueprints (SPEC-023).

Assigns a named owner to each installed blueprint and stores it in ``state.db``
(``gm_owners`` table). Purely deterministic — no AI. Ownership is organizational
state, not blueprint state (ADR-024), so it lives in ``state.db`` rather than in
``blueprint.json`` or ``pipelinekit.yaml``.

See: SPEC-023, ADR-024.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from pipelinekit.core.errors import GovernanceError
from pipelinekit.state import db

BLUEPRINTS_DIR = "blueprints"


@dataclass
class BlueprintOwner:
    """The owner assigned to a single installed blueprint."""

    id: str
    blueprint_name: str
    owner_name: str
    owner_email: str
    team_name: str | None
    notes: str | None
    created_at: str
    updated_at: str


@dataclass
class OwnershipReport:
    """Ownership coverage across every installed blueprint."""

    owners: list[BlueprintOwner]
    unowned_blueprints: list[str]
    total_blueprints: int
    owned_count: int
    coverage_pct: float


def _utc_now() -> str:
    """Return the current time as a timezone-aware ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _blueprint_installed(blueprint_name: str) -> bool:
    """Return True if ``blueprints/<name>/`` exists in the current project."""
    return (Path(BLUEPRINTS_DIR) / blueprint_name).is_dir()


def _row_to_owner(row: dict) -> BlueprintOwner:
    """Rebuild a ``BlueprintOwner`` from a stored ``gm_owners`` row."""
    return BlueprintOwner(
        id=row["id"],
        blueprint_name=row["blueprint_name"],
        owner_name=row["owner_name"],
        owner_email=row["owner_email"],
        team_name=row["team_name"],
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def validate_email(email: str) -> bool:
    """Validate an owner email: exactly one ``@`` and a dot after it.

    Returns True when valid.

    Raises:
        GovernanceError: ``PK-GM-002`` if the email is invalid.
    """
    local, sep, domain = email.partition("@")
    if email.count("@") != 1 or not sep or not local or "." not in domain:
        raise GovernanceError(
            "PK-GM-002",
            f"Invalid email address: {email!r}",
            {"email": email},
        )
    return True


def set_owner(
    blueprint_name: str,
    owner_name: str,
    owner_email: str,
    team_name: str | None,
    notes: str | None,
    db_path: str,
) -> BlueprintOwner:
    """Assign or update the owner of an installed blueprint.

    Raises:
        GovernanceError: ``PK-GM-002`` if the email is invalid,
            ``PK-GM-001`` if the blueprint is not installed.
    """
    validate_email(owner_email)
    if not _blueprint_installed(blueprint_name):
        raise GovernanceError(
            "PK-GM-001",
            f"Blueprint not found: {blueprint_name}",
            {"blueprint_name": blueprint_name},
        )

    existing = db.get_owner(blueprint_name, db_path)
    now = _utc_now()
    if existing is not None:
        owner_id = existing["id"]
        created_at = existing["created_at"]
    else:
        owner_id = str(uuid.uuid4())
        created_at = now

    owner = BlueprintOwner(
        id=owner_id,
        blueprint_name=blueprint_name,
        owner_name=owner_name,
        owner_email=owner_email,
        team_name=team_name,
        notes=notes,
        created_at=created_at,
        updated_at=now,
    )
    db.upsert_owner(owner, db_path)
    return owner


def get_owner(blueprint_name: str, db_path: str) -> BlueprintOwner | None:
    """Return the owner of a blueprint, or None if no owner is set."""
    row = db.get_owner(blueprint_name, db_path)
    return _row_to_owner(row) if row is not None else None


def get_ownership_report(blueprints_dir: str, db_path: str) -> OwnershipReport:
    """Build an ownership report across every installed blueprint."""
    root = Path(blueprints_dir)
    names = (
        sorted(entry.name for entry in root.iterdir() if entry.is_dir())
        if root.is_dir()
        else []
    )

    owners: list[BlueprintOwner] = []
    unowned: list[str] = []
    for name in names:
        row = db.get_owner(name, db_path)
        if row is not None:
            owners.append(_row_to_owner(row))
        else:
            unowned.append(name)

    total = len(names)
    owned = len(owners)
    coverage_pct = (owned / total * 100) if total > 0 else 0.0
    return OwnershipReport(
        owners=owners,
        unowned_blueprints=unowned,
        total_blueprints=total,
        owned_count=owned,
        coverage_pct=coverage_pct,
    )


def remove_owner(blueprint_name: str, db_path: str) -> bool:
    """Remove a blueprint's owner. Return True if one was removed.

    Raises:
        GovernanceError: ``PK-GM-001`` if the blueprint is not installed.
    """
    if not _blueprint_installed(blueprint_name):
        raise GovernanceError(
            "PK-GM-001",
            f"Blueprint not found: {blueprint_name}",
            {"blueprint_name": blueprint_name},
        )
    return db.delete_owner(blueprint_name, db_path)
