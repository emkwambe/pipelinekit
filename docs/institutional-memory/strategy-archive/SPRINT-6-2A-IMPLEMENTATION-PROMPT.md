# PipelineKit — Sprint 6-2a Implementation Prompt
## dlt Adapter Completion + SourceConfig Extension + Env Var Interpolation

---

## Your Identity

You are Claude Code operating as **runtime-engineer** and **quality-engineer**.

Primary ADR: `docs/decisions/ADR-017-dlt-Credential-Integration.md`  
Primary SPECs: SPEC-002 (config), SPEC-003 (runtime), SPEC-009 (adapters)

---

## Repository

```
C:\Users\HP\Documents\pipelinekit
```

## Read First

```
1.  .claude/CLAUDE.md
2.  docs/decisions/ADR-017-dlt-Credential-Integration.md   ← Authoritative
3.  docs/specifications/SPEC-002-Configuration-System.md
4.  docs/specifications/SPEC-003-Pipeline-Runtime.md
5.  docs/specifications/SPEC-009-Provider-Adapters.md
6.  docs/reference/Error-Codes.md
7.  docs/reference/Architectural-Smells.md
8.  src/pipelinekit/adapters/ingestion/dlt/adapter.py      ← Complete this
9.  src/pipelinekit/config/schema.py                       ← Extend SourceConfig
10. src/pipelinekit/config/loader.py                       ← Add interpolation
11. src/pipelinekit/config/schema.py                       ← Read current state
12. blueprints/postgres-to-snowflake/ingestion/pipeline.py ← dlt pattern reference
13. scripts/verify-blueprint-001.ps1                       ← Fix harness
```

---

## Sprint Goal

After this sprint, Blueprint #001 must pass a real dry-run:

```powershell
poetry run pipelinekit run --dry-run
```

With real Postgres credentials set — adapter validates connectivity, returns StepResult.

All 209 prior tests must still pass.

---

## Files You Are Allowed To Modify

```
src/pipelinekit/config/schema.py         Extend SourceConfig — add credential fields
src/pipelinekit/config/loader.py         Add _interpolate_env_vars() + apply to load_config
src/pipelinekit/adapters/ingestion/dlt/adapter.py   Complete the adapter
scripts/verify-blueprint-001.ps1         Fix harness — copy example config, not init
docs/reference/Error-Codes.md            Add PK-CONFIG-006 only
```

You may also create:
```
tests/adapters/ingestion/test_dlt_adapter_integration.py   New integration tests (mocked)
```

---

## Files You Must Not Modify

```
docs/reference/PROJECT-STATUS.md    ← NEVER — Command Center owns it
src/pipelinekit/adapters/transformation/   ← READ ONLY
src/pipelinekit/adapters/quality/          ← READ ONLY
src/pipelinekit/adapters/alerts/           ← READ ONLY
src/pipelinekit/runtime/                   ← READ ONLY
src/pipelinekit/contracts/                 ← READ ONLY
src/pipelinekit/ai/                        ← READ ONLY
src/pipelinekit/cli/                       ← READ ONLY
All existing test files                    ← READ ONLY
schemas/                                   ← READ ONLY
contracts/                                 ← READ ONLY
```

---

## Implementation Requirements

### 1. src/pipelinekit/config/schema.py — SourceConfig extension

Add credential fields to `SourceConfig`. All optional — backward compatible with existing tests.

```python
class SourceConfig(BaseModel):
    type: str
    # Postgres / MySQL
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    tables: Optional[list[str]] = None
    # Snowflake
    account: Optional[str] = None
    warehouse: Optional[str] = None
    schema_name: Optional[str] = Field(None, alias="schema")
    # BigQuery
    project: Optional[str] = None
    location: Optional[str] = None
    # DuckDB
    path: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)
```

All new fields optional. All 209 existing tests must still pass — no breaking change.

---

### 2. src/pipelinekit/config/loader.py — Environment variable interpolation

Add `_interpolate_env_vars()` and apply before Pydantic validation.

