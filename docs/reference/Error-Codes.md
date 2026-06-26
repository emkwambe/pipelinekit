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
| PK-NOTIFY-003 | Invalid recipient address |
| PK-NOTIFY-004 | API key missing or invalid |

---

## Phase 4 Registry — Intelligence Layer

### AI

| Code | Meaning |
|---|---|
| PK-AI-001 | AI provider unavailable (missing key / unreachable) |
| PK-AI-002 | AI response failed schema validation |
| PK-AI-003 | AI confidence below threshold |

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
└── ProposalError        PK-GEN-*         (Phase 6 — Sprint 6-5)
```

All errors carry structured code, message, and context dict.
Never raise bare exceptions. Never use free-form error strings.
