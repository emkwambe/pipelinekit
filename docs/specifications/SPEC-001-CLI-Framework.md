# SPEC-001-CLI-Framework.md

**Status:** Approved  
**Owner:** cli-engineer  
**Phase:** 1 — Foundation  
**Date:** June 24, 2026  
**Supersedes:** SPEC-001-OLD-Engineering-Backlog.md (archive)  
**ADRs:** ADR-003 (CLI-First), ADR-004 (Local-First), ADR-008 (Deterministic), ADR-009 (Human-Readable)

---

## Purpose

Define the complete CLI framework for PipelineKit MVP.

The CLI is the primary interface for all PipelineKit capabilities.
Every feature must be accessible from the terminal.
The CLI orchestrates. It never contains business logic.

---

## Governing Rules

- CLI-first. Every capability is a command.
- CLI calls runtime. CLI never calls providers directly.
- No business logic inside CLI commands.
- All commands must be deterministic.
- All commands must be scriptable (exit codes, no interactive prompts in non-init commands).
- All output uses Rich for formatting.
- All errors use structured PipelineKit error codes.

---

## Required Capabilities

### Phase 1 (this SPEC)

| Command | Description | Exit 0 | Exit 1 |
|---|---|---|---|
| `pipelinekit --help` | Show all commands and version | Always | Never |
| `pipelinekit --version` | Print version string | Always | Never |
| `pipelinekit init` | Generate pipelinekit.yaml in cwd | File created or already exists | Write failure |
| `pipelinekit validate` | Validate pipelinekit.yaml | Config valid | Config invalid |
| `pipelinekit status` | Show last run state from SQLite | Always | DB unavailable |

### Phase 2 (runtime-engineer activates — not in this SPEC)

`pipelinekit run` — execute pipeline  
`pipelinekit doctor` — inspect pipeline health  
`pipelinekit report` — generate pipeline report  
`pipelinekit migrate` — migrate from another tool  

### Phase 4 (diagnostics-engineer activates — not in this SPEC)

`pipelinekit diagnose` — AI-assisted root cause analysis  

---

## Inputs

- Working directory (cwd) — all commands operate relative to cwd
- `pipelinekit.yaml` — loaded by validate and status
- `.pipelinekit/state.db` — read by status

---

## Outputs

- `pipelinekit.yaml` — created by init
- Terminal output via Rich (tables, panels, colored text)
- Exit codes (0 = success, 1 = failure)
- Structured error messages: `[PK-CONFIG-001] Invalid pipelinekit.yaml`

---

## CLI Command Specifications

### `pipelinekit init`

**Behavior:**
1. Check if `pipelinekit.yaml` exists in cwd
2. If exists: print warning with Rich, exit 0 (do not overwrite)
3. If not exists: write default `pipelinekit.yaml` (see SPEC-002 for schema)
4. Print success message with Rich

**Output (success):**
```
✓ Created pipelinekit.yaml
  Edit this file to configure your pipeline.
  Run 'pipelinekit validate' to check your configuration.
```

**Output (already exists):**
```
⚠ pipelinekit.yaml already exists. Not overwritten.
  Run 'pipelinekit validate' to check your configuration.
```

**Never:**
- Overwrite existing config without explicit `--force` flag (Phase 2 feature)
- Prompt interactively for values in Phase 1

---

### `pipelinekit validate`

**Behavior:**
1. Look for `pipelinekit.yaml` in cwd
2. If not found: print error `[PK-CONFIG-003] pipelinekit.yaml not found`, exit 1
3. Load and parse YAML
4. Validate against Pydantic schema (SPEC-002)
5. Check all contract-required fields exist
6. Print result with Rich

**Output (success):**
```
✓ pipelinekit.yaml is valid
  Project: my-project (v0.1.0)
```

**Output (failure):**
```
✗ pipelinekit.yaml validation failed

  [PK-CONFIG-001] pipeline.name is required
  [PK-CONFIG-002] ingestion.source is missing
```

**Exit codes:** 0 = valid, 1 = invalid or not found

---

### `pipelinekit status`

**Behavior:**
1. Initialize `.pipelinekit/state.db` if it does not exist
2. Query last 5 pipeline runs from SQLite
3. If no runs: print "No runs recorded yet."
4. If runs exist: print table with run_id, status, timestamp, duration

**Output (no runs):**
```
No runs recorded yet.
Run 'pipelinekit run' to execute your pipeline.
```

**Output (with runs):**
```
Recent pipeline runs:

  Run ID    Status     Started              Duration
  ────────  ─────────  ───────────────────  ────────
  run-001   success    2026-06-24 09:00:00  4.2s
  run-002   failed     2026-06-24 10:00:00  1.1s
```

---

## CLI Architecture Rules

### File structure (cli-engineer owns only these files)

```
src/pipelinekit/cli/
├── __init__.py
├── main.py        Typer app, command registration, version callback
├── init.py        init command implementation
├── validate.py    validate command implementation
└── status.py      status command implementation
```

### Typer app pattern

```python
# main.py
import typer
from pipelinekit.cli.init import init_command
from pipelinekit.cli.validate import validate_command
from pipelinekit.cli.status import status_command

app = typer.Typer(
    name="pipelinekit",
    help="Trusted Analytics Infrastructure.",
    no_args_is_help=True,
)

app.command("init")(init_command)
app.command("validate")(validate_command)
app.command("status")(status_command)
```

### Command pattern (orchestrate only)

```python
# init.py
import typer
from rich.console import Console
from pipelinekit.config.loader import config_exists, write_default_config

console = Console()

def init_command():
    """Create a new PipelineKit project configuration."""
    if config_exists():
        console.print("⚠ pipelinekit.yaml already exists.", style="yellow")
        raise typer.Exit(0)
    write_default_config()
    console.print("✓ Created pipelinekit.yaml", style="green")
    raise typer.Exit(0)
```

The CLI command calls the config module. It does not implement config logic itself.

---

## Constraints

- Python 3.11+
- Typer for all CLI commands
- Rich for all terminal output
- No `print()` statements — use `console = Console()`
- No business logic in CLI files
- No direct database calls in CLI files — call `state.db` module
- No direct file I/O in CLI files — call `config.loader` module

---

## AI Guardrails

- No AI calls in Phase 1 CLI
- No `pipelinekit diagnose` in Phase 1
- `pipelinekit doctor --ai` flag is Phase 3
- CLI never calls LLMProvider directly — goes through diagnostics module

---

## Acceptance Criteria

All of the following must pass before SPEC-001 is considered implemented:

```
✓ poetry run pipelinekit --help  →  shows all commands and version
✓ poetry run pipelinekit init    →  creates pipelinekit.yaml
✓ poetry run pipelinekit init    →  (second run) warns, does not overwrite
✓ poetry run pipelinekit validate →  exits 0 on valid config
✓ poetry run pipelinekit validate →  exits 1 on invalid config, prints error codes
✓ poetry run pipelinekit status  →  prints "No runs recorded yet." on fresh install
✓ poetry run pytest tests/cli/   →  all tests pass
✓ poetry run ruff check .        →  no lint errors
✓ poetry run black --check .     →  no formatting errors
✓ poetry run mypy src/           →  no type errors
```

---

## Out of Scope

- `pipelinekit run` — Phase 2
- `pipelinekit doctor` — Phase 3
- `pipelinekit diagnose` — Phase 4
- `pipelinekit migrate` — Phase 3
- `pipelinekit report` — Phase 3
- Interactive prompts
- `--force` flag on init
- Remote configuration
- Cloud execution
