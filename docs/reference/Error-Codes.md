# PipelineKit Error Codes

## Format

PK-[AREA]-[NUMBER]

## Areas

CONFIG · CONTRACT · RUNTIME · ADAPTER · AI · STATE · BLUEPRINT · NOTIFY

## Phase 1 Registry — Foundation

### CONFIG

| Code | Meaning |
|---|---|
| PK-CONFIG-001 | pipelinekit.yaml fails Pydantic schema validation |
| PK-CONFIG-002 | Required section missing from config |
| PK-CONFIG-003 | pipelinekit.yaml not found in cwd |
| PK-CONFIG-004 | pipelinekit.yaml is not valid YAML |
| PK-CONFIG-005 | Failed to write pipelinekit.yaml |
| PK-CONFIG-006 | Required credential field empty after env var interpolation |

### STATE

| Code | Meaning |
|---|---|
| PK-STATE-001 | Cannot open or create state.db |
| PK-STATE-002 | Cannot write to state database |
| PK-STATE-003 | State schema is corrupted or incompatible |

---

## Phase 2 Registry — Data Layer

### RUNTIME

| Code | Meaning |
|---|---|
| PK-RUNTIME-001 | Pipeline execution failed (general) |
| PK-RUNTIME-002 | Provider initialization failed |
| PK-RUNTIME-003 | Pipeline already running (state conflict) |

### ADAPTER

| Code | Meaning |
|---|---|
| PK-ADAPTER-001 | Adapter connection failed |
| PK-ADAPTER-002 | Adapter execution failed |
| PK-ADAPTER-003 | Adapter returned invalid result |

### CONTRACT

| Code | Meaning |
|---|---|
| PK-CONTRACT-001 | Required column missing from table |
| PK-CONTRACT-002 | Freshness SLA violated |
| PK-CONTRACT-003 | Uniqueness constraint violated |
| PK-CONTRACT-004 | Not-null constraint violated |
| PK-CONTRACT-005 | Accepted-values constraint violated |
| PK-CONTRACT-006 | Row count outside expected range |
| PK-CONTRACT-007 | Contract file not found for table |
| PK-CONTRACT-008 | Contract file is invalid YAML or schema |

### DC — Contract Schema Versioning (DC-8, SPEC-020)

| Code | Meaning |
|---|---|
| PK-DC-008 | Contract version not found — `--diff` references a version that does not exist. Fix: run `pipelinekit contract version --history` to see available versions. |
| PK-DC-009 | Version format invalid — version string does not match MAJOR.MINOR.PATCH. Fix: use semantic version format, e.g. `v1.0.0` or `1.0.0`. |
| PK-DC-010 | State database error during snapshot — `state.db` write failed during contract snapshot. Fix: check disk space and `state.db` file permissions. |
| PK-DC-011 | Breaking change blocked — contract snapshot would produce a MAJOR version bump. The snapshot was blocked to prevent unacknowledged breaking changes. Fix: review the breaking changes listed above, then re-run with `--force`. |
| PK-DC-012 | No consumers registered — no consumers are watching this blueprint/table combination. This is informational, not an error, when no consumers have been set up yet. Fix: run `pipelinekit contract consumer add` to register consumers. |

DC-8 versioning codes are carried by `ContractError` (PK-DC-008/009) and
`StateError` (PK-DC-010). DC-9 (SPEC-021) surfaces `PK-DC-011` in the
`contract snapshot` warning block when a MAJOR bump is blocked without `--force`.
DC-10 (SPEC-027) registers contract consumers (`dc_consumers`) and records change
notifications (`dc_notifications`) when a breaking change is accepted with
`--force`. `PK-DC-012` is informational only — `create_notifications` returning
no records (no consumers watching the table) is never raised as an error.

### QM — Quality Management (QM-4, SPEC-022)

