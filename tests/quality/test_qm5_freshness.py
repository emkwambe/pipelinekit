"""Tests for QM-5 freshness SLA enforcement (SPEC-034).

Deterministic, no AI. Every test uses a ``tmp_path`` SQLite database — the real
``blueprints/`` directory and project ``state.db`` are never touched. Contract
snapshots are seeded through the DC-8 db layer with controlled ages.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from pipelinekit.contracts.versioning import ContractVersion
from pipelinekit.quality.freshness import (
    FreshnessRequirement,
    check_freshness,
    get_freshness_requirements,
    remove_freshness_requirement,
    set_freshness_requirement,
)
from pipelinekit.state import db


def _db(tmp_path: Path) -> str:
    """Return a path to an isolated state database for this test."""
    return str(tmp_path / "state.db")


def _seed_contract(db_path: str, blueprint: str, table: str, hours_ago: float) -> None:
    """Seed a DC-8 contract snapshot for ``table`` created ``hours_ago`` ago."""
    created_at = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
    version = ContractVersion(
        id=f"{blueprint}-{table}",
        blueprint_name=blueprint,
        contract_file=f"{table}.yaml",
        version="1.0.0",
        version_major=1,
        version_minor=0,
        version_patch=0,
        content_hash="hash",
        contract_content={"table": table},
        created_at=created_at,
        created_by="test",
    )
    db.insert_contract_version(version, db_path)


def test_qm5_set_freshness_requirement_creates_record(tmp_path: Path) -> None:
    """set_freshness_requirement creates a FreshnessRequirement."""
    db_path = _db(tmp_path)

    req = set_freshness_requirement("test-bp", "charges", 6.0, db_path)

    assert isinstance(req, FreshnessRequirement)
    assert req.blueprint_name == "test-bp"
    assert req.table_name == "charges"
    assert req.max_hours == 6.0
    assert req.id
    assert req.created_at
    assert req.updated_at


def test_qm5_set_freshness_requirement_updates_existing(tmp_path: Path) -> None:
    """Setting the same blueprint/table again updates max_hours (upsert)."""
    db_path = _db(tmp_path)
    first = set_freshness_requirement("test-bp", "charges", 6.0, db_path)
    second = set_freshness_requirement("test-bp", "charges", 12.0, db_path)

    reqs = get_freshness_requirements("test-bp", db_path)
    assert len(reqs) == 1
    assert reqs[0].max_hours == 12.0
    assert second.id == first.id  # id preserved
    assert second.created_at == first.created_at  # created_at preserved


def test_qm5_check_freshness_returns_fresh_when_recent(tmp_path: Path) -> None:
    """A table updated within the window is FRESH."""
    db_path = _db(tmp_path)
    _seed_contract(db_path, "test-bp", "charges", hours_ago=2)
    set_freshness_requirement("test-bp", "charges", 6.0, db_path)

    results = check_freshness("test-bp", db_path)

    assert len(results) == 1
    assert results[0].status == "FRESH"
    assert results[0].is_fresh is True


def test_qm5_check_freshness_returns_stale_when_old(tmp_path: Path) -> None:
    """A table older than the window is STALE."""
    db_path = _db(tmp_path)
    _seed_contract(db_path, "test-bp", "charges", hours_ago=9)
    set_freshness_requirement("test-bp", "charges", 6.0, db_path)

    results = check_freshness("test-bp", db_path)

    assert results[0].status == "STALE"
    assert results[0].is_fresh is False


def test_qm5_check_freshness_returns_no_data_when_no_snapshot(
    tmp_path: Path,
) -> None:
    """A requirement with no matching contract snapshot yields NO_DATA."""
    db_path = _db(tmp_path)
    set_freshness_requirement("test-bp", "charges", 6.0, db_path)

    results = check_freshness("test-bp", db_path)

    assert results[0].status == "NO_DATA"
    assert results[0].last_updated is None
    assert results[0].hours_since_update is None


def test_qm5_get_freshness_requirements_returns_for_blueprint(
    tmp_path: Path,
) -> None:
    """get_freshness_requirements returns only the given blueprint's rows."""
    db_path = _db(tmp_path)
    set_freshness_requirement("bp-a", "charges", 6.0, db_path)
    set_freshness_requirement("bp-b", "orders", 12.0, db_path)

    reqs = get_freshness_requirements("bp-a", db_path)

    assert len(reqs) == 1
    assert reqs[0].blueprint_name == "bp-a"
    assert reqs[0].table_name == "charges"


def test_qm5_remove_freshness_requirement_returns_true_when_found(
    tmp_path: Path,
) -> None:
    """remove_freshness_requirement returns True when the requirement exists."""
    db_path = _db(tmp_path)
    set_freshness_requirement("test-bp", "charges", 6.0, db_path)

    removed = remove_freshness_requirement("test-bp", "charges", db_path)

    assert removed is True
    assert get_freshness_requirements("test-bp", db_path) == []
    assert remove_freshness_requirement("test-bp", "charges", db_path) is False


def test_qm5_check_freshness_handles_multiple_tables(tmp_path: Path) -> None:
    """check_freshness evaluates each table's requirement independently."""
    db_path = _db(tmp_path)
    _seed_contract(db_path, "test-bp", "charges", hours_ago=2)  # fresh
    _seed_contract(db_path, "test-bp", "customers", hours_ago=9)  # stale
    set_freshness_requirement("test-bp", "charges", 6.0, db_path)
    set_freshness_requirement("test-bp", "customers", 6.0, db_path)

    results = check_freshness("test-bp", db_path)
    by_table = {r.table_name: r for r in results}

    assert len(results) == 2
    assert by_table["charges"].status == "FRESH"
    assert by_table["customers"].status == "STALE"


def test_qm5_hours_since_update_is_correct(tmp_path: Path) -> None:
    """hours_since_update reflects the age of the newest contract snapshot."""
    db_path = _db(tmp_path)
    _seed_contract(db_path, "test-bp", "charges", hours_ago=5)
    set_freshness_requirement("test-bp", "charges", 10.0, db_path)

    results = check_freshness("test-bp", db_path)

    assert results[0].hours_since_update is not None
    assert 4.8 < results[0].hours_since_update < 5.2
