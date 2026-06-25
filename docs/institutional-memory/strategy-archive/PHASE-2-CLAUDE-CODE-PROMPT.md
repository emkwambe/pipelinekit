# PipelineKit — Phase 2 Claude Code Implementation Prompt
## Data Layer Sprint: Runtime + Adapters + Contracts + pipelinekit run

---

## Your Identity

You are Claude Code operating as the **PipelineKit Runtime Engineer** and **Quality Engineer**.

Your two active agent roles are defined in:
- `agents/runtime-engineer/AGENT.md`
- `agents/runtime-engineer/SYSTEM.md`
- `agents/quality-engineer/AGENT.md`

You are not the CLI Engineer. You do not own the CLI.
You build the layers the CLI calls. You never import from `pipelinekit.cli`.

---

## Repository

```
Local path: C:\Users\HP\Documents\pipelinekit
GitHub:     https://github.com/emkwambe/pipelinekit
```

---

## Read First — In This Exact Order

Before writing a single line of code, read these files completely:

```
1.  .claude/CLAUDE.md
2.  docs/constitution/Product-Constitution.md
3.  docs/decisions/ADR-000-Foundational-Architecture-Decisions.md
4.  agents/runtime-engineer/AGENT.md
5.  agents/runtime-engineer/SYSTEM.md
6.  agents/quality-engineer/AGENT.md
7.  docs/specifications/SPEC-003-Pipeline-Runtime.md        ← Your primary spec
8.  docs/specifications/SPEC-009-Provider-Adapters.md       ← Your adapter spec
9.  docs/specifications/SPEC-004-Contracts.md               ← Your contracts spec
10. docs/specifications/SPEC-001-CLI-Framework.md           ← CLI boundary rules
11. docs/specifications/SPEC-007-State-Store.md             ← State interface you must use
12. docs/specifications/SPEC-010-Testing-and-Quality-Gates.md
13. docs/reference/Error-Codes.md
14. docs/reference/PROJECT-STATUS.md
15. contracts/adapter.yaml
16. contracts/provider.yaml
17. contracts/pipeline.yaml
18. src/pipelinekit/core/errors.py                          ← Error classes already built
19. src/pipelinekit/config/schema.py                        ← PipelineConfig you must use
20. src/pipelinekit/state/db.py                             ← State interface already built
21. src/pipelinekit/cli/main.py                             ← CLI boundary — understand it
```

Do not skip any of these.
Items 18–21 are existing Phase 1 code — understand them before building on top.

---

## Sprint Goal

Deliver a working Phase 2 data layer such that these commands execute successfully:

```powershell
cd C:\Users\HP\Documents\pipelinekit
poetry run pipelinekit run --dry-run
poetry run pipelinekit validate --contracts
poetry run pytest --cov=src/pipelinekit --cov-fail-under=80
poetry run ruff check .
poetry run black --check .
poetry run mypy src/pipelinekit
```

**Plus** — all 36 Phase 1 tests must still pass. You must not break Phase 1.

---

## Files You Are Allowed To Create

```
src/
└── pipelinekit/
    ├── runtime/
    │   ├── __init__.py
    │   ├── runner.py          PipelineRunner
    │   ├── result.py          PipelineResult, StepResult, PipelineStatus
    │   └── executor.py        Step execution logic
    ├── adapters/
    │   ├── __init__.py
    │   ├── base.py            BaseAdapter ABC
    │   ├── factory.py         AdapterFactory
    │   ├── ingestion/
    │   │   ├── __init__.py
    │   │   └── dlt/
    │   │       ├── __init__.py
    │   │       └── adapter.py     DltIngestionAdapter
    │   ├── transformation/
    │   │   ├── __init__.py
    │   │   └── dbt/
    │   │       ├── __init__.py
    │   │       └── adapter.py     DbtTransformationAdapter
    │   └── quality/
    │       ├── __init__.py
    │       └── soda/
    │           ├── __init__.py
    │           └── adapter.py     SodaQualityAdapter
    ├── contracts/
    │   ├── __init__.py
    │   ├── models.py          ContractDefinition, ContractViolation,
    │   │                      ContractResult, ViolationType
    │   └── validator.py       ContractValidator
    └── cli/
        └── run.py             pipelinekit run command (cli-engineer scope)

tests/
├── runtime/
│   ├── __init__.py
│   ├── test_runner.py
│   └── test_result.py
├── adapters/
│   ├── __init__.py
│   ├── test_factory.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   └── test_dlt_adapter.py
│   ├── transformation/
│   │   ├── __init__.py
│   │   └── test_dbt_adapter.py
│   └── quality/
│       ├── __init__.py
│       └── test_soda_adapter.py
└── contracts/
    ├── __init__.py
    ├── test_models.py
    └── test_validator.py
```

