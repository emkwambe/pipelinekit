# ADR-017: dlt Credential Integration Policy

**Status:** Accepted  
**Date:** June 25, 2026  
**Phase:** 6 — Blueprint Catalog (Sprint 6-2a)  
**ADR Number:** 017  
**Governs:** `src/pipelinekit/adapters/ingestion/dlt/adapter.py`, `src/pipelinekit/config/schema.py`, `pipelinekit.yaml` credential fields

---

## Context

The Blueprint #001 diagnostic run (June 25, 2026) revealed that the dlt ingestion adapter is a Phase 2 scaffold. `_source_rows()` returns `[]`, no real SQL source is built, and no credential wiring exists between `pipelinekit.yaml` and dlt's configuration system.

This created a fundamental architectural question that must be decided before any dlt adapter work proceeds:

> **Does PipelineKit pass credentials into dlt from `pipelinekit.yaml`, or does it adopt dlt's own secrets.toml/environment variable convention as the BYOK boundary?**

The diagnostic run also revealed a secondary gap: `pipelinekit.yaml` config values like `host: "${PG_HOST}"` are passed literally as strings — the loader does not interpolate environment variables.

---

## Decision

**PipelineKit owns credential configuration. `pipelinekit.yaml` is the single source of truth.**

`SourceConfig` is extended with first-class credential fields. The dlt adapter reads from `PipelineConfig` and translates into dlt's credential objects. `pipelinekit validate` catches missing or invalid credentials before pipeline execution. Environment variable interpolation is added to the config loader.

This is Position A.

---

## Why Position A Over Position B

**Position B (dlt owns credentials)** would mean users maintain two separate credential systems: `pipelinekit.yaml` for structural config and `.dlt/secrets.toml` or dlt env vars for credentials. This:

- Creates two places to look when something fails
- Makes `pipelinekit validate` incomplete — it cannot validate what it cannot see
- Means PipelineKit is a thin wrapper around dlt rather than an operating layer above it
- Violates Smell 16 (Control Plane Inversion) — the tool starts dictating how PipelineKit behaves

**Position A** is consistent with the governing principle: one operating model, one config file, one place to look. PipelineKit orchestrates dlt — it does not defer to dlt's config system.

---

## What Changes

### 1. src/pipelinekit/config/schema.py — SourceConfig extension

```python
class SourceConfig(BaseModel):
    type: str
    # Postgres
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    tables: Optional[list[str]] = None
    # Snowflake
    account: Optional[str] = None
    warehouse: Optional[str] = None
    schema_: Optional[str] = Field(None, alias="schema")
    # BigQuery
    project: Optional[str] = None
    # DuckDB
    path: Optional[str] = None
```

### 2. src/pipelinekit/config/loader.py — Environment variable interpolation

`load_config()` must expand `${VAR}` patterns before Pydantic validation:

```python
import os, re

def _interpolate_env_vars(value: str) -> str:
    """Replace ${VAR} with os.environ.get(VAR, '')."""
    return re.sub(
        r'\$\{([^}]+)\}',
        lambda m: os.environ.get(m.group(1), ''),
        value
    )
```

Apply recursively to all string values in the loaded YAML dict before passing to `PipelineConfig`.

### 3. src/pipelinekit/adapters/ingestion/dlt/adapter.py — Complete the adapter

The adapter must:
- Build a real `sql_database` dlt source from `SourceConfig` (Postgres)
- Translate `SourceConfig` fields into dlt `ConnectionStringCredentials`
- Execute the dlt pipeline against the configured destination
- Return `StepResult` with actual `rows_processed` count

dlt credential wiring:

```python
# Postgres source
from dlt.sources.sql_database import sql_database

conn_str = (
    f"postgresql://{config.source.user}:{config.source.password}"
    f"@{config.source.host}:{config.source.port}/{config.source.database}"
)
source = sql_database(conn_str).with_resources(*config.source.tables)

# Snowflake destination — dlt ConnectionStringCredentials
from dlt.destinations.impl.snowflake.snowflake import SnowflakeCredentials

credentials = SnowflakeCredentials(
    account=config.destination.account,
    user=config.destination.user,
    password=config.destination.password,
    database=config.destination.database,
    warehouse=config.destination.warehouse,
)
```

### 4. pipelinekit.yaml default — Fix contracts.directory

`write_default_config()` must write:
```yaml
contracts:
  enabled: true
  directory: ./contracts
```

When used with a blueprint, the user sets this to the blueprint's contracts directory. The verification harness must copy `pipelinekit.example.yaml` — not run `pipelinekit init` — to use Blueprint #001's config.

### 5. scripts/verify-blueprint-001.ps1 — Fix harness

The verification script must:
1. Copy `pipelinekit.example.yaml` → `pipelinekit.yaml` (not run `pipelinekit init`)
2. Set `contracts.directory` to `./blueprints/postgres-to-snowflake/contracts`
3. Add env var preflight guard — fail early with clear message if required vars not set

---

## BYOK Application (ADR-005)

Credentials remain customer-provided. The mechanism changes — from dlt's env var convention to `pipelinekit.yaml` fields with `${VAR}` interpolation. The customer still provides credentials via environment variables. PipelineKit reads them through the config loader, not directly from the environment.

This is BYOK compliant — PipelineKit never stores, logs, or transmits credentials.

---

## pipelinekit validate — Credential Validation

After this ADR is implemented, `pipelinekit validate` gains:

- Check that `${VAR}` interpolated values are non-empty for required credential fields
- New error code: `PK-CONFIG-006` — Required credential field empty after interpolation
- This makes `pipelinekit validate` a real pre-flight check, not just a schema check

---

## Error Codes Added

| Code | Meaning |
|---|---|
| `PK-CONFIG-006` | Required credential field empty after env var interpolation |

---

## Consequences

### Benefits
- `pipelinekit.yaml` is genuinely the single source of truth
- `pipelinekit validate` catches credential gaps before execution
- No `.dlt/secrets.toml` required — users do not need to learn dlt's config system
- Blueprint runbooks become simpler — one env var block, one config file

### Limitations
- Every dlt source type (Postgres, MySQL, REST API, Salesforce) needs credential mapping in the adapter
- Phase 2 dlt adapter must be completed — currently a scaffold
- `${VAR}` interpolation adds complexity to loader (minor)

### Sprint impact
- Sprint 6-2a: implement ADR-017 (this decision)
  - Extend SourceConfig
  - Add env var interpolation to loader
  - Complete dlt adapter (Postgres source + Snowflake/BigQuery destination)
  - Fix verification harness
  - Re-run Blueprint #001 verification
- Sprint 6-2b: Blueprint #002 Salesforce → Snowflake (after 6-2a passes)

---

## Principle Alignment

- ADR-005 (BYOK) — customer provides credentials via env vars; PipelineKit interpolates
- ADR-008 (Deterministic) — `pipelinekit validate` gives deterministic credential check
- ADR-009 (Human-Readable) — one config file, human-readable credential references
- Governing Principle — one operating model above the tool stack
- Smell 4 (Specification Drift) — SPEC-002 updated to reflect SourceConfig extension
- Smell 15 (Blueprint Shortcut) — Blueprint #001 cannot ship without working adapter
- Smell 16 (Control Plane Inversion) — PipelineKit passes credentials to dlt, not vice versa
