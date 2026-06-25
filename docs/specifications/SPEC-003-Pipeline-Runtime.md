# SPEC-003-Pipeline-Runtime.md

**Status:** Approved  
**Owner:** runtime-engineer  
**Phase:** 2 — Data Layer  
**Date:** June 25, 2026  
**ADRs:** ADR-003 (CLI-First), ADR-004 (Local-First), ADR-007 (AI is Operator not Owner), ADR-008 (Deterministic), ADR-010 (Explainability Before Automation)  
**Contracts:** contracts/pipeline.yaml, contracts/provider.yaml  
**Depends on:** SPEC-001 (CLI), SPEC-002 (Config), SPEC-007 (State)

---

## Purpose

Define the pipeline runtime — the execution engine that sits between the CLI and the provider adapters.

The runtime owns execution orchestration, run lifecycle management, and result reporting.
The runtime never calls providers directly — it calls adapters.
The CLI never calls the runtime internals — it calls `PipelineRunner`.
The runtime never modifies production without explicit user approval.

---

## Governing Rules

- Runtime is the only layer that coordinates adapter calls
- Runtime records every execution in state (SPEC-007)
- Runtime produces structured results — never free-form output
- Runtime is deterministic: identical inputs produce identical behavior
- Runtime never calls AI — diagnosis is Phase 4
- Runtime never calls Resend directly — notifications go through the notification adapter (Phase 3)
- All provider errors must be caught and mapped to PK error codes

---

## Required Capabilities — Phase 2

| Capability | Description |
|---|---|
| `PipelineRunner.run()` | Orchestrate full pipeline execution end to end |
| `PipelineRunner.validate()` | Validate config + adapters before execution |
| Execution lifecycle | pending → running → success / failed |
| Run record | Write start, update on finish, store error if failed |
| Result object | Structured `PipelineResult` returned to CLI |
| `pipelinekit run` | CLI command that calls `PipelineRunner.run()` |

---

## Inputs

- `PipelineConfig` — loaded by CLI via `config.loader`
- Adapter instances — created by `AdapterFactory`
- State db — written via `state.db`

## Outputs

- `PipelineResult` — structured result object returned to CLI
- State record — written to `.pipelinekit/state.db`
- Console output — via Rich (rendered by CLI, not runtime)

---

## PipelineRunner Interface

```python
# src/pipelinekit/runtime/runner.py

from pipelinekit.config.schema import PipelineConfig
from pipelinekit.runtime.result import PipelineResult

class PipelineRunner:
    def __init__(self, config: PipelineConfig):
        self.config = config

    def run(self) -> PipelineResult:
        """
        Execute the full pipeline:
        1. Initialize state — insert run record (status=pending)
        2. Initialize adapters
        3. Execute ingestion (if enabled)
        4. Execute transformation (if enabled)
        5. Execute quality checks (if enabled)
        6. Update state — success or failed
        7. Return PipelineResult
        """
        ...

    def validate(self) -> PipelineResult:
        """
        Validate configuration and adapter connectivity
        without executing the pipeline.
        Returns PipelineResult with status=valid or status=invalid.
        """
        ...
```

---

## PipelineResult

```python
# src/pipelinekit/runtime/result.py

from dataclasses import dataclass, field
from enum import Enum

class PipelineStatus(str, Enum):
    SUCCESS  = "success"
    FAILED   = "failed"
    PARTIAL  = "partial"
    VALID    = "valid"
    INVALID  = "invalid"

@dataclass
class StepResult:
    step: str                    # "ingestion" | "transformation" | "quality"
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

## Execution Lifecycle

```
CLI calls PipelineRunner.run()
    │
    ├─ 1. state.db.insert_run(run_id, pipeline_name)   status=pending
    │
    ├─ 2. AdapterFactory.create_ingestion(config)
    │     AdapterFactory.create_transformation(config)
    │     AdapterFactory.create_quality(config)
    │
    ├─ 3. ingestion_adapter.execute()     → StepResult
    │     (skip if ingestion.enabled=False)
    │
    ├─ 4. transformation_adapter.execute() → StepResult
    │     (skip if transformation.enabled=False)
    │
    ├─ 5. quality_adapter.execute()       → StepResult
    │     (skip if quality.enabled=False)
    │
    ├─ 6. state.db.update_run(run_id, status, duration_s, error_code)
    │
    └─ 7. return PipelineResult
