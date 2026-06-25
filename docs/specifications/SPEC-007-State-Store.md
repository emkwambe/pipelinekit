# SPEC-007-State-Store.md

**Status:** Approved  
**Owner:** cli-engineer (Phase 1 scaffold), runtime-engineer (Phase 2 writes runs)  
**Phase:** 1 — Foundation  
**Date:** June 24, 2026  
**ADRs:** ADR-004 (Local-First), ADR-008 (Deterministic), ADR-009 (Human-Readable)  
**Reference:** docs/reference/Glossary.md (State definition)

---

## Purpose

Define the local state store for PipelineKit.

State is metadata about pipeline execution, validation, diagnosis, and alerts.
State lives in SQLite at `.pipelinekit/state.db` relative to the project directory.
State is local-first, zero-infrastructure, and portable.
State is never sent to a remote server without explicit user configuration.

---

## Governing Rules

- SQLite only — no ORM, no external database in Phase 1
- State lives at `.pipelinekit/state.db` (relative to cwd)
- `.pipelinekit/` directory is created automatically if it does not exist
- `.pipelinekit/` must be added to `.gitignore`
- State is metadata only — no pipeline data is stored in SQLite
- All state reads and writes go through `state/db.py` — never direct SQL in CLI or runtime
- State must initialize cleanly on fresh install (no migration required in Phase 1)

---

## Required Capabilities

### Phase 1 (this SPEC)

- Initialize `.pipelinekit/state.db` and create schema on first use
- Write a `pipeline_runs` table
- Read last N runs for `pipelinekit status`
- Handle missing or corrupted database gracefully

### Phase 2 extension (runtime-engineer writes)

- Insert run record on pipeline start
- Update run record on pipeline completion or failure
- Store run metadata: duration, exit code, error code if failed
- Query runs by status, date range

### Phase 3 extension

- Store diagnostic results
- Store contract violation history
- Store quality check results

---

## Database Location

```
<project_cwd>/
├── pipelinekit.yaml
└── .pipelinekit/
    └── state.db        ← SQLite database
```

`.pipelinekit/` must be in `.gitignore`:
```
.pipelinekit/
```

---

## Schema

### Table: `pipeline_runs`

```sql
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id          TEXT PRIMARY KEY,           -- run-{uuid4 first 8 chars}
    pipeline    TEXT NOT NULL,              -- pipeline.name from config
    status      TEXT NOT NULL,              -- pending | running | success | failed
    started_at  TEXT NOT NULL,              -- ISO 8601 UTC
    finished_at TEXT,                       -- ISO 8601 UTC, NULL if still running
    duration_s  REAL,                       -- seconds, NULL if still running
    error_code  TEXT,                       -- PK-RUNTIME-001 etc, NULL if success
    error_msg   TEXT                        -- human message, NULL if success
);
```

### Table: `validation_runs` (Phase 1 — lightweight)

```sql
CREATE TABLE IF NOT EXISTS validation_runs (
    id          TEXT PRIMARY KEY,
    status      TEXT NOT NULL,              -- valid | invalid
    ran_at      TEXT NOT NULL,              -- ISO 8601 UTC
    error_count INTEGER DEFAULT 0,
    errors      TEXT                        -- JSON array of error strings
);
```

---

## State Module Interface

```python
# src/pipelinekit/state/db.py

from pathlib import Path
from pipelinekit.core.errors import StateError

STATE_DIR = ".pipelinekit"
STATE_DB  = "state.db"

def get_db_path(cwd: Path = Path.cwd()) -> Path:
    """Return the path to state.db, creating .pipelinekit/ if needed."""
    ...

def initialize(cwd: Path = Path.cwd()) -> None:
    """
    Create .pipelinekit/state.db and apply schema if not exists.
    Safe to call on every startup — idempotent.
    Raises StateError(PK-STATE-001) on failure.
    """
    ...

def get_recent_runs(n: int = 5, cwd: Path = Path.cwd()) -> list[dict]:
    """
    Return the last n pipeline runs, most recent first.
    Returns empty list if no runs exist.
    Raises StateError(PK-STATE-001) if database is unavailable.
    """
    ...

def insert_run(run_id: str, pipeline_name: str, cwd: Path = Path.cwd()) -> None:
    """
    Insert a new run record with status=pending.
    Called by runtime-engineer in Phase 2.
    """
    ...

def update_run(run_id: str, status: str, duration_s: float,
               error_code: str = None, error_msg: str = None,
               cwd: Path = Path.cwd()) -> None:
    """
    Update run record on completion or failure.
    Called by runtime-engineer in Phase 2.
    """
    ...
```

---

## Error Codes

| Code | Condition |
|---|---|
| `PK-STATE-001` | Cannot open or create state.db |
| `PK-STATE-002` | Cannot write to state.db (permissions, disk full) |
| `PK-STATE-003` | State schema is corrupted or incompatible |

---

## File Structure

```
src/pipelinekit/
└── state/
    ├── __init__.py
    └── db.py       get_db_path(), initialize(), get_recent_runs(),
                    insert_run(), update_run()
```

---

## Constraints

- Python stdlib `sqlite3` only — no SQLAlchemy, no Peewee, no external ORM
- No migrations framework in Phase 1 — schema is created fresh via `CREATE TABLE IF NOT EXISTS`
- No remote sync of state in any phase unless explicitly configured
- Run IDs are generated as `run-{first 8 chars of uuid4}` — e.g. `run-a3f2c1b8`
- All timestamps stored as ISO 8601 UTC strings: `2026-06-24T09:00:00Z`
- State is append-only in Phase 1 — no delete, no update except run completion

---

## AI Guardrails

- AI may read state to produce diagnostics — read-only
- AI may never write to state directly
- AI may never delete state records
- State is evidence for AI diagnosis — AI interprets, never modifies

---

## gitignore Entry

`pipelinekit init` must ensure `.gitignore` contains:

```
# PipelineKit state
.pipelinekit/
```

If `.gitignore` does not exist, create it.
If `.gitignore` exists and already contains `.pipelinekit/`, do not duplicate.

---

## Acceptance Criteria

```
✓ initialize() creates .pipelinekit/state.db on first call
✓ initialize() is idempotent — safe to call multiple times
✓ get_recent_runs() returns [] on fresh database
✓ get_recent_runs() returns correct rows after insert_run()
✓ initialize() raises StateError(PK-STATE-001) if directory cannot be created
✓ pipelinekit status prints "No runs recorded yet." on fresh database
✓ pipelinekit status prints run table when runs exist
✓ .pipelinekit/ appears in .gitignore after pipelinekit init
✓ poetry run pytest tests/state/ → all tests pass
```

---

## Out of Scope

- Remote state sync — not planned for Phase 1
- State encryption — not planned for Phase 1
- State export/import — Phase 3
- State migrations — Phase 2 if schema changes
- Dashboard or UI for state — not planned