```python
import os
import re

def _interpolate_env_vars(obj: Any) -> Any:
    """
    Recursively replace ${VAR} patterns with environment variable values.
    Unset variables become empty string — never raise.
    Applied to the raw YAML dict before PipelineConfig validation.
    """
    if isinstance(obj, str):
        return re.sub(
            r'\$\{([^}]+)\}',
            lambda m: os.environ.get(m.group(1), ''),
            obj
        )
    elif isinstance(obj, dict):
        return {k: _interpolate_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_interpolate_env_vars(i) for i in obj]
    return obj
```

In `load_config()`, apply after `yaml.safe_load()`, before `PipelineConfig(**raw)`:

```python
raw = yaml.safe_load(f)
raw = _interpolate_env_vars(raw)
config = PipelineConfig(**raw)
```

**New error code:** Add `PK-CONFIG-006` to `Error-Codes.md`:
```
PK-CONFIG-006   Required credential field empty after env var interpolation
```

`pipelinekit validate` should warn (not fail) when a credential field resolves to empty string — the user may not have set the env var yet. Fail only on `pipelinekit run`.

---

### 3. src/pipelinekit/adapters/ingestion/dlt/adapter.py — Complete the adapter

This is the core of the sprint. The adapter must build a real dlt pipeline.

**initialize():**
```python
def initialize(self) -> None:
    """Build dlt pipeline object from config. Validates imports available."""
    import dlt
    self._pipeline = dlt.pipeline(
        pipeline_name=f"pipelinekit_{self.config.ingestion.source.type}",
        destination=self.config.ingestion.destination.type,
        dataset_name="pipelinekit_raw",
    )
```

**validate():**
```python
def validate(self) -> StepResult:
    """
    Test source connectivity without loading data.
    For Postgres: attempt TCP connection to host:port.
    For Snowflake destination: verify account + credentials format.
    Returns StepResult(status=valid) or StepResult(status=invalid, error_code=PK-ADAPTER-001).
    Never raises — always returns StepResult.
    """
```

**execute():**
```python
def execute(self) -> StepResult:
    """
    Run the dlt pipeline. Returns StepResult with rows_processed.

    Postgres source:
        from dlt.sources.sql_database import sql_database
        conn_str = build_postgres_conn_str(self.config.ingestion.source)
        tables = self.config.ingestion.source.tables or []
        source = sql_database(conn_str).with_resources(*tables)

    Snowflake destination:
        credentials built from config.ingestion.destination fields

    Maps all dlt exceptions to PK-ADAPTER-001 or PK-ADAPTER-002.
    Never lets dlt exceptions propagate raw.
    """
```

**Credential building helpers (private methods):**

```python
def _build_postgres_conn_str(self, source: SourceConfig) -> str:
    """Build postgresql:// connection string from SourceConfig."""
    return (
        f"postgresql://{source.user}:{source.password}"
        f"@{source.host}:{source.port or 5432}/{source.database}"
    )

def _build_snowflake_credentials(self, dest: SourceConfig) -> dict:
    """Build Snowflake credentials dict for dlt."""
    return {
        "account": dest.account,
        "user": dest.user,
        "password": dest.password,
        "database": dest.database,
        "warehouse": dest.warehouse,
        "schema": dest.schema_name or "raw",
    }
```

All dlt imports stay inside this file. Zero dlt imports anywhere else. This is Smell 2 enforced.

---

### 4. scripts/verify-blueprint-001.ps1 — Fix harness

Replace the `pipelinekit init` step with example config copy:

```powershell
# Step 0: Preflight — check required env vars
$required = @("POSTGRES_CONN_STR", "PG_HOST", "PG_DATABASE",
              "SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD",
              "SNOWFLAKE_DATABASE", "SNOWFLAKE_WAREHOUSE")
$missing = $required | Where-Object { -not [Environment]::GetEnvironmentVariable($_) }
if ($missing) {
    Write-Host "✗ Missing env vars: $($missing -join ', ')" -ForegroundColor Red
    Write-Host "  Set all required variables before running this script."
    exit 1
}

# Step 1: Copy example config (not pipelinekit init)
Copy-Item "blueprints\postgres-to-snowflake\pipelinekit.example.yaml" "pipelinekit.yaml" -Force

# Update contracts directory to point to blueprint contracts
$config = Get-Content "pipelinekit.yaml" -Raw
$config = $config -replace "directory: ./contracts", "directory: ./blueprints/postgres-to-snowflake/contracts"
Set-Content "pipelinekit.yaml" $config
```