| Code | Meaning |
|---|---|
| PK-QM-001 | No blueprints found for coverage scan — no installed blueprints were found in the blueprints directory. Fix: run `pipelinekit blueprint install <name>` first. |
| PK-QM-002 | Schema file parse error — a `schema.yml` file could not be parsed as valid YAML. Fix: check the file for YAML syntax errors. |
| PK-QM-003 | Volume anomaly detected — row count deviates significantly from the established baseline. Possible causes: missing partition, failed extraction, truncated load, duplicate rows loaded, or source data issue. Fix: investigate the pipeline run logs for the affected table. |
| PK-QM-004 | Schema drift detected — the `schema.yml` column definitions diverge from the contract snapshot. Fix: run `pipelinekit contract snapshot` to update the contract, or update the `schema.yml` to match the contract. |

QM-4 quality-coverage codes are carried by `QualityError` (read-only scanning;
no `state.db` writes). QM-6 (SPEC-024) adds `PK-QM-003`, surfaced by
`pipelinekit quality check-anomalies` when a recorded row count deviates beyond
the threshold; the command exits 1 so it is script-detectable. Row-count
snapshots are stored in the `qm_row_counts` table (`state.db`). QM-7 (SPEC-029)
adds `PK-QM-004`, surfaced by `pipelinekit quality check-drift` when a dbt
`schema.yml` model's columns diverge from its contract snapshot; the command
exits 1 on drift. Drift detection is read-only — it adds no `state.db` tables and
reports `NO_BASELINE` (never an error) when no contract snapshot exists.

### GM — Governance Management (GM-1, SPEC-023)

| Code | Meaning |
|---|---|
| PK-GM-001 | Blueprint not found — the specified blueprint is not installed. Fix: run `pipelinekit blueprint list` to see installed blueprints, then `pipelinekit blueprint install <name>` to install. |
| PK-GM-002 | Invalid email address — the owner email is not valid. Fix: provide a valid email address (must contain `@` and a domain with a dot). |
| PK-GM-003 | Invalid convention scope — the scope must be one of: `blueprint`, `table`, `column`, `contract_file`. Fix: use a valid scope. |
| PK-GM-004 | Invalid regex pattern — the pattern is not valid Python regex syntax. Fix: test your pattern (e.g. at regex101.com) before adding. |
| PK-GM-005 | Approval request not found — no approval request exists with the given request code. Fix: run `pipelinekit governance approval list` to see valid codes. |
| PK-GM-006 | Request already decided — this approval request has already been approved or rejected. Fix: check status with `pipelinekit governance approval list`. |

GM-1 governance codes are carried by `GovernanceError`. Ownership is stored in
the `gm_owners` table; missing ownership is surfaced as a warning (never a
failure) by the `ownership` health check. GM-2 (SPEC-028) adds naming convention
enforcement in the `gm_conventions` table; `PK-GM-003` and `PK-GM-004` are raised
by `convention add`. Convention violations are surfaced as warnings by
`pipelinekit governance convention check` (which exits 1 on any violation) and
never block pipeline execution. GM-3 (SPEC-031) adds a record-only approval
workflow (`gm_approvers`, `gm_approval_requests`); `PK-GM-005` and `PK-GM-006` are
raised by `approval approve`/`approval reject`. Approval records are audit
evidence (SOC 2 CC8) and never block pipeline execution.

### OM — Observability Management (OM-4, SPEC-025)

| Code | Meaning |
|---|---|
| PK-OM-001 | SLO violated — a pipeline Service Level Objective threshold was not met during evaluation. Fix: investigate the pipeline — check freshness, row counts, or coverage for the affected table. |
| PK-OM-002 | Invalid SLO type — the SLO type must be one of: `freshness`, `row_count`, `coverage`. Fix: use a valid SLO type. |

