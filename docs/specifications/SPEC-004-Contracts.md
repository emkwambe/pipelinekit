# SPEC-004-Contracts.md

**Status:** Approved  
**Owner:** runtime-engineer  
**Phase:** 2 — Data Layer  
**Date:** June 25, 2026  
**ADRs:** ADR-008 (Deterministic), ADR-009 (Human-Readable), ADR-010 (Explainability Before Automation), ADR-011 (Trust as primary metric)  
**Contracts:** contracts/pipeline.yaml  
**Schemas:** schemas/blueprint.schema.json  
**Principle:** Principle 4 — Contracts Define Truth

---

## Purpose

Define the data contract system — the mechanism by which PipelineKit enforces expectations about data structure, freshness, quality, and business rules.

Contracts are first-class artifacts.
Contracts define truth.
AI never defines truth.
A pipeline without contracts is a pipeline without trust.

---

## Governing Rules

- Contracts are YAML files — human-readable, version-controllable
- Contracts live in the directory specified by `pipelinekit.yaml` → `contracts.directory`
- Contract validation is deterministic — no AI involvement
- Contract violations are structured errors with PK error codes
- Contracts are checked after ingestion, before transformation output is trusted
- A contract violation does not automatically stop the pipeline — it flags and reports
- AI may read contract violations as evidence — AI never modifies contracts

---

## Contract File Format

Each contract is a YAML file named after the table it governs.

```yaml
# contracts/orders.yaml

version: 1
table: orders
description: "Order transaction records from operational database"

freshness:
  max_age_hours: 12
  column: updated_at

required_columns:
  - order_id
  - customer_id
  - amount
  - status
  - created_at

uniqueness:
  - order_id

not_null:
  - order_id
  - customer_id
  - amount

accepted_values:
  status:
    - pending
    - confirmed
    - shipped
    - delivered
    - cancelled

row_count:
  min: 1
```

---

## Contract Pydantic Model

```python
# src/pipelinekit/contracts/models.py

from pydantic import BaseModel
from typing import Optional

class FreshnessRule(BaseModel):
    max_age_hours: int
    column: str

class RowCountRule(BaseModel):
    min: Optional[int] = None
    max: Optional[int] = None

class AcceptedValuesRule(BaseModel):
    # key = column name, value = list of accepted values
    __root__: dict[str, list[str]]

class ContractDefinition(BaseModel):
    version: int = 1
    table: str
    description: str = ""
    freshness: Optional[FreshnessRule] = None
    required_columns: list[str] = []
    uniqueness: list[str] = []
    not_null: list[str] = []
    accepted_values: dict[str, list[str]] = {}
    row_count: Optional[RowCountRule] = None
```

---

## Contract Violation Model

```python
# src/pipelinekit/contracts/models.py (continued)

from enum import Enum

class ViolationType(str, Enum):
    FRESHNESS         = "freshness"
    MISSING_COLUMN    = "missing_column"
    UNIQUENESS        = "uniqueness"
    NOT_NULL          = "not_null"
    ACCEPTED_VALUES   = "accepted_values"
    ROW_COUNT         = "row_count"

class ContractViolation(BaseModel):
    table: str
    violation_type: ViolationType
    column: Optional[str] = None
    error_code: str                  # PK-CONTRACT-001 etc
    message: str
    evidence: dict = {}              # structured detail for AI diagnosis

class ContractResult(BaseModel):
    table: str
    status: str                      # "passed" | "violated"
    violations: list[ContractViolation] = []
    checked_at: str                  # ISO 8601 UTC

    def passed(self) -> bool:
        return self.status == "passed"
```

---

## ContractValidator Interface

```python
# src/pipelinekit/contracts/validator.py

from pathlib import Path
from pipelinekit.contracts.models import ContractDefinition, ContractResult

class ContractValidator:
    """Validates data against contract definitions.

    Contracts define truth. This validator enforces that truth
    against actual data. Violations are structured evidence —
    they feed Phase 4 AI diagnostics.

    Contract: contracts/pipeline.yaml (Principle 4)
    """

    def __init__(self, contracts_dir: Path):
        self.contracts_dir = contracts_dir

    def load_contract(self, table: str) -> ContractDefinition:
        """Load contract YAML for a given table name."""
        ...

    def load_all_contracts(self) -> list[ContractDefinition]:
        """Load all .yaml files from contracts_dir."""
        ...

    def validate_table(
        self,
        contract: ContractDefinition,
        connection  # database connection — Phase 2 uses sqlalchemy or dlt's connection
    ) -> ContractResult:
        """
        Validate a single table against its contract.
        Returns ContractResult with all violations found.
        Never raises — always returns a result.
        """
        ...

    def validate_all(self, connection) -> list[ContractResult]:
        """
        Validate all tables that have contracts.
        Returns list of ContractResult, one per table.
        """
        ...
```