---

## Test Requirements

All 209 prior tests must still pass — no regressions.

New tests (mock only — no real database connections):

**Extended tests for test_dlt_adapter.py (existing file — add tests):**
- `test_build_postgres_conn_str()` — correct conn string from SourceConfig
- `test_validate_returns_invalid_on_unreachable_host()` — PK-ADAPTER-001 on TCP failure
- `test_execute_maps_dlt_exception_to_pk_code()` — ConfigFieldMissingException → PK-ADAPTER-002

**New tests for loader interpolation:**
Add to `tests/config/test_loader.py` (existing file):
- `test_interpolate_env_vars_string()` — `${VAR}` replaced with env value
- `test_interpolate_env_vars_unset()` — unset var becomes empty string, no raise
- `test_load_config_interpolates_before_validation()` — full round-trip

**New SourceConfig tests:**
Add to `tests/config/test_schema.py` (existing file):
- `test_source_config_accepts_credential_fields()` — user/password/warehouse load correctly
- `test_source_config_backward_compatible()` — existing config without creds still loads

---

## Validation Commands

```powershell
cd C:\Users\HP\Documents\pipelinekit

poetry install

# All prior tests pass
poetry run pytest --cov=src/pipelinekit --cov-fail-under=80

# Config interpolation works
$env:TEST_HOST = "localhost"
poetry run python -c "
from pipelinekit.config.loader import _interpolate_env_vars
result = _interpolate_env_vars({'host': '\${TEST_HOST}'})
assert result['host'] == 'localhost', f'Got: {result}'
print('Interpolation: OK')
"

# SourceConfig accepts credential fields
poetry run python -c "
from pipelinekit.config.schema import SourceConfig
s = SourceConfig(type='postgres', host='localhost', user='admin', password='secret')
print(f'SourceConfig: OK — {s.type} {s.host}')
"

# Quality gates
poetry run ruff check .
poetry run black --check .
poetry run mypy src/pipelinekit
```

---

## Definition of Done

```
✓ SourceConfig has user, password, warehouse, schema_name, tables, project, path fields
✓ All new fields optional — 209 existing tests still pass
✓ load_config() interpolates ${VAR} before Pydantic validation
✓ Unset env vars become empty string — never raise
✓ DltIngestionAdapter.validate() tests TCP connectivity, returns StepResult
✓ DltIngestionAdapter.execute() builds real sql_database source from SourceConfig
✓ Postgres conn string built from config fields
✓ Snowflake credentials built from config fields
✓ All dlt imports isolated in adapter file — zero elsewhere
✓ verify-blueprint-001.ps1 copies example config, not pipelinekit init
✓ verify-blueprint-001.ps1 has env var preflight guard
✓ PK-CONFIG-006 added to Error-Codes.md
✓ pytest passes — all tests green
✓ coverage >= 80%
✓ ruff, black, mypy clean
✓ PROJECT-STATUS.md untouched
```

---

## Stop and Ask Before

- Touching any file outside the allowed-modify list
- Making real database connections in tests
- Importing dlt outside adapters/ingestion/dlt/adapter.py
- Touching PROJECT-STATUS.md
- Changing any existing test

---

## Commit Message

```
feat: Sprint 6-2a — dlt adapter completion + credential wiring (ADR-017)

- src/pipelinekit/config/schema.py — SourceConfig extended with credential fields
- src/pipelinekit/config/loader.py — ${VAR} env interpolation before validation
- src/pipelinekit/adapters/ingestion/dlt/adapter.py — real sql_database source,
  Postgres conn string, Snowflake credentials from PipelineConfig
- scripts/verify-blueprint-001.ps1 — harness fixed (example config, preflight guard)
- docs/reference/Error-Codes.md — PK-CONFIG-006 added

ADR-017 satisfied. Blueprint #001 dry-run now exercises real dlt connectivity.
pipelinekit.yaml is the single source of credential truth.
```
