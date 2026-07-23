"""Tests for DC-10 consumer notification (SPEC-027).

Deterministic, no AI, no email. Every test uses a ``tmp_path`` SQLite database —
the real ``blueprints/`` directory and project ``state.db`` are never touched.
"""

from __future__ import annotations

from pathlib import Path

from pipelinekit.contracts.notification import (
    ContractConsumer,
    create_notifications,
    get_consumers,
    get_pending_notifications,
    mark_all_read,
    register_consumer,
    remove_consumer,
)


def _db(tmp_path: Path) -> str:
    """Return a path to an isolated state database for this test."""
    return str(tmp_path / "state.db")


def test_dc10_register_consumer_creates_record(tmp_path: Path) -> None:
    """register_consumer creates ContractConsumer with correct fields."""
    db_path = _db(tmp_path)

    consumer = register_consumer(
        "stripe-to-snowflake", "charges", "analyst@company.com", db_path
    )

    assert isinstance(consumer, ContractConsumer)
    assert consumer.blueprint_name == "stripe-to-snowflake"
    assert consumer.table_name == "charges"
    assert consumer.consumer_email == "analyst@company.com"
    assert consumer.id
    assert consumer.created_at


def test_dc10_register_consumer_is_idempotent(tmp_path: Path) -> None:
    """Re-registering the same email/table combination does not duplicate."""
    db_path = _db(tmp_path)
    first = register_consumer("bp", "charges", "a@company.com", db_path)
    second = register_consumer("bp", "charges", "a@company.com", db_path)

    consumers = get_consumers("bp", db_path)
    assert len(consumers) == 1
    assert first.id == second.id


def test_dc10_get_consumers_returns_for_blueprint(tmp_path: Path) -> None:
    """get_consumers returns only consumers for the specified blueprint."""
    db_path = _db(tmp_path)
    register_consumer("bp-one", "charges", "a@company.com", db_path)
    register_consumer("bp-one", "customers", "b@company.com", db_path)
    register_consumer("bp-two", "orders", "c@company.com", db_path)

    one = get_consumers("bp-one", db_path)
    two = get_consumers("bp-two", db_path)

    assert len(one) == 2
    assert {c.consumer_email for c in one} == {"a@company.com", "b@company.com"}
    assert len(two) == 1
    assert two[0].blueprint_name == "bp-two"


def test_dc10_remove_consumer_returns_true_when_found(tmp_path: Path) -> None:
    """remove_consumer returns True when consumer exists and removes it."""
    db_path = _db(tmp_path)
    register_consumer("bp", "charges", "a@company.com", db_path)

    removed = remove_consumer("bp", "charges", "a@company.com", db_path)

    assert removed is True
    assert get_consumers("bp", db_path) == []


def test_dc10_remove_consumer_returns_false_when_not_found(tmp_path: Path) -> None:
    """remove_consumer returns False when the consumer does not exist."""
    db_path = _db(tmp_path)

    assert remove_consumer("bp", "charges", "a@company.com", db_path) is False


def test_dc10_create_notifications_for_all_watching_consumers(tmp_path: Path) -> None:
    """create_notifications creates one record per registered consumer."""
    db_path = _db(tmp_path)
    register_consumer("bp", "charges", "a@company.com", db_path)
    register_consumer("bp", "charges", "b@company.com", db_path)

    created = create_notifications(
        "bp", "charges.yaml", "charges", "1.0.0", "2.0.0", "MAJOR", db_path
    )

    assert len(created) == 2
    assert {n.consumer_email for n in created} == {"a@company.com", "b@company.com"}
    assert all(n.change_type == "MAJOR" for n in created)
    assert all(n.is_read is False for n in created)
    assert len(get_pending_notifications(db_path)) == 2


def test_dc10_create_notifications_empty_when_no_consumers(tmp_path: Path) -> None:
    """create_notifications returns [] when no consumers are registered."""
    db_path = _db(tmp_path)

    created = create_notifications(
        "bp", "charges.yaml", "charges", "1.0.0", "2.0.0", "MAJOR", db_path
    )

    assert created == []
    assert get_pending_notifications(db_path) == []


def test_dc10_create_notifications_filters_by_table(tmp_path: Path) -> None:
    """create_notifications only notifies consumers watching the changed table."""
    db_path = _db(tmp_path)
    register_consumer("bp", "charges", "charges@company.com", db_path)
    register_consumer("bp", "customers", "customers@company.com", db_path)

    created = create_notifications(
        "bp", "charges.yaml", "charges", "1.0.0", "2.0.0", "MAJOR", db_path
    )

    assert len(created) == 1
    assert created[0].consumer_email == "charges@company.com"


def test_dc10_mark_all_read_returns_count_and_clears_pending(tmp_path: Path) -> None:
    """mark_all_read returns the correct count and marks all notifications read."""
    db_path = _db(tmp_path)
    register_consumer("bp", "charges", "a@company.com", db_path)
    register_consumer("bp", "charges", "b@company.com", db_path)
    create_notifications(
        "bp", "charges.yaml", "charges", "1.0.0", "2.0.0", "MAJOR", db_path
    )

    count = mark_all_read(db_path)

    assert count == 2
    assert get_pending_notifications(db_path) == []