---

## pipelinekit validate — Contract Extension

`pipelinekit validate` in Phase 1 validates config only.
In Phase 2, it gains a `--contracts` flag:

```python
# src/pipelinekit/cli/validate.py (extended)

def validate_command(
    contracts: bool = typer.Option(False, "--contracts", help="Also validate data contracts.")
):
    """Validate pipelinekit.yaml and optionally data contracts."""
```

**Output with `--contracts` and violations:**
```
✓ pipelinekit.yaml is valid

⚠ Contract violations found:

  Table: orders
  ─────────────────────────────────────────────────────
  [PK-CONTRACT-002] Freshness violation: data is 18h old (max: 12h)
  [PK-CONTRACT-001] Required column missing: customer_id

  Table: customers
  ─────────────────────────────────────────────────────
  ✓ All checks passed
```

---

## Error Codes — Contracts

| Code | Meaning |
|---|---|
| `PK-CONTRACT-001` | Required column missing from table |
| `PK-CONTRACT-002` | Freshness SLA violated |
| `PK-CONTRACT-003` | Uniqueness constraint violated |
| `PK-CONTRACT-004` | Not-null constraint violated |
| `PK-CONTRACT-005` | Accepted values constraint violated |
| `PK-CONTRACT-006` | Row count outside expected range |
| `PK-CONTRACT-007` | Contract file not found for table |
| `PK-CONTRACT-008` | Contract file is invalid YAML |

---

## File Structure

```
src/pipelinekit/
└── contracts/
    ├── __init__.py
    ├── models.py       ContractDefinition, ContractViolation,
    │                   ContractResult, ViolationType
    └── validator.py    ContractValidator
```

---

## Contract Storage in State

Contract results are persisted to state for AI diagnostics in Phase 4:

```sql
CREATE TABLE IF NOT EXISTS contract_results (
    id              TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL,
    table_name      TEXT NOT NULL,
    status          TEXT NOT NULL,     -- passed | violated
    violation_count INTEGER DEFAULT 0,
    violations      TEXT,              -- JSON array of ContractViolation
    checked_at      TEXT NOT NULL      -- ISO 8601 UTC
);
```

---

## Test Strategy

Contract tests must not require real database connections.
Use in-memory data structures to simulate table results.

```python
# tests/contracts/test_validator.py

def test_freshness_violation_detected(sample_contract, stale_table_data):
    """Freshness violation is caught when data exceeds max_age_hours."""
    ...

def test_missing_column_detected(sample_contract, table_missing_column):
    """Missing required column produces PK-CONTRACT-001 violation."""
    ...

def test_all_checks_pass(sample_contract, valid_table_data):
    """ContractResult.passed() is True when all rules satisfied."""
    ...

def test_violation_has_evidence(sample_contract, violating_table_data):
    """Each ContractViolation carries structured evidence dict."""
    ...
```

---

## AI Guardrails

- Contract validation is purely deterministic — no AI
- `ContractViolation.evidence` is structured for AI consumption in Phase 4
- AI may recommend contract updates — human approves publication
- AI may never modify contract files directly
- `pipelinekit contract generate` is a Phase 4 AI command (AI suggests, human approves)

---

## Constraints

- Contract files are YAML only — no JSON, no Python
- Contract validation does not block pipeline execution — it flags violations
- Contract violations are always recorded in state
- `ContractValidator` never makes network calls
- `ContractValidator` is stateless — connection passed per call
- All violation messages must be human-readable without AI

---

## Acceptance Criteria

```
✓ ContractDefinition loads valid contract YAML
✓ ContractDefinition raises on invalid YAML
✓ ContractValidator detects freshness violation
✓ ContractValidator detects missing required column
✓ ContractValidator detects uniqueness violation
✓ ContractValidator detects not-null violation
✓ ContractResult.passed() returns True when no violations
✓ ContractResult.passed() returns False when violations exist
✓ All violations carry PK error codes
✓ All violations carry structured evidence dict
✓ poetry run pytest tests/contracts/ → all tests pass
✓ coverage >= 90% on src/pipelinekit/contracts/
```

---

## Out of Scope

- `pipelinekit contract generate` (AI-assisted) — Phase 4
- Contract inheritance or composition — Phase 3
- Cross-table contract rules — Phase 3
- Contract versioning and migration — Phase 3
- Real-time contract monitoring — Phase 3 (observability layer)
