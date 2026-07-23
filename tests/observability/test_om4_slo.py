"""Tests for OM-4 SLO definition and evaluation (SPEC-025).

Deterministic, no AI. Every test uses a ``tmp_path`` SQLite database — the real
``blueprints/`` directory and project ``state.db`` are never touched. Freshness
data is inserted through the DC-8 db layer so no raw SQL is needed.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pipelinekit.contracts.versioning import ContractVersion
from pipelinekit.core.errors import ObservabilityError
from pipelinekit.observability.slo import (
    SLODefinition,
    check_slos,
    get_slos,
    remove_slo,
    set_slo,
)
from pipelinekit.quality.anomaly import record_row_counts
from pipelinekit.state import db


def _db(tmp_path: Path) -> str:
    """Return a path to an isolated state database for this test."""
    return str(tmp_path / "state.db")


def _insert_contract_snapshot(db_path: str, hours_ago: float) -> None:
    """Insert a DC-8 contract snapshot created ``hours_ago`` hours in the past."""
    created_at = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
    version = ContractVersion(
        id="test-version-id",
        blueprint_name="test-bp",
        contract_file="charges.yaml",
        version="1.0.0",
        version_major=1,
        version_minor=0,
        version_patch=0,
        content_hash="abc123",
        contract_content={},
        created_at=created_at,
        created_by="test",
    )
    db.insert_contract_version(version, db_path)


def test_om4_set_slo_creates_definition(tmp_path: Path) -> None:
    """set_slo creates SLODefinition with correct fields."""
    db_path = _db(tmp_path)

    slo = set_slo("test-bp", "charges", "freshness", 6.0, "hours", db_path)

    assert isinstance(slo, SLODefinition)
    assert slo.blueprint_name == "test-bp"
    assert slo.table_name == "charges"
    assert slo.slo_type == "freshness"
    assert slo.threshold == 6.0
    assert slo.unit == "hours"
    assert slo.id
    assert slo.created_at
    assert slo.updated_at


def test_om4_set_slo_updates_existing_via_upsert(tmp_path: Path) -> None:
    """Setting the same blueprint/table/type again updates the threshold."""
    db_path = _db(tmp_path)
    first = set_slo("test-bp", "charges", "row_count", 1000.0, "rows", db_path)
    second = set_slo("test-bp", "charges", "row_count", 5000.0, "rows", db_path)

    slos = get_slos("test-bp", db_path)
    assert len(slos) == 1  # upsert — not a duplicate
    assert slos[0].threshold == 5000.0
    assert second.id == first.id  # id preserved across update
    assert second.created_at == first.created_at  # created_at preserved


def test_om4_get_slos_returns_all_for_blueprint(tmp_path: Path) -> None:
    """get_slos returns only SLOs for the specified blueprint."""
    db_path = _db(tmp_path)
    set_slo("bp-one", "charges", "freshness", 6.0, "hours", db_path)
    set_slo("bp-one", "charges", "row_count", 1000.0, "rows", db_path)
    set_slo("bp-two", "orders", "coverage", 80.0, "percent", db_path)

    one = get_slos("bp-one", db_path)
    two = get_slos("bp-two", db_path)

    assert len(one) == 2
    assert {s.slo_type for s in one} == {"freshness", "row_count"}
    assert len(two) == 1
    assert two[0].blueprint_name == "bp-two"


def test_om4_remove_slo_returns_true_when_found(tmp_path: Path) -> None:
    """remove_slo returns True when the SLO exists and removes it."""
    db_path = _db(tmp_path)
    set_slo("test-bp", "charges", "freshness", 6.0, "hours", db_path)

    removed = remove_slo("test-bp", "charges", "freshness", db_path)

    assert removed is True
    assert get_slos("test-bp", db_path) == []
    # Removing again returns False (nothing left to delete).
    assert remove_slo("test-bp", "charges", "freshness", db_path) is False


def test_om4_check_slos_freshness_met(tmp_path: Path) -> None:
    """freshness SLO is OK when the contract snapshot is recent."""
    db_path = _db(tmp_path)
    _insert_contract_snapshot(db_path, hours_ago=2)
    set_slo("test-bp", "charges", "freshness", 6.0, "hours", db_path)

    results = check_slos("test-bp", db_path)

    assert len(results) == 1
    assert results[0].status == "OK"
    assert results[0].is_met is True
    assert results[0].current_value is not None
    assert results[0].current_value < 6.0


def test_om4_check_slos_freshness_violated(tmp_path: Path) -> None:
    """freshness SLO is VIOLATED when the contract snapshot is stale."""
    db_path = _db(tmp_path)
    _insert_contract_snapshot(db_path, hours_ago=8)
    set_slo("test-bp", "charges", "freshness", 6.0, "hours", db_path)

    results = check_slos("test-bp", db_path)

    assert results[0].status == "VIOLATED"
    assert results[0].is_met is False
    assert results[0].current_value is not None
    assert results[0].current_value >= 6.0


def test_om4_check_slos_row_count_met(tmp_path: Path) -> None:
    """row_count SLO is OK when the latest count exceeds the threshold."""
    db_path = _db(tmp_path)
    record_row_counts("test-bp", {"charges": 45000}, db_path)
    set_slo("test-bp", "charges", "row_count", 1000.0, "rows", db_path)

    results = check_slos("test-bp", db_path)

    assert results[0].status == "OK"
    assert results[0].is_met is True
    assert results[0].current_value == 45000.0


def test_om4_check_slos_row_count_violated(tmp_path: Path) -> None:
    """row_count SLO is VIOLATED when the latest count is below the threshold."""
    db_path = _db(tmp_path)
    record_row_counts("test-bp", {"charges": 500}, db_path)
    set_slo("test-bp", "charges", "row_count", 1000.0, "rows", db_path)

    results = check_slos("test-bp", db_path)

    assert results[0].status == "VIOLATED"
    assert results[0].is_met is False
    assert results[0].current_value == 500.0


def test_om4_check_slos_returns_no_data_when_no_snapshot(tmp_path: Path) -> None:
    """SLO check returns NO_DATA when no state.db records exist yet."""
    db_path = _db(tmp_path)
    set_slo("test-bp", "charges", "freshness", 6.0, "hours", db_path)

    results = check_slos("test-bp", db_path)

    assert results[0].status == "NO_DATA"
    assert results[0].current_value is None
    assert results[0].is_met is False


def test_om4_raises_pk_om_002_for_invalid_slo_type(tmp_path: Path) -> None:
    """ObservabilityError with PK-OM-002 is raised for an unknown slo_type."""
    db_path = _db(tmp_path)

    with pytest.raises(ObservabilityError) as exc_info:
        set_slo("test-bp", "charges", "latency", 100.0, "ms", db_path)

    assert exc_info.value.code == "PK-OM-002"