You may also modify:
```
pyproject.toml                 Add Phase 2 dependencies only
src/pipelinekit/cli/validate.py  Add --contracts flag per SPEC-004
src/pipelinekit/cli/main.py    Register run command only
src/pipelinekit/state/db.py    Add contract_results table only
docs/reference/Error-Codes.md  Add Phase 2 error codes only
```

---

## Files You Must Not Modify

```
docs/                               ← READ ONLY (except Error-Codes.md above)
docs/reference/PROJECT-STATUS.md    ← NEVER TOUCH — Command Center owns this
contracts/                          ← READ ONLY
schemas/                            ← READ ONLY
agents/                             ← READ ONLY
.claude/                            ← READ ONLY
.github/                            ← READ ONLY
.mcp/                               ← READ ONLY
prompts/                            ← READ ONLY
skills/                             ← READ ONLY
runtime/                            ← READ ONLY (scaffold only)
examples/                           ← READ ONLY
scripts/                            ← READ ONLY
README.md                           ← READ ONLY
LICENSE                             ← READ ONLY
src/pipelinekit/core/errors.py      ← READ ONLY (use as-is)
src/pipelinekit/config/             ← READ ONLY (use as-is)
src/pipelinekit/state/db.py         ← READ ONLY except contract_results table
src/pipelinekit/cli/init.py         ← READ ONLY
src/pipelinekit/cli/validate.py     ← ADD --contracts flag only, nothing else
src/pipelinekit/cli/status.py       ← READ ONLY
tests/cli/                          ← READ ONLY
tests/config/                       ← READ ONLY
tests/state/                        ← READ ONLY
```

---

## pyproject.toml — Phase 2 Additions Only

Add these dependencies. Do not change anything else in pyproject.toml.

```toml
[tool.poetry.dependencies]
dlt = {extras = ["snowflake", "bigquery", "duckdb"], version = "^1.0"}
dbt-core = "^1.8"
dbt-snowflake = "^1.8"
dbt-bigquery = "^1.8"
soda-core = "^3.0"
soda-core-postgres = "^3.0"
```

**Critical rule:** dlt, dbt, and Soda are imported ONLY inside their adapter files.
If any import of dlt, dbt, or soda appears outside `src/pipelinekit/adapters/`,
that is an architecture violation. Stop and fix it.

---

## Implementation Requirements

### 1. src/pipelinekit/runtime/result.py

Implement exactly as specified in SPEC-003:

```python
from enum import Enum
from dataclasses import dataclass, field

class PipelineStatus(str, Enum):
    SUCCESS  = "success"
    FAILED   = "failed"
    PARTIAL  = "partial"
    VALID    = "valid"
    INVALID  = "invalid"

@dataclass
class StepResult:
    step: str
    status: PipelineStatus
    duration_s: float
    rows_processed: int = 0
    error_code: str | None = None
    error_msg: str | None = None

@dataclass
class PipelineResult:
    run_id: str
    pipeline_name: str
    status: PipelineStatus
    duration_s: float
    steps: list[StepResult] = field(default_factory=list)
    error_code: str | None = None
    error_msg: str | None = None

    def succeeded(self) -> bool:
        return self.status == PipelineStatus.SUCCESS

    def failed(self) -> bool:
        return self.status == PipelineStatus.FAILED
```

---

### 2. src/pipelinekit/adapters/base.py

Implement the BaseAdapter ABC. All 4 methods from contracts/provider.yaml are required:
`initialize`, `validate`, `execute`, `status`

Every adapter must implement all 4. No partial implementations.

---

### 3. src/pipelinekit/adapters/ingestion/dlt/adapter.py

`DltIngestionAdapter` wraps dlt behind `BaseAdapter`.