OM-4 defines SLOs in the `om_slos` table and evaluates them against existing DC
(freshness), QM (row count), and coverage data. `PK-OM-002` is carried by
`ObservabilityError` (raised for an invalid type). `PK-OM-001` is **never
raised** — it is surfaced as warning text by `pipelinekit observability slo
check` (which exits 1 on any violation) and in `pipelinekit health --strict`.
A missing data source yields `NO_DATA`, never a failure.

### AM — Architecture Management (AM-4, SPEC-026)

| Code | Meaning |
|---|---|
| PK-AM-001 | Blueprint not found — one or both blueprints in the dependency are not installed. Fix: run `pipelinekit blueprint list` to see installed blueprints. |
| PK-AM-002 | Invalid dependency type — the dependency type must be one of: `contract`, `dbt_source`, `manual`. Fix: use a valid dependency type. |

AM-4 maps blueprint dependencies in the `am_dependencies` table by statically
reading contract, `sources.yml`, and `blueprint.json` files. `PK-AM-001` and
`PK-AM-002` are carried by `ArchitectureError` (raised by `dependency add`).
Auto-detection returning no edges is a valid result — the current blueprints are
independent pipelines.

---

## Phase 3 Registry — Trust Layer

### BLUEPRINT

| Code | Meaning |
|---|---|
| PK-BLUEPRINT-001 | blueprint.json fails schema validation |
| PK-BLUEPRINT-002 | blueprint.json not found |
| PK-BLUEPRINT-003 | Blueprint directory not found |
| PK-BLUEPRINT-004 | Blueprint dbt project invalid |

### NOTIFY

| Code | Meaning |
|---|---|
| PK-NOTIFY-001 | Notification provider unavailable |
| PK-NOTIFY-002 | Notification delivery failed |
| PK-NOTIFY-003 | Notification target not configured (Resend: recipient empty; Slack: webhook URL not set) |
| PK-NOTIFY-004 | Notification auth/transport failure (Resend: API key missing/invalid; Slack: webhook request failed) |

These notify codes are shared across alert adapters. The Resend (email) and Slack
(incoming webhook) adapters both raise `PK-NOTIFY-003` when their destination is
not configured and `PK-NOTIFY-004` for an auth/transport failure. Adapter `send()`
never raises — failures are returned as a `NotificationResult(sent=False)` carrying
the code, and a broken channel never blocks pipeline state recording (SPEC-008).

---

## Phase 4 Registry — Intelligence Layer

### AI

| Code | Meaning |
|---|---|
| PK-AI-001 | AI provider unavailable (missing key / unreachable). Also raised by the provider cascade as **all providers exhausted** — every provider in the cascade failed or was skipped. Fix: check API keys and network; run `pipelinekit health --strict`. |
| PK-AI-002 | AI response failed schema validation |
| PK-AI-003 | AI confidence below threshold |

The provider cascade (AI-6 update, ADR-042) reuses `PK-AI-001` for exhaustion via
`CascadeExhaustedError` (a subclass of `LLMError`) — including the case where the
prompt exceeds every configured provider's context window (add a larger-context
provider such as `kimi`/`moonshot-v1-128k`). No new AI error code is introduced;
`PK-AI-002` keeps its existing "response failed schema validation" meaning.

### DIAG

| Code | Meaning |
|---|---|
| PK-DIAG-001 | Run ID not found in state.db |
| PK-DIAG-002 | Evidence collection failed |
| PK-DIAG-003 | Diagnosis engine initialization failed |

---

## Phase 5 Registry — Architecture Layer

### ARCH

| Code | Meaning |
|---|---|
| PK-ARCH-001 | Architecture context collection failed |
| PK-ARCH-002 | Architecture result failed schema validation |
| PK-ARCH-003 | ADR parsing failed |
| PK-ARCH-004 | Insufficient run history for analysis (< 5 runs) |

Architecture schema-validation failures surface as `PK-AI-002` at the engine
trust boundary (shared with Phase 4); `PK-ARCH-002` is reserved for the SPEC-011
contract. `ArchitectureError` carries the `PK-ARCH-*` codes.

