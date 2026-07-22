"""Deterministic data-contract validation.

``ContractValidator`` enforces contract definitions against actual table data.
It is purely deterministic — no AI, no network calls of its own. Every
violation it produces is structured evidence for Phase 4 diagnostics.

``validate_table`` never raises: a bad table or rule produces a violation, not
an exception, so one failing table cannot abort ``validate_all`` (SPEC-004).

The ``connection`` argument is any DB-API-style object exposing
``cursor().execute(sql)`` / ``fetchall()`` / ``description``. Tests supply an
in-memory fake; Phase 2 callers pass a real connection.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml  # type: ignore[import-untyped]
from pydantic import ValidationError

from pipelinekit.contracts.models import (
    ContractDefinition,
    ContractResult,
    ContractViolation,
    ViolationType,
)
from pipelinekit.core.errors import ContractError


def _utc_now() -> str:
    """Return the current time as an ISO 8601 UTC string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _to_datetime(value: Any) -> Optional[datetime]:
    """Coerce a cell value to an aware UTC datetime, or None if not parseable."""
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    return None


class ContractValidator:
    """Validates data against contract definitions (Principle 4)."""

    def __init__(self, contracts_dir: Path) -> None:
        self.contracts_dir = contracts_dir

    # -- loading -------------------------------------------------------------

    def load_contract(self, table: str) -> ContractDefinition:
        """Load and parse the contract YAML for ``table``."""
        path = self.contracts_dir / f"{table}.yaml"
        if not path.is_file():
            raise ContractError(
                "PK-CONTRACT-007",
                f"Contract file not found for table '{table}'",
                {"path": str(path)},
            )
        return self._parse_contract(path)

    def load_all_contracts(self) -> list[ContractDefinition]:
        """Load every ``*.yaml`` contract from ``contracts_dir`` (empty if none)."""
        if not self.contracts_dir.is_dir():
            return []
        return [
            self._parse_contract(p) for p in sorted(self.contracts_dir.glob("*.yaml"))
        ]

    def _parse_contract(self, path: Path) -> ContractDefinition:
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ContractError(
                "PK-CONTRACT-008",
                f"Contract file is not valid YAML: {path.name}",
                {"path": str(path), "detail": str(exc)},
            ) from exc
        try:
            return ContractDefinition(**(raw or {}))
        except (ValidationError, TypeError) as exc:
            raise ContractError(
                "PK-CONTRACT-008",
                f"Contract file is invalid: {path.name}",
                {"path": str(path), "detail": str(exc)},
            ) from exc

    # -- validation ----------------------------------------------------------

    def validate_table(
        self, contract: ContractDefinition, connection: Any
    ) -> ContractResult:
        """Validate one table against its contract. Never raises."""
        try:
            columns, rows = self._fetch(connection, contract.table)
            return self._evaluate(contract, columns, rows)
        except Exception as exc:
            # Defensive: an unreadable table is reported, never raised.
            violation = ContractViolation(
                table=contract.table,
                violation_type=ViolationType.ROW_COUNT,
                error_code="PK-CONTRACT-006",
                message=f"Could not read table '{contract.table}': {exc}",
                evidence={"error": str(exc)},
            )
            return ContractResult(
                table=contract.table,
                status="violated",
                violations=[violation],
                checked_at=_utc_now(),
            )

    def validate_all(self, connection: Any) -> list[ContractResult]:
        """Validate every table that has a contract."""
        return [
            self.validate_table(contract, connection)
            for contract in self.load_all_contracts()
        ]

    _TABLE_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_.]*$")

    def _fetch(self, connection: Any, table: str) -> tuple[list[str], list[dict]]:
        """Read a table's columns and rows via a DB-API-style connection."""
        if not self._TABLE_NAME_RE.match(table):
            raise ContractError(
                "PK-CONTRACT-001",
                f"Invalid table name for contract validation: '{table}'",
                {"table": table},
            )
        cursor = connection.cursor()
        cursor.execute(f'SELECT * FROM "{table}"')
        description = cursor.description or []
        columns = [col[0] for col in description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return columns, rows

    def _evaluate(
        self, contract: ContractDefinition, columns: list[str], rows: list[dict]
    ) -> ContractResult:
        """Run all contract rules in a single pass, collecting every violation."""
        table = contract.table
        colset = set(columns)
        violations: list[ContractViolation] = []

        self._check_required_columns(contract, colset, violations)
        self._check_freshness(contract, colset, rows, violations)
        self._check_uniqueness(contract, colset, rows, violations)
        self._check_not_null(contract, colset, rows, violations)
        self._check_accepted_values(contract, colset, rows, violations)
        self._check_row_count(contract, rows, violations)

        status = "passed" if not violations else "violated"
        return ContractResult(
            table=table,
            status=status,
            violations=violations,
            checked_at=_utc_now(),
        )

    # -- individual checks ---------------------------------------------------

    def _check_required_columns(
        self,
        contract: ContractDefinition,
        colset: set[str],
        violations: list[ContractViolation],
    ) -> None:
        for col in contract.required_columns:
            if col not in colset:
                violations.append(
                    ContractViolation(
                        table=contract.table,
                        violation_type=ViolationType.MISSING_COLUMN,
                        column=col,
                        error_code="PK-CONTRACT-001",
                        message=f"Required column missing: {col}",
                        evidence={
                            "missing_column": col,
                            "available_columns": sorted(colset),
                        },
                    )
                )

    def _check_freshness(
        self,
        contract: ContractDefinition,
        colset: set[str],
        rows: list[dict],
        violations: list[ContractViolation],
    ) -> None:
        rule = contract.freshness
        if rule is None or rule.column not in colset:
            return
        timestamps = [
            ts
            for ts in (_to_datetime(r.get(rule.column)) for r in rows)
            if ts is not None
        ]
        if not timestamps:
            return
        latest = max(timestamps)
        age_hours = (datetime.now(timezone.utc) - latest).total_seconds() / 3600.0
        if age_hours > rule.max_age_hours:
            violations.append(
                ContractViolation(
                    table=contract.table,
                    violation_type=ViolationType.FRESHNESS,
                    column=rule.column,
                    error_code="PK-CONTRACT-002",
                    message=(
                        f"Freshness violation: data is {age_hours:.1f}h old "
                        f"(max: {rule.max_age_hours}h)"
                    ),
                    evidence={
                        "column": rule.column,
                        "max_age_hours": rule.max_age_hours,
                        "actual_age_hours": round(age_hours, 2),
                        "latest_value": latest.isoformat(),
                    },
                )
            )

    def _check_uniqueness(
        self,
        contract: ContractDefinition,
        colset: set[str],
        rows: list[dict],
        violations: list[ContractViolation],
    ) -> None:
        for col in contract.uniqueness:
            if col not in colset:
                continue
            counts = Counter(r.get(col) for r in rows if r.get(col) is not None)
            dupes = sorted(str(v) for v, n in counts.items() if n > 1)
            if dupes:
                violations.append(
                    ContractViolation(
                        table=contract.table,
                        violation_type=ViolationType.UNIQUENESS,
                        column=col,
                        error_code="PK-CONTRACT-003",
                        message=f"Uniqueness violation on column: {col}",
                        evidence={
                            "column": col,
                            "duplicate_values": dupes,
                            "duplicate_count": len(dupes),
                        },
                    )
                )

    def _check_not_null(
        self,
        contract: ContractDefinition,
        colset: set[str],
        rows: list[dict],
        violations: list[ContractViolation],
    ) -> None:
        for col in contract.not_null:
            if col not in colset:
                continue
            null_count = sum(1 for r in rows if r.get(col) is None)
            if null_count > 0:
                violations.append(
                    ContractViolation(
                        table=contract.table,
                        violation_type=ViolationType.NOT_NULL,
                        column=col,
                        error_code="PK-CONTRACT-004",
                        message=f"Not-null violation: {null_count} null(s) in {col}",
                        evidence={"column": col, "null_count": null_count},
                    )
                )

    def _check_accepted_values(
        self,
        contract: ContractDefinition,
        colset: set[str],
        rows: list[dict],
        violations: list[ContractViolation],
    ) -> None:
        for col, allowed in contract.accepted_values.items():
            if col not in colset:
                continue
            allowed_set = set(allowed)
            unexpected = sorted(
                {
                    str(r.get(col))
                    for r in rows
                    if r.get(col) is not None and r.get(col) not in allowed_set
                }
            )
            if unexpected:
                violations.append(
                    ContractViolation(
                        table=contract.table,
                        violation_type=ViolationType.ACCEPTED_VALUES,
                        column=col,
                        error_code="PK-CONTRACT-005",
                        message=f"Unexpected values in column: {col}",
                        evidence={
                            "column": col,
                            "unexpected_values": unexpected,
                            "accepted_values": list(allowed),
                        },
                    )
                )

    def _check_row_count(
        self,
        contract: ContractDefinition,
        rows: list[dict],
        violations: list[ContractViolation],
    ) -> None:
        rule = contract.row_count
        if rule is None:
            return
        n = len(rows)
        below = rule.min is not None and n < rule.min
        above = rule.max is not None and n > rule.max
        if below or above:
            violations.append(
                ContractViolation(
                    table=contract.table,
                    violation_type=ViolationType.ROW_COUNT,
                    error_code="PK-CONTRACT-006",
                    message=f"Row count {n} outside expected range",
                    evidence={"row_count": n, "min": rule.min, "max": rule.max},
                )
            )
