# SPEC-012-Health-Command-System.md

**Status:** Approved  
**Owner:** cli-engineer + release-engineer  
**Phase:** 5 — Architecture Layer (alongside architect commands)  
**Date:** June 25, 2026  
**ADRs:** ADR-008 (Deterministic), ADR-009 (Human-Readable), ADR-011 (Trust)  
**Depends on:** SPEC-001 (CLI), SPEC-007 (State), SPEC-006 (Blueprints)  
**Reference:** docs/reference/Sustainability-Policy.md

---

## Purpose

The Sustainability Policy defines the maintenance habits for PipelineKit.  
This SPEC defines the CLI commands that make those habits executable, not just readable.

A policy that lives only as a markdown file gets read once.  
A policy that is also a CLI command gets run every time it matters.

`pipelinekit health` is the programmed sustainability policy.

---

## What pipelinekit health Covers

Every section of the Sustainability Policy maps to a health check:

| Policy Section | Command |
|---|---|
| Dependency currency | `pipelinekit health deps` |
| Security advisories | `pipelinekit health security` |
| Blueprint integrity | `pipelinekit health blueprints` |
| SPEC status drift | `pipelinekit health specs` |
| Test suite status | `pipelinekit health tests` |
| Full summary | `pipelinekit health` |

---

## CLI Commands

```python
# src/pipelinekit/cli/health.py

health_app = typer.Typer(
    name="health",
    help="Check PipelineKit installation and project health.",
    no_args_is_help=False,  # pipelinekit health runs all checks by default
)

@health_app.callback(invoke_without_command=True)
def health_command(ctx: typer.Context):
    """Run all health checks. Use subcommands for individual checks."""
    if ctx.invoked_subcommand is None:
        # Run all checks
        ...

@health_app.command("deps")
def deps_command():
    """Check for outdated dependencies."""

@health_app.command("security")
def security_command():
    """Check for known security vulnerabilities (requires pip-audit)."""

@health_app.command("blueprints")
def blueprints_command():
    """Validate all installed blueprints against their schemas."""

@health_app.command("specs")
def specs_command():
    """Check SPEC status headers for drift (Placeholder/Draft vs Implemented)."""

@health_app.command("tests")
def tests_command():
    """Run test suite and report coverage."""
```

---

## Output Format

### pipelinekit health (full run)

```
PipelineKit Health Check
────────────────────────

Dependencies       ✓  All 12 direct dependencies current
Security           ✓  No known vulnerabilities (last checked: 2026-06-25)
Blueprints         ✓  1 blueprint installed, all valid
SPECs              ⚠  2 SPECs show status drift (see below)
Tests              ✓  151 passed, 82.16% coverage

Overall: 4/5 checks passed

Issues:
  SPEC-002: status=Approved but phase=Implemented
  SPEC-007: status=Approved but phase=Implemented
  Run 'pipelinekit health specs --fix' to update status headers

Last full health check: 2026-06-25 14:32:00 UTC
```

### pipelinekit health deps

```
Dependency Health
─────────────────

  Package       Current   Latest    Status
  ──────────    ───────   ──────    ──────
  dlt           1.28.0    1.28.3    ⚠ patch available
  anthropic     0.25.1    0.26.0    ⚠ minor available
  openai        1.35.0    1.35.0    ✓ current
  dbt-core      1.8.4     1.8.4     ✓ current
  soda-core     3.5.6     3.5.6     ✓ current
  typer         0.26.7    0.26.7    ✓ current
  pydantic      2.7.1     2.7.1     ✓ current

Recommendation:
  dlt 1.28.3 — patch update, safe to apply
  anthropic 0.26.0 — minor update, test before applying

Run 'poetry update dlt' to apply patch updates.
```

### pipelinekit health security

```
Security Check
──────────────

Scanning 47 packages...

  ✓ No known vulnerabilities found

Last scan: 2026-06-25 14:32:00 UTC
Next recommended scan: 2026-07-25

Note: Install pip-audit to enable this check:
  poetry add --group dev pip-audit
```

### pipelinekit health blueprints

```
Blueprint Health
────────────────

  Blueprint               Version   Schema   Contracts   dbt
  ─────────────────────   ───────   ──────   ─────────   ───
  postgres-to-snowflake   1.0.0     ✓        ✓           ✓

All 1 blueprint(s) healthy.
```