---

## Phase 6 Registry — Catalog + Ecosystem

### HEALTH

| Code | Meaning |
|---|---|
| PK-HEALTH-001 | Dependency check failed (poetry unavailable) |
| PK-HEALTH-002 | Security check failed (pip-audit error) |
| PK-HEALTH-003 | Blueprint validation failed |
| PK-HEALTH-004 | SPEC drift detected |

`HealthError` carries the `PK-HEALTH-*` codes. Health checks are non-blocking:
a missing tool resolves to an `info` result rather than raising.

---

### GEN — AI Blueprint Proposal (Sprint 6-5)

| Code | Meaning |
|---|---|
| PK-GEN-001 | Proposal failed — AI provider error / invalid JSON |
| PK-GEN-002 | Proposed plan failed schema validation |
| PK-GEN-003 | Apply failed — no assets in approved state |
| PK-GEN-004 | Blueprint directory already exists |
| PK-GEN-005 | Proposed blueprint.json failed schema validation |
| PK-GEN-006 | Source or destination type not supported by adapter registry |
| PK-GEN-007 | Asset state transition violation |

`ProposalError` carries the `PK-GEN-*` codes. AI proposes; a human approves;
`apply()` writes (ADR-018). `can_auto_apply` is always False.

---

### REGISTRY — Remote Blueprint Registry (Sprint 6-6)

| Code | Meaning |
|---|---|
| PK-REGISTRY-001 | Registry unreachable — network error (and no cache) |
| PK-REGISTRY-002 | Blueprint validation failed — schema or missing assets |
| PK-REGISTRY-003 | Blueprint already installed — use --force to overwrite |
| PK-REGISTRY-004 | Blueprint not found in catalog |
| PK-REGISTRY-005 | Version not found in catalog |
| PK-REGISTRY-006 | Blueprint already at latest version (upgrade) |
| PK-REGISTRY-007 | No backup found for rollback |

`RegistryError` carries the `PK-REGISTRY-*` codes. Every installed blueprint is
schema-validated and asset-checked before any write (ADR-019); offline, a cached
catalog is used when present.

---

### MIGRATE — Migration Intelligence (Sprint 6-7)

| Code | Meaning |
|---|---|
| PK-MIGRATE-001 | Config file not found |
| PK-MIGRATE-002 | Config format not recognized |
| PK-MIGRATE-003 | Blocking gaps exist — use --force to apply anyway |
| PK-MIGRATE-004 | AI analysis failed (invalid response) |
| PK-MIGRATE-005 | Python file parsing failed (syntax error) |

`MigrationError` carries the `PK-MIGRATE-*` codes. AI reads existing configs and
proposes — a human approves — `apply()` writes `pipelinekit.proposed.yaml` (never
`pipelinekit.yaml`). Parsing is deterministic and never executes the source file;
the Python parser uses `ast.parse()` only. `can_auto_apply` is always False
(ADR-020).

---

## Error Class Hierarchy

```python
PipelineKitError(code, message, context)
├── ConfigurationError   PK-CONFIG-*
├── StateError           PK-STATE-*
├── RuntimeError         PK-RUNTIME-*
├── ContractError        PK-CONTRACT-*
├── BlueprintError       PK-BLUEPRINT-*
├── NotificationError    PK-NOTIFY-*      (use PipelineKitError directly for now)
├── AIError              PK-AI-*          (Phase 4)
├── ArchitectureError    PK-ARCH-*        (Phase 5)
├── HealthError          PK-HEALTH-*      (Phase 6)
├── ProposalError        PK-GEN-*         (Phase 6 — Sprint 6-5)
├── RegistryError        PK-REGISTRY-*    (Phase 6 — Sprint 6-6)
└── MigrationError       PK-MIGRATE-*     (Phase 6 — Sprint 6-7)
```

All errors carry structured code, message, and context dict.
Never raise bare exceptions. Never use free-form error strings.