```

If any step raises an exception:
- Catch it, map to PK error code
- Mark that step as failed
- Continue remaining steps (partial execution)
- Mark overall pipeline as FAILED or PARTIAL
- Always update state — never leave a run in `pending`

---

## pipelinekit run command

```python
# src/pipelinekit/cli/run.py

def run_command(
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate only, do not execute.")
):
    """Execute the configured pipeline."""
```

**Behavior:**
1. Load config via `config.loader.load_config()`
2. If `--dry-run`: call `PipelineRunner.validate()`, print result, exit
3. Else: call `PipelineRunner.run()`, print result table, exit 0 or 1
4. Print execution summary using Rich table

**Output (success):**
```
✓ Pipeline completed successfully

  Step             Status    Duration    Rows
  ─────────────    ───────   ────────    ────
  ingestion        success   12.4s       45,231
  transformation   success   8.1s        —
  quality          success   2.3s        —

  Total: 22.8s
```

**Output (failure):**
```
✗ Pipeline failed

  Step         Status   Error
  ──────────   ──────   ──────────────────────────────
  ingestion    failed   [PK-ADAPTER-001] Connection refused

  Run 'pipelinekit doctor' to diagnose. (Phase 3)
```

---

## File Structure

```
src/pipelinekit/
├── runtime/
│   ├── __init__.py
│   ├── runner.py       PipelineRunner
│   ├── result.py       PipelineResult, StepResult, PipelineStatus
│   └── executor.py     Step execution logic (called by runner)
└── cli/
    └── run.py          pipelinekit run command (cli-engineer adds)
```

---

## Error Codes — Phase 2 Runtime

| Code | Meaning |
|---|---|
| `PK-RUNTIME-001` | Pipeline execution failed (general) |
| `PK-RUNTIME-002` | Provider initialization failed |
| `PK-RUNTIME-003` | Pipeline already running (state conflict) |
| `PK-ADAPTER-001` | Adapter connection failed |
| `PK-ADAPTER-002` | Adapter execution failed |
| `PK-ADAPTER-003` | Adapter returned invalid result |

---

## Constraints

- Runtime never imports from `pipelinekit.cli`
- Runtime never calls providers directly — always through adapters
- Runtime never prints to console — returns `PipelineResult` only
- Runtime never calls AI — Phase 4 only
- Runtime never calls Resend — Phase 3 notification adapter
- All exceptions caught and mapped to PK error codes
- `PipelineRunner` is stateless — config passed at construction
- Execution is synchronous in Phase 2 — async deferred to Phase 3+

---

## AI Guardrails

- No AI calls in Phase 2 runtime
- `PipelineResult` is evidence for future AI diagnosis — structure it clearly
- `StepResult.error_msg` must be human-readable — it feeds Phase 4 diagnostics
- Runtime must never auto-remediate on failure

---

## Acceptance Criteria

```
✓ PipelineRunner.run() returns PipelineResult on success
✓ PipelineRunner.run() returns PipelineResult with status=FAILED on adapter failure
✓ Run record written to state.db on every execution
✓ Run record always updated — never left as pending
✓ pipelinekit run exits 0 on success
✓ pipelinekit run exits 1 on failure with PK error code
✓ pipelinekit run --dry-run validates without executing
✓ poetry run pytest tests/runtime/ → all tests pass
✓ coverage >= 85% on src/pipelinekit/runtime/
```

---

## Out of Scope

- Async execution — Phase 3+
- Parallel step execution — Phase 3+
- Retry logic — Phase 3
- AI diagnostics — Phase 4
- Notification sending — Phase 3
- Blueprint execution — Phase 3