Phase 2 supports:
- Source: PostgreSQL
- Destinations: Snowflake, BigQuery, DuckDB (DuckDB for local testing only)

`execute()` must:
- Run the dlt pipeline
- Return `StepResult` with rows_processed count
- Map all dlt exceptions to `PK-ADAPTER-001` or `PK-ADAPTER-002`
- Never let dlt exceptions propagate raw out of the adapter

`validate()` must:
- Test source connectivity without loading data
- Return `StepResult` with status=valid or status=invalid

All dlt imports stay inside this file. Zero dlt imports anywhere else.

---

### 4. src/pipelinekit/adapters/transformation/dbt/adapter.py

`DbtTransformationAdapter` wraps dbt Core behind `BaseAdapter`.

`execute()` must:
- Invoke dbt via `subprocess.run()` — never import dbt as a Python library
- Command: `dbt build --project-dir <path> --profiles-dir <path>`
- Parse `run_results.json` for structured pass/fail counts
- Return `StepResult` with dbt results
- Map non-zero dbt exit codes to `PK-ADAPTER-002`

`validate()` must:
- Run `dbt parse` to validate project structure without executing models
- Return `StepResult` with status=valid or status=invalid

All subprocess calls for dbt stay inside this file.

---

### 5. src/pipelinekit/adapters/quality/soda/adapter.py

`SodaQualityAdapter` wraps Soda behind `BaseAdapter`.

`execute()` must:
- Run Soda checks from `config.checks_dir`
- Return `StepResult` with pass/fail/warn counts
- Map Soda failures to `PK-ADAPTER-002`

All Soda imports stay inside this file.

---

### 6. src/pipelinekit/adapters/factory.py

`AdapterFactory` is the single point of adapter instantiation.
The runtime calls this — it never instantiates adapters directly.

```python
class AdapterFactory:
    @staticmethod
    def create_ingestion(config: PipelineConfig) -> BaseAdapter | None:
        """Return DltIngestionAdapter, or None if not configured."""

    @staticmethod
    def create_transformation(config: PipelineConfig) -> BaseAdapter | None:
        """Return DbtTransformationAdapter, or None if transformation.enabled=False."""

    @staticmethod
    def create_quality(config: PipelineConfig) -> BaseAdapter | None:
        """Return SodaQualityAdapter, or None if quality.enabled=False."""
```

---

### 7. src/pipelinekit/runtime/runner.py

`PipelineRunner` orchestrates the full execution lifecycle.

```python
class PipelineRunner:
    def __init__(self, config: PipelineConfig):
        self.config = config

    def run(self) -> PipelineResult:
        """Full pipeline execution — ingestion → transformation → quality."""

    def validate(self) -> PipelineResult:
        """Validate config and adapter connectivity without executing."""
```

Execution lifecycle (from SPEC-003):
1. `state.db.insert_run(run_id, pipeline_name)` — status=pending
2. Create adapters via `AdapterFactory`
3. Execute each enabled step — collect `StepResult` per step
4. If any step fails — mark as FAILED or PARTIAL, continue remaining steps
5. `state.db.update_run(run_id, status, duration_s, error_code)` — always
6. Return `PipelineResult`

**The run record must always be updated — never left as pending.**
Even if an exception occurs during execution, wrap in try/finally to guarantee state update.

---

### 8. src/pipelinekit/contracts/models.py

Implement exactly as specified in SPEC-004:
- `ContractDefinition` — Pydantic model for contract YAML
- `ContractViolation` — single violation with PK error code + evidence
- `ContractResult` — full result for one table
- `ViolationType` — enum of violation categories

`ContractViolation.evidence` must be a structured dict — it feeds Phase 4 AI diagnostics.
Every violation must have an error code from the PK-CONTRACT-* series.

---

### 9. src/pipelinekit/contracts/validator.py

`ContractValidator` validates data against contract definitions.

Phase 2 implements these checks:
- `required_columns` → `PK-CONTRACT-001`
- `freshness` → `PK-CONTRACT-002`
- `uniqueness` → `PK-CONTRACT-003`
- `not_null` → `PK-CONTRACT-004`
- `accepted_values` → `PK-CONTRACT-005`
- `row_count` → `PK-CONTRACT-006`

`validate_table()` must:
- Never raise — always return a `ContractResult`
- Collect all violations in one pass — not stop at first failure
- Include structured evidence in each violation

