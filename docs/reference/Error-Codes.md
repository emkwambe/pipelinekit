# PipelineKit Error Codes

## Format

PK-[AREA]-[NUMBER]

## Areas

CONFIG

CONTRACT

RUNTIME

ADAPTER

AI

STATE

## Examples

PK-CONFIG-001

Invalid pipelinekit.yaml.

PK-CONTRACT-001

Required column missing.

PK-RUNTIME-001

Pipeline execution failed.

PK-AI-001

AI provider unavailable.

PK-STATE-001

State database unavailable.

## Phase 2 Registry — Data Layer

Added by the Data Layer sprint (runtime, adapters, contracts).

### CONFIG

| Code | Meaning |
|---|---|
| PK-CONFIG-005 | Failed to write pipelinekit.yaml |

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

### STATE

| Code | Meaning |
|---|---|
| PK-STATE-002 | Cannot write to state database |
