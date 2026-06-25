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
└── ArchitectureError    PK-ARCH-*        (Phase 5)
```

All errors carry structured code, message, and context dict.
Never raise bare exceptions. Never use free-form error strings.