### pipelinekit health specs

```
SPEC Status Check
─────────────────

  SPEC                              Status     Phase      Drift
  ──────────────────────────────    ─────────  ─────────  ──────
  SPEC-001-CLI-Framework            Approved   Phase 1    ⚠ should be Implemented
  SPEC-002-Configuration-System     Implemented Phase 1   ✓
  SPEC-003-Pipeline-Runtime         Implemented Phase 2   ✓
  ...

2 SPECs with status drift detected.
Run 'pipelinekit health specs --fix' to update headers automatically.
```

---

## Implementation Details

### deps check

Uses `subprocess` to call `poetry show --outdated --no-ansi` and parses output.  
Categorizes results: patch (safe), minor (test first), major (ADR required).  
Does not automatically update anything — reports only.

### security check

Uses `subprocess` to call `pip-audit --format=json` if available.  
If `pip-audit` not installed → prints installation instructions, exits 0.  
Never fails the check for missing tool — just informs.

### blueprints check

Uses existing `BlueprintRegistry` and `BlueprintValidator` from Phase 3.  
Calls `validator.validate()` for each installed blueprint.  
Reports schema, contracts, and dbt project validity.

### specs check

Reads all `.md` files in `docs/specifications/`.  
Parses the `**Status:**` header line.  
Cross-references against `PROJECT-STATUS.md` phase completion record.  
Reports mismatches between status header and known implementation state.  
`--fix` flag rewrites the status header in place — uses the exact same pattern as the Phase 3 housekeeping PowerShell commands.

### tests check

Uses `subprocess` to call `poetry run pytest --cov=src/pipelinekit --co -q`.  
Reports: test count, pass/fail, coverage percentage.  
Does not re-run tests by default (slow) — shows last pytest result from `.coverage` file.  
`--run` flag triggers a fresh test run.

---

## State Recording

Every `pipelinekit health` run is recorded in state.db:

```sql
CREATE TABLE IF NOT EXISTS health_runs (
    id          TEXT PRIMARY KEY,
    ran_at      TEXT NOT NULL,
    deps_status TEXT,      -- ok | warnings | errors
    security_status TEXT,
    blueprints_status TEXT,
    specs_status TEXT,
    tests_status TEXT,
    overall_status TEXT,
    summary     TEXT       -- JSON
);
```

This allows `pipelinekit status` to show last health check date alongside run history.

---

## File Structure

```
src/pipelinekit/
├── cli/
│   └── health.py           health command group
└── health/
    ├── __init__.py
    ├── deps.py             DepsChecker
    ├── security.py         SecurityChecker
    ├── blueprints.py       BlueprintHealthChecker
    ├── specs.py            SpecDriftChecker
    └── tests.py            TestsChecker

tests/
└── health/
    ├── __init__.py
    ├── test_deps.py
    ├── test_blueprints.py
    └── test_specs.py
```

---

## pyproject.toml Addition

```toml
[tool.poetry.group.dev.dependencies]
pip-audit = "^2.0"
```

---

## Error Codes

| Code | Meaning |
|---|---|
| `PK-HEALTH-001` | Dependency check failed (poetry unavailable) |
| `PK-HEALTH-002` | Security check failed (pip-audit error) |
| `PK-HEALTH-003` | Blueprint validation failed |
| `PK-HEALTH-004` | SPEC drift detected |

---

## Acceptance Criteria

```
✓ pipelinekit health runs all 5 checks
✓ pipelinekit health deps shows outdated packages
✓ pipelinekit health security shows vulnerability status
✓ pipelinekit health blueprints validates all installed blueprints
✓ pipelinekit health specs detects status header drift
✓ pipelinekit health tests shows last test run summary
✓ Health run recorded in state.db
✓ All checks exit 0 even when warnings exist (non-blocking)
✓ Only pipelinekit health --strict exits 1 on warnings
✓ poetry run pytest tests/health/ → all tests pass
```

---

## Out of Scope

- Auto-upgrading dependencies — health reports, never acts
- Auto-fixing all SPEC drift — `--fix` flag for specs only
- Continuous monitoring daemon — not planned
- Remote health reporting — not planned
