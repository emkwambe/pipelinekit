# SPEC-010-Testing-and-Quality-Gates.md

**Status:** Approved  
**Owner:** quality-engineer  
**Phase:** 1 — Foundation (applies to all phases)  
**Date:** June 24, 2026  
**ADRs:** ADR-008 (Deterministic), ADR-011 (Trust as primary metric)  
**Reference:** SPEC-002-OLD-Repository-Standards.md (archive, 80% coverage standard)

---

## Purpose

Define the testing standards, quality gates, and CI requirements for PipelineKit.

Every feature shipped must be tested.
Every test must be deterministic.
Every merge to main must pass all quality gates.
Quality is not optional — it is the mechanism that makes trust possible.

---

## Governing Rules

- Minimum 80% test coverage across `src/pipelinekit/`
- All tests must be deterministic — no flaky tests permitted
- Tests must not make external network calls
- Tests must not require running databases, dlt, dbt, or Soda
- Tests must run in under 60 seconds total (Phase 1)
- Every new module gets a corresponding test file before merge
- No code ships without tests — this applies to all agents in all phases

---

## Test Stack

| Tool | Purpose | Version |
|---|---|---|
| `pytest` | Test runner | Latest stable |
| `pytest-cov` | Coverage measurement | Latest stable |
| `black` | Code formatting | Latest stable |
| `ruff` | Linting | Latest stable |
| `mypy` | Static type checking | Latest stable |

---

## Test Structure

```
tests/
├── __init__.py
├── cli/
│   ├── __init__.py
│   ├── test_init.py          pipelinekit init tests
│   ├── test_validate.py      pipelinekit validate tests
│   └── test_status.py        pipelinekit status tests
├── config/
│   ├── __init__.py
│   ├── test_schema.py        Pydantic model tests
│   └── test_loader.py        load_config, write_default_config tests
├── state/
│   ├── __init__.py
│   └── test_db.py            SQLite state tests
├── runtime/                  Phase 2 — runtime-engineer adds
├── adapters/                 Phase 2 — runtime-engineer adds
├── contracts/                Phase 2 — runtime-engineer adds
├── observability/            Phase 3
└── ai/                       Phase 4
```

---

## Required Tests — Phase 1

### tests/cli/test_init.py

```python
# Minimum required tests

def test_init_creates_config(tmp_path):
    """pipelinekit init creates pipelinekit.yaml when not present."""
    ...

def test_init_does_not_overwrite(tmp_path):
    """pipelinekit init does not overwrite existing pipelinekit.yaml."""
    ...

def test_init_exits_zero(tmp_path):
    """pipelinekit init exits with code 0 on success."""
    ...

def test_init_exits_zero_when_exists(tmp_path):
    """pipelinekit init exits with code 0 even when file already exists."""
    ...

def test_init_creates_gitignore_entry(tmp_path):
    """pipelinekit init adds .pipelinekit/ to .gitignore."""
    ...
```

### tests/cli/test_validate.py

```python
def test_validate_exits_zero_on_valid_config(tmp_path):
    """pipelinekit validate exits 0 on valid pipelinekit.yaml."""
    ...

def test_validate_exits_one_on_missing_file(tmp_path):
    """pipelinekit validate exits 1 when pipelinekit.yaml not found."""
    ...

def test_validate_exits_one_on_invalid_yaml(tmp_path):
    """pipelinekit validate exits 1 on malformed YAML."""
    ...

def test_validate_exits_one_on_missing_section(tmp_path):
    """pipelinekit validate exits 1 when required section is absent."""
    ...

def test_validate_prints_error_code(tmp_path, capsys):
    """pipelinekit validate prints PK error code on failure."""
    ...
```

### tests/cli/test_status.py

```python
def test_status_no_runs(tmp_path):
    """pipelinekit status prints 'No runs recorded yet.' on fresh state."""
    ...

def test_status_exits_zero(tmp_path):
    """pipelinekit status exits 0 always (even with no runs)."""
    ...

def test_status_initializes_db(tmp_path):
    """pipelinekit status creates .pipelinekit/state.db if not present."""
    ...
```

### tests/config/test_schema.py

```python
def test_valid_config_loads():
    """Full valid YAML dict loads into PipelineConfig without error."""
    ...

def test_missing_pipeline_section_fails():
    """PipelineConfig raises ValidationError when pipeline section absent."""
    ...

def test_missing_ingestion_section_fails():
    """PipelineConfig raises ValidationError when ingestion section absent."""
    ...

def test_default_values_applied():
    """Optional fields receive correct defaults when not provided."""
    ...
```

### tests/config/test_loader.py

