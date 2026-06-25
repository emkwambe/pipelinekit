"""Pydantic models for data contracts and their violations.

A contract is a human-readable YAML file named after the table it governs.
Every violation carries a ``PK-CONTRACT-*`` code and a structured ``evidence``
dict that feeds Phase 4 AI diagnostics.

Note: SPEC-004 sketches an ``AcceptedValuesRule(__root__=...)`` model, but
``__root__`` is Pydantic v1 syntax removed in v2. ``ContractDefinition`` already
carries ``accepted_values`` as a plain ``dict[str, list[str]]`` (which is what
the validator uses), so that v1-only helper is intentionally omitted.

See: SPEC-004.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class FreshnessRule(BaseModel):
    """Maximum acceptable age of the newest row in a table."""

    max_age_hours: int
    column: str


class RowCountRule(BaseModel):
    """Acceptable bounds on the number of rows in a table."""

    min: Optional[int] = None
    max: Optional[int] = None


class ContractDefinition(BaseModel):
    """A full data contract for a single table."""

    version: int = 1
    table: str
    description: str = ""
    freshness: Optional[FreshnessRule] = None
    required_columns: list[str] = []
    uniqueness: list[str] = []
    not_null: list[str] = []
    accepted_values: dict[str, list[str]] = {}
    row_count: Optional[RowCountRule] = None


class ViolationType(str, Enum):
    """Category of a contract violation."""

    FRESHNESS = "freshness"
    MISSING_COLUMN = "missing_column"
    UNIQUENESS = "uniqueness"
    NOT_NULL = "not_null"
    ACCEPTED_VALUES = "accepted_values"
    ROW_COUNT = "row_count"


class ContractViolation(BaseModel):
    """A single contract violation with a PK code and structured evidence."""

    table: str
    violation_type: ViolationType
    column: Optional[str] = None
    error_code: str
    message: str
    evidence: dict = {}


class ContractResult(BaseModel):
    """The validation result for one table against its contract."""

    table: str
    status: str
    violations: list[ContractViolation] = []
    checked_at: str

    def passed(self) -> bool:
        """Return True when the table satisfied every contract rule."""
        return self.status == "passed"
