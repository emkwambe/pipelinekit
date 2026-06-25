"""Tests for ContractValidator (SPEC-004). In-memory data — no real database."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pipelinekit.contracts.models import ContractDefinition
from pipelinekit.contracts.validator import ContractValidator
from pipelinekit.core.errors import ContractError

_VALID_CONTRACT_YAML = """
version: 1
table: orders
required_columns:
  - order_id
"""


class _FakeCursor:
    def __init__(self, columns: list[str], rows: list[tuple]) -> None:
        self.description = [(c,) for c in columns]
        self._rows = rows

    def execute(self, sql: str) -> None:
        self._sql = sql

    def fetchall(self) -> list[tuple]:
        return self._rows


class _FakeConnection:
    """In-memory DB-API-style connection built from dict rows."""

    def __init__(self, columns: list[str], rows: list[dict]) -> None:
        self._columns = columns
        self._rows = [tuple(r.get(c) for c in columns) for r in rows]

    def cursor(self) -> _FakeCursor:
        return _FakeCursor(self._columns, self._rows)


def _validator() -> ContractValidator:
    return ContractValidator(Path("."))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def test_freshness_violation_detected():
    """Stale data exceeding max_age_hours produces PK-CONTRACT-002."""
    contract = ContractDefinition(
        table="orders",
        freshness={"max_age_hours": 12, "column": "updated_at"},
    )
    conn = _FakeConnection(
        ["order_id", "updated_at"],
        [{"order_id": 1, "updated_at": "2020-01-01T00:00:00Z"}],
    )
    result = _validator().validate_table(contract, conn)
    assert not result.passed()
    assert any(v.error_code == "PK-CONTRACT-002" for v in result.violations)


def test_missing_required_column_detected():
    """A missing required column produces PK-CONTRACT-001."""
    contract = ContractDefinition(
        table="orders", required_columns=["order_id", "customer_id"]
    )
    conn = _FakeConnection(["order_id"], [{"order_id": 1}])
    result = _validator().validate_table(contract, conn)
    codes = [v.error_code for v in result.violations]
    assert "PK-CONTRACT-001" in codes
    assert any(v.column == "customer_id" for v in result.violations)


def test_uniqueness_violation_detected():
    """Duplicate values in a uniqueness column produce PK-CONTRACT-003."""
    contract = ContractDefinition(table="orders", uniqueness=["order_id"])
    conn = _FakeConnection(
        ["order_id"], [{"order_id": 1}, {"order_id": 1}, {"order_id": 2}]
    )
    result = _validator().validate_table(contract, conn)
    assert any(v.error_code == "PK-CONTRACT-003" for v in result.violations)


def test_not_null_violation_detected():
    """A null in a not-null column produces PK-CONTRACT-004."""
    contract = ContractDefinition(table="orders", not_null=["customer_id"])
    conn = _FakeConnection(
        ["order_id", "customer_id"],
        [{"order_id": 1, "customer_id": None}, {"order_id": 2, "customer_id": 7}],
    )
    result = _validator().validate_table(contract, conn)
    assert any(v.error_code == "PK-CONTRACT-004" for v in result.violations)
    violation = next(v for v in result.violations if v.error_code == "PK-CONTRACT-004")
    assert violation.evidence["null_count"] == 1


def test_accepted_values_violation_detected():
    """A value outside the accepted set produces PK-CONTRACT-005."""
    contract = ContractDefinition(
        table="orders", accepted_values={"status": ["pending", "shipped"]}
    )
    conn = _FakeConnection(["status"], [{"status": "pending"}, {"status": "exploded"}])
    result = _validator().validate_table(contract, conn)
    assert any(v.error_code == "PK-CONTRACT-005" for v in result.violations)


def test_row_count_violation_detected():
    """A row count below the minimum produces PK-CONTRACT-006."""
    contract = ContractDefinition(table="orders", row_count={"min": 1})
    conn = _FakeConnection(["order_id"], [])
    result = _validator().validate_table(contract, conn)
    assert any(v.error_code == "PK-CONTRACT-006" for v in result.violations)


def test_all_checks_pass():
    """ContractResult.passed() is True when every rule is satisfied."""
    contract = ContractDefinition(
        table="orders",
        freshness={"max_age_hours": 24, "column": "updated_at"},
        required_columns=["order_id", "status"],
        uniqueness=["order_id"],
        not_null=["order_id"],
        accepted_values={"status": ["pending", "shipped"]},
        row_count={"min": 1, "max": 10},
    )
    conn = _FakeConnection(
        ["order_id", "status", "updated_at"],
        [
            {"order_id": 1, "status": "pending", "updated_at": _now_iso()},
            {"order_id": 2, "status": "shipped", "updated_at": _now_iso()},
        ],
    )
    result = _validator().validate_table(contract, conn)
    assert result.passed()
    assert result.violations == []


def test_all_violations_collected_in_one_pass():
    """Validation collects every violation rather than stopping at the first."""
    contract = ContractDefinition(
        table="orders",
        required_columns=["order_id", "customer_id"],
        uniqueness=["order_id"],
        not_null=["order_id"],
    )
    conn = _FakeConnection(
        ["order_id"],
        [{"order_id": None}, {"order_id": None}],
    )
    result = _validator().validate_table(contract, conn)
    codes = {v.error_code for v in result.violations}
    # missing customer_id (001), duplicate order_id nulls excluded from uniqueness,
    # null order_id (004) — at least the missing-column and not-null violations.
    assert "PK-CONTRACT-001" in codes
    assert "PK-CONTRACT-004" in codes
    assert len(result.violations) >= 2


def test_load_contract(tmp_path):
    """load_contract parses a contract YAML file by table name."""
    (tmp_path / "orders.yaml").write_text(_VALID_CONTRACT_YAML, encoding="utf-8")
    contract = ContractValidator(tmp_path).load_contract("orders")
    assert contract.table == "orders"


def test_load_contract_not_found(tmp_path):
    """load_contract raises PK-CONTRACT-007 when the file is absent."""
    with pytest.raises(ContractError) as exc_info:
        ContractValidator(tmp_path).load_contract("missing")
    assert exc_info.value.code == "PK-CONTRACT-007"


def test_load_contract_invalid_yaml(tmp_path):
    """load_contract raises PK-CONTRACT-008 on malformed contract YAML."""
    (tmp_path / "bad.yaml").write_text("table: [unclosed\n", encoding="utf-8")
    with pytest.raises(ContractError) as exc_info:
        ContractValidator(tmp_path).load_contract("bad")
    assert exc_info.value.code == "PK-CONTRACT-008"


def test_load_all_and_validate_all(tmp_path):
    """load_all_contracts and validate_all cover the multi-contract path."""
    (tmp_path / "orders.yaml").write_text(_VALID_CONTRACT_YAML, encoding="utf-8")
    validator = ContractValidator(tmp_path)
    assert len(validator.load_all_contracts()) == 1
    conn = _FakeConnection(["order_id"], [{"order_id": 1}])
    results = validator.validate_all(conn)
    assert len(results) == 1
    assert results[0].passed()


def test_validate_table_unreadable_connection_never_raises():
    """An unreadable connection yields a violation, not an exception."""

    class _BoomConnection:
        def cursor(self):
            raise RuntimeError("database down")

    contract = ContractDefinition(table="orders")
    result = _validator().validate_table(contract, _BoomConnection())
    assert not result.passed()
    assert result.violations[0].error_code == "PK-CONTRACT-006"
