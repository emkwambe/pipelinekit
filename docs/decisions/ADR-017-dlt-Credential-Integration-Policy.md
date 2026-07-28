# ADR-017 — dlt Credential Integration Policy

**Status:** Accepted
**Date:** June 25, 2026
**Deciders:** Eddy Mkwambe (Founder), Command Center
**Triggered by:** Blueprint #001 diagnostic run — dlt ConfigFieldMissingException
**Supersedes:** None
**Related:** ADR-001 (Adopt dlt), ADR-005 (BYOK), ADR-009 (Human-Readable Config)

---

## Context

Blueprint #001 diagnostic run revealed that dlt's Snowflake destination resolves
credentials via its own provider hierarchy:

1. Environment variables: `DESTINATION__SNOWFLAKE__CREDENTIALS__DATABASE`, `HOST`, etc.
2. `.dlt/secrets.toml`
3. `.dlt/config.toml`

PipelineKit's `pipelinekit.yaml` holds credentials as first-class fields
(`host`, `database`, `user`, `password`, `warehouse`). The dlt adapter
received a `PipelineConfig` object but passed no credentials into dlt —
forcing dlt to fall back to its own resolution, find nothing, and raise
`ConfigFieldMissingException`.

Two positions were evaluated:

**Position A — PipelineKit translates credentials into dlt format**
`pipelinekit.yaml` is the single source of truth. The dlt adapter reads
`SourceConfig` and `DestinationConfig`, constructs dlt-compatible credential
objects (`ConnectionStringCredentials`, `SnowflakeCredentials`), and injects
them into `dlt.pipeline()`. PipelineKit `validate` catches missing credentials
before any run attempt.

**Position B — dlt owns credential resolution**
PipelineKit orchestrates structure only. Users maintain dlt's own
`.dlt/secrets.toml` or its env var convention for credentials.
`pipelinekit.yaml` holds only structural config (source type, destination
type, tables). Two credential systems exist side by side.

---

## Decision

**Position A is adopted.**

PipelineKit translates credentials from `pipelinekit.yaml` into dlt's native
credential objects at the adapter boundary. Users configure credentials exactly
once, in `pipelinekit.yaml`. The dlt adapter is responsible for the translation.

---

## Rationale

**1. The governing principle requires it.**
PipelineKit is the AI-native operating system for trusted analytics pipelines.
An operating system presents a unified interface. Requiring users to maintain
both `pipelinekit.yaml` and `.dlt/secrets.toml` creates two credential systems —
violating the single-config promise of ADR-009.

**2. Position B is Smell 16 (Control Plane Inversion).**
If PipelineKit defers credential management to dlt, it becomes a thin wrapper
around dlt rather than an operating layer above it. The user's mental model
becomes "I need to understand dlt" rather than "I need to understand PipelineKit."
That is the wrong direction.

**3. Position A is consistent with ADR-005 (BYOK).**
BYOK means users bring their own keys — not that they manage multiple credential
formats. Under Position A, the user's key lives in `pipelinekit.yaml` (or an
env var referenced from it via `${VAR}` interpolation). PipelineKit handles
the rest.

**4. `pipelinekit validate` becomes the credential gate.**
Under Position A, a missing `user`, `password`, or `warehouse` is caught at
validate time — before dlt is ever invoked. Fail fast, fail clearly, fail at
the PipelineKit layer.

---

## Implementation Requirements

Implemented in Sprint 6-2a:

**1. `load_config` — env var interpolation**
`src/pipelinekit/config/loader.py` must expand `${VAR}` references in
`pipelinekit.yaml` values before constructing `PipelineConfig`.
Missing vars raise `PK-CONFIG-006`.

**2. `SourceConfig` — first-class credential fields**
Add `user: str | None`, `password: str | None`, `schema: str | None`.

**3. `DestinationConfig` — first-class credential fields**
Add `user: str | None`, `password: str | None`, `warehouse: str | None`,
`schema: str | None`.

**4. dlt ingestion adapter — credential translation**
`src/pipelinekit/adapters/ingestion/dlt/adapter.py`:
- `_source_rows()` builds a real `sql_database` dlt source from `SourceConfig`
  using `ConnectionStringCredentials` constructed from config fields.
- `execute()` constructs `SnowflakeCredentials` from `DestinationConfig` fields
  and passes them explicitly to `dlt.pipeline()`.
- No reliance on dlt's own env var resolution for credentials PipelineKit holds.

**5. `contracts.directory` default**
Default `pipelinekit.yaml` must set `contracts.directory: ./contracts`
relative to project root, not repo root.

**6. Error code**
Add `PK-CONFIG-006: Missing env var referenced in pipelinekit.yaml`.

---

## Boundary

dlt's `.dlt/secrets.toml` and env var convention remain valid for users who
invoke dlt directly. PipelineKit does not prohibit them. But PipelineKit
never requires them — all credentials PipelineKit needs flow through
`pipelinekit.yaml`.

---

## Consequences

**Positive:**
- Single config file — users never need to know dlt credential naming
- `pipelinekit validate` catches missing credentials before any run
- Blueprint #001 can complete its first verified deployment
- All future blueprints inherit correct credential handling automatically

**Negative:**
- The dlt adapter becomes slightly more complex (credential construction)
- Any future dlt destination requires a credential translator in the adapter

**Risks:**
- dlt credential object APIs may change across versions — pin dlt version
  in `pyproject.toml` and note in adapter comments