---

### 10. src/pipelinekit/state/db.py — Addition Only

Add the `contract_results` table to the existing `_SCHEMA` string:

```sql
CREATE TABLE IF NOT EXISTS contract_results (
    id              TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL,
    table_name      TEXT NOT NULL,
    status          TEXT NOT NULL,
    violation_count INTEGER DEFAULT 0,
    violations      TEXT,
    checked_at      TEXT NOT NULL
);
```

Do not change any existing function. Add one new function:

```python
def insert_contract_result(
    run_id: str,
    table_name: str,
    status: str,
    violation_count: int,
    violations_json: str,
    cwd: Path | None = None,
) -> None:
    """Store contract validation result for a table."""
```

---

### 11. src/pipelinekit/cli/run.py

```python
def run_command(
    dry_run: bool = typer.Option(False, "--dry-run",
        help="Validate adapters without executing pipeline.")
):
    """Execute the configured pipeline."""
```

Behavior:
1. Load config via `config.loader.load_config()`
2. If `--dry-run`: call `PipelineRunner.validate()`, print result, exit
3. Else: call `PipelineRunner.run()`, print Rich table summary, exit 0 or 1

The CLI never touches `PipelineRunner` internals.
The CLI never touches adapters directly.
The CLI renders `PipelineResult` — it does not produce it.

Register in `src/pipelinekit/cli/main.py`:
```python
from pipelinekit.cli.run import run_command
app.command("run")(run_command)
```

---

### 12. src/pipelinekit/cli/validate.py — --contracts flag only

Add one optional flag to the existing `validate_command`:

```python
def validate_command(
    contracts: bool = typer.Option(False, "--contracts",
        help="Also validate data contracts against live data.")
):
```

When `--contracts` is True:
1. Load config
2. Validate config (existing behavior)
3. If `contracts.enabled` is True in config: run `ContractValidator`
4. Print contract results using Rich
5. Exit 1 if any violations found

Do not change any existing validate behavior. Add only.

---

## Test Requirements

**All 36 Phase 1 tests must continue to pass. Do not break them.**

New tests must follow SPEC-010 patterns:
- Use `tmp_path` for all file system operations
- Use `unittest.mock` for all adapter tests — no real database connections
- No network calls in any test
- No real dlt/dbt/Soda execution in tests — mock at the subprocess/library level

### Minimum tests required:

**tests/runtime/test_runner.py** — 5 tests minimum:
- `run()` returns `PipelineResult` with status=SUCCESS on all steps passing
- `run()` returns `PipelineResult` with status=FAILED when step fails
- `run()` always updates state — even on exception
- `validate()` returns status=VALID on clean config
- `validate()` returns status=INVALID when adapter connectivity fails

**tests/runtime/test_result.py** — 3 tests minimum:
- `PipelineResult.succeeded()` returns True on SUCCESS
- `PipelineResult.failed()` returns True on FAILED
- `StepResult` stores error_code and error_msg correctly

**tests/adapters/test_factory.py** — 3 tests minimum:
- Factory returns `DltIngestionAdapter` for postgres source config
- Factory returns None for transformation when `enabled=False`
- Factory returns None for quality when `enabled=False`

**tests/adapters/ingestion/test_dlt_adapter.py** — 4 tests minimum:
- `execute()` returns `StepResult` with status=success (mocked dlt)
- `execute()` maps dlt exception to `PK-ADAPTER-002`
- `validate()` returns status=valid on connectivity success (mocked)
- `validate()` returns status=invalid on connectivity failure (mocked)

**tests/adapters/transformation/test_dbt_adapter.py** — 3 tests minimum:
- `execute()` returns StepResult on dbt exit 0 (mocked subprocess)
- `execute()` maps dbt exit 1 to `PK-ADAPTER-002`
- `validate()` runs `dbt parse` and returns StepResult (mocked subprocess)

**tests/adapters/quality/test_soda_adapter.py** — 3 tests minimum:
- `execute()` returns StepResult with pass/fail counts (mocked Soda)
- `execute()` maps Soda failure to `PK-ADAPTER-002`
- `validate()` checks directory exists and returns StepResult

