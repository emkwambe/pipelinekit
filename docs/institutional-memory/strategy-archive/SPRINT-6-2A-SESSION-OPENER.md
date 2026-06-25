# PipelineKit — Sprint 6-2a Session Opener

You are Claude Code working inside the PipelineKit repository.

## Repository

```
C:\Users\HP\Documents\pipelinekit
```

## Read First

```
1. .claude/CLAUDE.md
2. docs/reference/PROJECT-STATUS.md
3. docs/decisions/ADR-017-dlt-Credential-Integration.md   ← New — read completely
4. docs/specifications/SPEC-002-Configuration-System.md
5. docs/specifications/SPEC-003-Pipeline-Runtime.md
6. docs/specifications/SPEC-009-Provider-Adapters.md
7. src/pipelinekit/adapters/ingestion/dlt/adapter.py      ← What you complete
8. src/pipelinekit/config/schema.py                       ← What you extend
9. src/pipelinekit/config/loader.py                       ← What you extend
10. scripts/verify-blueprint-001.ps1                      ← What you fix
```

## Context

Blueprint #001 diagnostic run revealed the dlt ingestion adapter is a Phase 2 scaffold.
ADR-017 has been accepted — it defines exactly what to build.

This is a runtime-engineer sprint. You own:
- `src/pipelinekit/adapters/ingestion/dlt/adapter.py`
- `src/pipelinekit/config/schema.py` (SourceConfig extension only)
- `src/pipelinekit/config/loader.py` (env var interpolation only)
- `scripts/verify-blueprint-001.ps1` (harness fix only)

## Confirm Your Understanding Of

1. What ADR-017 decides and why Position A was chosen over Position B
2. What `_source_rows()` currently returns and why that is the core gap
3. What env var interpolation means and where it goes
4. What the verification harness fix requires
5. What must never be touched

Confirm when ready.
