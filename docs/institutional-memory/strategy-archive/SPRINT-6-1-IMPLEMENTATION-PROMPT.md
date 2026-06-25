# PipelineKit — Sprint 6-1 Implementation Prompt
## pipelinekit health + Schema Fix + pip-audit

---

## Your Identity

You are Claude Code operating as **cli-engineer** and **quality-engineer**.

Primary SPEC: `docs/specifications/SPEC-012-Health-Command-System.md`

---

## Repository

```
C:\Users\HP\Documents\pipelinekit
```

## Read First

```
1.  .claude/CLAUDE.md
2.  docs/specifications/SPEC-012-Health-Command-System.md   ← Primary spec
3.  docs/reference/Sustainability-Policy.md
4.  docs/reference/PROJECT-STATUS.md
5.  docs/reference/Error-Codes.md
6.  schemas/architecture.schema.json                        ← Fix needed
7.  src/pipelinekit/cli/main.py                             ← Register health
8.  src/pipelinekit/blueprints/registry.py                  ← Health reuses this
9.  src/pipelinekit/blueprints/validator.py                 ← Health reuses this
10. src/pipelinekit/state/db.py                             ← Add health_runs table
```

---

## Sprint Goal

```powershell
poetry run pipelinekit health
poetry run pipelinekit health deps
poetry run pipelinekit health security
poetry run pipelinekit health blueprints
poetry run pipelinekit health specs
poetry run pipelinekit health tests
poetry run pytest --cov=src/pipelinekit --cov-fail-under=80
poetry run ruff check .
poetry run black --check .
poetry run mypy src/pipelinekit
```

All must exit 0. All 184 prior tests must still pass.

---

## Files You Are Allowed To Create

```
src/pipelinekit/cli/health.py
src/pipelinekit/health/__init__.py
src/pipelinekit/health/deps.py
src/pipelinekit/health/security.py
src/pipelinekit/health/blueprints.py
src/pipelinekit/health/specs.py
src/pipelinekit/health/tests.py

tests/health/__init__.py
tests/health/test_deps.py
tests/health/test_blueprints.py
tests/health/test_specs.py
```

You may also modify:
```
src/pipelinekit/cli/main.py          Register health command group only
src/pipelinekit/state/db.py          Add health_runs table + insert_health_run() only
schemas/architecture.schema.json     Fix adr_compliance type: object → array
docs/reference/Error-Codes.md        Add PK-HEALTH-001 to 004 only
pyproject.toml                       Add pip-audit to dev dependencies only
```

---

## Files You Must Not Modify

```
docs/reference/PROJECT-STATUS.md    ← NEVER — Command Center owns it
All Phase 1-5 source files          ← READ ONLY
All Phase 1-5 test files            ← READ ONLY
schemas/diagnostic.schema.json      ← READ ONLY
schemas/blueprint.schema.json       ← READ ONLY
contracts/                          ← READ ONLY
agents/                             ← READ ONLY
docs/specifications/ (others)       ← READ ONLY
```

---

## Schema Fix — Do This First

`schemas/architecture.schema.json` has a type conflict flagged in Phase 5.

Change `adr_compliance` from:
```json
"adr_compliance": {"type": "object"}
```
to:
```json
"adr_compliance": {"type": "array"}
```

This aligns the schema with `ArchitectureResult.adr_compliance: list[ADRComplianceCheck]`.
Fix this before implementing health commands.

---

## Implementation Requirements

### pyproject.toml — Add pip-audit

```toml
[tool.poetry.group.dev.dependencies]
pip-audit = "^2.0"
```

---

### src/pipelinekit/health/deps.py

```python
class DepsChecker:
    """Check for outdated dependencies using poetry show --outdated."""

    def check(self) -> HealthCheckResult:
        """
        Run: poetry show --outdated --no-ansi
        Parse output into: current, patch_available, minor_available, major_available
        Returns HealthCheckResult with status and details.
        Never raises — always returns a result.
        """
```

Categories:
- `ok` — all dependencies current
- `warning` — patch or minor updates available
- `error` — major updates available or poetry unavailable

---

### src/pipelinekit/health/security.py

```python
class SecurityChecker:
    """Check for known vulnerabilities using pip-audit."""

    def check(self) -> HealthCheckResult:
        """
        Run: pip-audit --format=json if available.
        If pip-audit not installed: return status=info with install instructions.
        Never fails the check for missing tool — informs only.
        """
```

---

### src/pipelinekit/health/blueprints.py

```python
class BlueprintHealthChecker:
    """Validate all installed blueprints using existing BlueprintRegistry + Validator."""

    def check(self, cwd: Path | None = None) -> HealthCheckResult:
        """
        Use BlueprintRegistry to list blueprints.
        Use BlueprintValidator to validate each.
        Returns HealthCheckResult with per-blueprint status.
        Returns status=ok if no blueprints installed (not an error).
        """
```

Reuses Phase 3 infrastructure — no new blueprint logic.

---

### src/pipelinekit/health/specs.py

```python
class SpecDriftChecker:
    """Check SPEC status headers against known implementation state."""

    def check(self, specs_dir: Path | None = None) -> HealthCheckResult:
        """
        Read all SPEC-*.md files in docs/specifications/.
        Parse **Status:** header line.
        Cross-reference against known implemented phases.
        Report mismatches: Approved on implemented SPEC = drift.
        Never modifies SPEC files unless --fix flag passed.
        """

    def fix(self, specs_dir: Path | None = None) -> int:
        """Update status headers to Implemented where appropriate. Returns count fixed."""
```

