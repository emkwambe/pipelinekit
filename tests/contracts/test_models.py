"""Tests for contract models (SPEC-004)."""

from __future__ import annotations

import yaml
from pipelinekit.contracts.models import (
    ContractDefinition,
    ContractResult,
    ContractViolation,
    ViolationType,
)

_CONTRACT_YAML = """
version: 1
table: orders
description: "Order records"
freshness:
  max_age_hours: 12
  column: updated_at
required_columns:
  - order_id
  - customer_id
uniqueness:
  - order_id
not_null:
  - order_id
accepted_values:
  status:
    - pending
    - shipped
row_count:
  min: 1
"""


def test_valid_contract_yaml_loads():
    """A valid contract YAML loads into ContractDefinition."""
    data = yaml.safe_load(_CONTRACT_YAML)
    contract = ContractDefinition(**data)
    assert contract.table == "orders"
    assert contract.freshness is not None
    assert contract.freshness.max_age_hours == 12
    assert contract.required_columns == ["order_id", "customer_id"]
    assert contract.accepted_values["status"] == ["pending", "shipped"]
    assert contract.row_count is not None
    assert contract.row_count.min == 1


def test_contract_result_passed_true_without_violations():
    """ContractResult.passed() is True when there are no violations."""
    result = ContractResult(
        table="orders", status="passed", checked_at="2026-06-25T00:00:00Z"
    )
    assert result.passed() is True


def test_contract_result_passed_false_with_violations():
    """ContractResult.passed() is False when violations exist."""
    violation = ContractViolation(
        table="orders",
        violation_type=ViolationType.NOT_NULL,
        column="order_id",
        error_code="PK-CONTRACT-004",
        message="null found",
        evidence={"null_count": 3},
    )
    result = ContractResult(
        table="orders",
        status="violated",
        violations=[violation],
        checked_at="2026-06-25T00:00:00Z",
    )
    assert result.passed() is False


def test_contract_violation_carries_code_and_evidence():
    """ContractViolation carries a PK error code and a structured evidence dict."""
    violation = ContractViolation(
        table="orders",
        violation_type=ViolationType.FRESHNESS,
        column="updated_at",
        error_code="PK-CONTRACT-002",
        message="stale",
        evidence={"actual_age_hours": 18, "max_age_hours": 12},
    )
    assert violation.error_code == "PK-CONTRACT-002"
    assert isinstance(violation.evidence, dict)
    assert violation.evidence["actual_age_hours"] == 18