```python
def test_load_config_valid(tmp_path):
    """load_config() returns PipelineConfig on valid pipelinekit.yaml."""
    ...

def test_load_config_not_found(tmp_path):
    """load_config() raises ConfigurationError(PK-CONFIG-003) when file absent."""
    ...

def test_load_config_invalid_yaml(tmp_path):
    """load_config() raises ConfigurationError(PK-CONFIG-004) on bad YAML."""
    ...

def test_write_default_config(tmp_path):
    """write_default_config() creates file that passes load_config()."""
    ...

def test_config_exists_true(tmp_path):
    """config_exists() returns True when pipelinekit.yaml present."""
    ...

def test_config_exists_false(tmp_path):
    """config_exists() returns False when pipelinekit.yaml absent."""
    ...
```

### tests/state/test_db.py

```python
def test_initialize_creates_db(tmp_path):
    """initialize() creates .pipelinekit/state.db."""
    ...

def test_initialize_idempotent(tmp_path):
    """initialize() called twice does not raise or corrupt db."""
    ...

def test_get_recent_runs_empty(tmp_path):
    """get_recent_runs() returns [] on fresh database."""
    ...

def test_insert_and_retrieve_run(tmp_path):
    """insert_run() followed by get_recent_runs() returns the run."""
    ...

def test_state_error_on_bad_path():
    """initialize() raises StateError(PK-STATE-001) on unwritable path."""
    ...
```

---

## Test Patterns

### Use tmp_path for all file system tests

```python
def test_init_creates_config(tmp_path):
    from typer.testing import CliRunner
    from pipelinekit.cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["init"], catch_exceptions=False,
                           env={"PWD": str(tmp_path)})
    assert result.exit_code == 0
    assert (tmp_path / "pipelinekit.yaml").exists()
```

### Use Typer's test runner for CLI tests

```python
from typer.testing import CliRunner
from pipelinekit.cli.main import app

runner = CliRunner()

def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "validate" in result.output
    assert "status" in result.output
```

### Never mock the file system — use tmp_path

Tests must operate on real temporary directories.
Mocking filesystem operations hides real integration bugs.

### Never test private implementation details

Test the public interface — what commands produce, what functions return.
Do not test internal variable names or private methods.

---

## Quality Gate Commands

These must all pass before any code merges to main:

```powershell
# Run in order — all must exit 0

poetry run pytest --cov=src/pipelinekit --cov-report=term-missing --cov-fail-under=80
poetry run ruff check .
poetry run black --check .
poetry run mypy src/pipelinekit
```

---

## CI Configuration

The release-engineer activates at end of Phase 1 to create:

```
.github/workflows/ci.yml
```

Minimum CI pipeline:

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install poetry
      - run: poetry install
      - run: poetry run ruff check .
      - run: poetry run black --check .
      - run: poetry run mypy src/pipelinekit
      - run: poetry run pytest --cov=src/pipelinekit --cov-fail-under=80
```

---

## Coverage Rules

| Module | Minimum Coverage |
|---|---|
| `src/pipelinekit/cli/` | 90% |
| `src/pipelinekit/config/` | 95% |
| `src/pipelinekit/state/` | 90% |
| `src/pipelinekit/core/` | 85% |
| Overall | 80% |

Coverage is measured by `pytest-cov`.
Coverage reports print to terminal.
Coverage below threshold fails the build.

---

## Linting Rules

`ruff` enforces:
- No unused imports
- No undefined names
- No bare `except:`
- No `print()` in source code (use Rich Console)
- F-string consistency

`black` enforces:
- Line length 88
- Consistent formatting across all files

`mypy` enforces:
- All public functions have type annotations
- No `Any` without explicit comment justification
- Pydantic models are fully typed

---

## Constraints

- No network calls in any test
- No real database connections in tests — use tmp_path SQLite
- No `time.sleep()` in tests
- No hardcoded absolute paths in tests — use `tmp_path` or `Path.cwd()`
- No test ordering dependencies — each test must be independently runnable
- Test files named `test_*.py`
- Test functions named `test_*`

---

## AI Guardrails

- AI may generate test scaffolds — quality-engineer reviews before merge
- AI-generated tests must be reviewed for meaningful assertions
- AI must not generate tests that always pass (e.g. `assert True`)
- AI must not skip edge cases (missing file, invalid YAML, empty state)

---

## Acceptance Criteria

```
✓ pytest discovers all tests automatically
✓ All Phase 1 tests pass on fresh clone
✓ Coverage >= 80% overall
✓ ruff check passes with zero errors
✓ black --check passes with zero errors
✓ mypy passes with zero errors
✓ Total test suite runs in under 60 seconds
✓ No test requires network access
✓ No test requires external database
```

---

## Out of Scope

- Integration tests against real databases — Phase 2
- End-to-end blueprint tests — Phase 3
- AI diagnostic tests — Phase 4
- Load or performance tests — not planned for MVP
- Browser or UI tests — not planned