Known implemented SPECs (update status if still showing Approved):
SPEC-001, 002, 003, 004, 006, 007, 008, 009, 010, 011

---

### src/pipelinekit/health/tests.py

```python
class TestsChecker:
    """Report last test run summary from .coverage file."""

    def check(self, cwd: Path | None = None) -> HealthCheckResult:
        """
        Read .coverage file if present — report last coverage %.
        If .coverage absent: return status=info (tests not yet run).
        Does NOT re-run tests by default (slow).
        """
```

---

### HealthCheckResult Model

```python
# src/pipelinekit/health/__init__.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class HealthCheckResult:
    name: str
    status: str          # ok | warning | error | info
    message: str
    details: list[str] = None
    fix_hint: str | None = None
```

---

### src/pipelinekit/cli/health.py

```python
health_app = typer.Typer(
    name="health",
    help="Check PipelineKit installation and project health.",
    no_args_is_help=False,
)

@health_app.callback(invoke_without_command=True)
def health_command(
    ctx: typer.Context,
    strict: bool = typer.Option(False, "--strict", help="Exit 1 on any warning.")
):
    """Run all health checks."""
    if ctx.invoked_subcommand is None:
        # Run all 5 checks and print summary table
        ...
```

**Output — pipelinekit health (full run):**
```
PipelineKit Health Check
────────────────────────

  deps          ✓  All dependencies current
  security      ✓  No known vulnerabilities
  blueprints    ✓  1 blueprint installed, all valid
  specs         ⚠  2 SPECs show status drift
  tests         ✓  184 passed, 81.27% coverage

4/5 checks passed

Issues:
  specs: SPEC-001, SPEC-002 show Approved — should be Implemented
  Run 'pipelinekit health specs --fix' to update

Run 'pipelinekit health <check>' for details.
```

Default: exits 0 even with warnings.
`--strict`: exits 1 if any check is warning or error.

---

### state/db.py — Addition Only

```sql
CREATE TABLE IF NOT EXISTS health_runs (
    id              TEXT PRIMARY KEY,
    ran_at          TEXT NOT NULL,
    deps_status     TEXT,
    security_status TEXT,
    blueprints_status TEXT,
    specs_status    TEXT,
    tests_status    TEXT,
    overall_status  TEXT,
    summary         TEXT
);
```

```python
def insert_health_run(results: dict, cwd: Path | None = None) -> None:
    """Store health run result. Called by health command only."""
```

---

## Error Codes

```
PK-HEALTH-001   Dependency check failed (poetry unavailable)
PK-HEALTH-002   Security check failed (pip-audit error)
PK-HEALTH-003   Blueprint validation failed
PK-HEALTH-004   SPEC drift detected
```

Add `HealthError` to `core/errors.py`.

---

## Test Requirements

All 184 prior tests must still pass. New tests mock subprocess calls.

**tests/health/test_deps.py** — 3 tests:
- Returns `ok` when no outdated packages (mocked poetry output)
- Returns `warning` when patch updates available
- Returns `info` when poetry unavailable

**tests/health/test_blueprints.py** — 3 tests:
- Returns `ok` when blueprint validates cleanly
- Returns `error` when blueprint schema fails
- Returns `ok` when no blueprints installed

**tests/health/test_specs.py** — 3 tests:
- Detects drift when SPEC shows Approved but is implemented
- Returns `ok` when all SPECs correct
- `fix()` updates status headers correctly (tmp_path)

---

## Validation Commands

```powershell
cd C:\Users\HP\Documents\pipelinekit
poetry install

poetry run pipelinekit health
poetry run pipelinekit health deps
poetry run pipelinekit health security
poetry run pipelinekit health blueprints
poetry run pipelinekit health specs
poetry run pipelinekit health tests

poetry run pytest --cov=src/pipelinekit --cov-fail-under=80
poetry run ruff check .
poetry run black --check .
poetry run mypy src/pipelinekit
```

---

## Definition of Done

```
✓ schemas/architecture.schema.json — adr_compliance is array not object
✓ pipelinekit health runs all 5 checks
✓ pipelinekit health deps shows dependency status
✓ pipelinekit health security shows vulnerability status
✓ pipelinekit health blueprints validates Blueprint #001
✓ pipelinekit health specs detects SPEC drift
✓ pipelinekit health tests shows coverage summary
✓ Health run recorded in state.db
✓ --strict flag exits 1 on warnings
✓ All 184 prior tests still pass
✓ coverage >= 80% overall
✓ ruff, black, mypy clean
✓ PROJECT-STATUS.md untouched
```

---

## Stop and Ask Before

- Adding any dependency beyond pip-audit
- Touching PROJECT-STATUS.md
- Modifying any Phase 1-5 source or test file
- Running real pip-audit or poetry commands in tests (mock only)

---

## Commit Message

```
feat: Sprint 6-1 — pipelinekit health + schema fix + pip-audit

- src/pipelinekit/health/ — deps, security, blueprints, specs, tests checkers
- src/pipelinekit/cli/health.py — health command group (5 subcommands)
- schemas/architecture.schema.json — adr_compliance type fixed (object → array)
- pyproject.toml — pip-audit added to dev dependencies
- state/db.py — health_runs table + insert_health_run()
- core/errors.py — HealthError added

SPEC-012 satisfied. Sustainability policy is now programmed, not just documented.
```
