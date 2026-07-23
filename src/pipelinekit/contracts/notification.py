"""DC-10 — consumer registration and contract change notifications (SPEC-027).

Records who watches which contract table and creates notification records when a
breaking contract change is accepted (DC-9 ``snapshot --force``). This is the
audit-trail layer only — notification records live in ``state.db``
(``dc_consumers`` and ``dc_notifications``); it never sends email. Delivery via
the OM alerting system is a future integration. Purely deterministic — no AI.

An empty result from :func:`create_notifications` (no consumers watching the
changed table) is a valid, non-error outcome.

See: SPEC-027, ADR-028.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from pipelinekit.state import db


@dataclass
class ContractConsumer:
    """A downstream consumer watching one contract table of a blueprint."""

    id: str
    blueprint_name: str
    table_name: str
    consumer_email: str
    created_at: str


@dataclass
class ContractNotification:
    """A record that a consumer should be told about a contract change."""

    id: str
    blueprint_name: str
    contract_file: str
    table_name: str
    consumer_email: str
    old_version: str
    new_version: str
    change_type: str  # "MAJOR" | "MINOR" | "PATCH"
    is_read: bool
    created_at: str


def _utc_now() -> str:
    """Return the current time as a timezone-aware ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _row_to_consumer(row: dict) -> ContractConsumer:
    """Rebuild a ``ContractConsumer`` from a stored ``dc_consumers`` row."""
    return ContractConsumer(
        id=row["id"],
        blueprint_name=row["blueprint_name"],
        table_name=row["table_name"],
        consumer_email=row["consumer_email"],
        created_at=row["created_at"],
    )


def _row_to_notification(row: dict) -> ContractNotification:
    """Rebuild a ``ContractNotification`` from a ``dc_notifications`` row."""
    return ContractNotification(
        id=row["id"],
        blueprint_name=row["blueprint_name"],
        contract_file=row["contract_file"],
        table_name=row["table_name"],
        consumer_email=row["consumer_email"],
        old_version=row["old_version"],
        new_version=row["new_version"],
        change_type=row["change_type"],
        is_read=bool(row["is_read"]),
        created_at=row["created_at"],
    )


def register_consumer(
    blueprint_name: str,
    table_name: str,
    consumer_email: str,
    db_path: str,
) -> ContractConsumer:
    """Register a consumer watching a blueprint/table.

    Idempotent: re-registering the same ``(blueprint, table, email)`` triple
    returns the existing record rather than creating a duplicate.
    """
    existing = _find_consumer(blueprint_name, table_name, consumer_email, db_path)
    if existing is not None:
        return existing

    consumer = ContractConsumer(
        id=str(uuid.uuid4()),
        blueprint_name=blueprint_name,
        table_name=table_name,
        consumer_email=consumer_email,
        created_at=_utc_now(),
    )
    db.insert_consumer(consumer, db_path)
    # Read back so the returned record reflects what was actually stored.
    stored = _find_consumer(blueprint_name, table_name, consumer_email, db_path)
    return stored if stored is not None else consumer


def get_consumers(blueprint_name: str, db_path: str) -> list[ContractConsumer]:
    """Return every consumer registered for a blueprint, across all tables."""
    return [_row_to_consumer(row) for row in db.get_consumers(blueprint_name, db_path)]


def remove_consumer(
    blueprint_name: str,
    table_name: str,
    consumer_email: str,
    db_path: str,
) -> bool:
    """Remove a consumer. Return True if one existed and was removed."""
    return db.delete_consumer(blueprint_name, table_name, consumer_email, db_path)


def _find_consumer(
    blueprint_name: str, table_name: str, consumer_email: str, db_path: str
) -> ContractConsumer | None:
    """Return the consumer matching the triple, or None."""
    for row in db.get_consumers_for_table(blueprint_name, table_name, db_path):
        if row["consumer_email"] == consumer_email:
            return _row_to_consumer(row)
    return None


def create_notifications(
    blueprint_name: str,
    contract_file: str,
    table_name: str,
    old_version: str,
    new_version: str,
    change_type: str,
    db_path: str,
) -> list[ContractNotification]:
    """Create one notification per consumer watching ``blueprint_name/table_name``.

    Called by ``snapshot --force`` after a MAJOR version is written. Returns the
    created notifications, or an empty list when no consumers are registered for
    the changed table (a valid, non-error outcome).
    """
    watchers = db.get_consumers_for_table(blueprint_name, table_name, db_path)
    created: list[ContractNotification] = []
    for row in watchers:
        notification = ContractNotification(
            id=str(uuid.uuid4()),
            blueprint_name=blueprint_name,
            contract_file=contract_file,
            table_name=table_name,
            consumer_email=row["consumer_email"],
            old_version=old_version,
            new_version=new_version,
            change_type=change_type,
            is_read=False,
            created_at=_utc_now(),
        )
        db.insert_notification(notification, db_path)
        created.append(notification)
    return created


def get_pending_notifications(db_path: str) -> list[ContractNotification]:
    """Return all unread notifications."""
    return [_row_to_notification(row) for row in db.get_pending_notifications(db_path)]


def mark_all_read(db_path: str) -> int:
    """Mark all pending notifications read. Return the number updated."""
    return db.mark_notifications_read(db_path)