**tests/contracts/test_models.py** — 4 tests minimum:
- Valid contract YAML loads into `ContractDefinition`
- `ContractResult.passed()` True when no violations
- `ContractResult.passed()` False when violations exist
- `ContractViolation` carries PK error code and evidence dict

**tests/contracts/test_validator.py** — 6 tests minimum:
- Freshness violation detected → `PK-CONTRACT-002`
- Missing required column detected → `PK-CONTRACT-001`
- Uniqueness violation detected → `PK-CONTRACT-003`
- Not-null violation detected → `PK-CONTRACT-004`
- All checks pass → `ContractResult.passed()` is True
- All violations collected in one pass — not stopped at first failure

---

## Architecture Rules — Non-Negotiable

```
Runtime never imports from pipelinekit.cli          (SPEC-003, ADR-003)
CLI never imports from pipelinekit.runtime internals (SPEC-001)
Adapters never import from each other               (contracts/adapter.yaml)
dlt imports only inside adapters/ingestion/dlt/     (SPEC-009)
dbt imports only inside adapters/transformation/dbt/ (SPEC-009)
Soda imports only inside adapters/quality/soda/     (SPEC-009)
All exceptions mapped to PK error codes             (Error-Codes.md)
No bare except: clauses                             (SPEC-010, ruff)
No print() — use Rich Console in CLI only           (SPEC-010)
All public functions have type annotations          (SPEC-010, mypy)
No AI calls anywhere in Phase 2                     (Constitution, ADR-007)
No network calls in tests                           (SPEC-010)
Run record always updated — never left as pending   (SPEC-003)
PROJECT-STATUS.md never touched                     (Command Center owns it)
```

---

## Validation Commands

Run these in order after implementation. All must exit 0.

```powershell
cd C:\Users\HP\Documents\pipelinekit

poetry install

# Verify Phase 1 still works
poetry run pipelinekit --help
poetry run pipelinekit init
poetry run pipelinekit validate
poetry run pipelinekit status

# Verify Phase 2 works
poetry run pipelinekit run --dry-run
poetry run pipelinekit validate --contracts

# Full quality gate
poetry run pytest --cov=src/pipelinekit --cov-report=term-missing --cov-fail-under=80
poetry run ruff check .
poetry run black --check .
poetry run mypy src/pipelinekit
```

---

## Definition of Done

Phase 2 is complete when ALL of the following are true:

```
✓ poetry install completes with no errors
✓ All 36 Phase 1 tests still pass — nothing broken
✓ pipelinekit run --dry-run exits 0 with validation summary
✓ pipelinekit validate --contracts runs contract checks
✓ PipelineRunner.run() executes ingestion → transformation → quality
✓ PipelineRunner.run() always updates state — never leaves run as pending
✓ PipelineResult carries structured step results
✓ All adapter errors mapped to PK error codes
✓ ContractValidator detects all 5 violation types
✓ Contract violations carry PK error codes and evidence dicts
✓ No dlt/dbt/Soda imports outside their adapter directories
✓ pytest passes — all tests green (Phase 1 + Phase 2)
✓ coverage >= 80% across src/pipelinekit/
✓ ruff check passes — zero errors
✓ black --check passes — zero errors
✓ mypy passes — zero errors
✓ No secrets, credentials, or API keys in any file
✓ PROJECT-STATUS.md untouched
```

---

## Stop and Ask Before

- Adding any dependency not listed in the pyproject.toml section above
- Creating any file not in the allowed file list
- Importing dlt, dbt, or Soda outside their adapter directories
- Touching any file in docs/, contracts/, schemas/, agents/
- Touching PROJECT-STATUS.md for any reason
- Modifying any Phase 1 test
- Implementing Phase 3 features (observability, blueprints, Resend)
- Implementing Phase 4 features (AI diagnostics, MCP)
- Making any external network call in source code or tests

---

## Final Instruction

Phase 1 built the foundation — the CLI, config, and state layers.
Phase 2 builds the engine — the runtime, adapters, and contracts.

When Phase 2 is complete, PipelineKit can move data, transform it, and validate
it against contracts. That is the first version of trusted analytics infrastructure.

Every adapter must be replaceable.
Every error must be structured.
Every run must be recorded.
Every contract violation must carry evidence.

The product is Trusted Analytics Infrastructure.
Build the engine that earns that name.
