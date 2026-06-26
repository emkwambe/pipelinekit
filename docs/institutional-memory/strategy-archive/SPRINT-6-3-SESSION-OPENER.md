# PipelineKit — Sprint 6-3 Session Opener
## Blueprint #002 — Salesforce → Snowflake

You are Claude Code working inside the PipelineKit repository.

## Repository

```
C:\Users\HP\Documents\pipelinekit
```

## Read First

```
1. .claude/CLAUDE.md
2. docs/reference/PROJECT-STATUS.md
3. docs/specifications/SPEC-013-Blueprint-002-Salesforce-Snowflake.md  ← Primary
4. docs/specifications/SPEC-006-Blueprint-Engine.md
5. blueprints/postgres-to-snowflake/blueprint.json                     ← Pattern
6. blueprints/postgres-to-snowflake/pipelinekit.example.yaml           ← Pattern
7. src/pipelinekit/config/schema.py                                    ← Extend
8. src/pipelinekit/adapters/ingestion/dlt/adapter.py                   ← Extend
9. docs/reference/Architectural-Smells.md                              ← Smell 15
```

## Context

Blueprint #001 (Postgres → Snowflake) is locally verified — 1,000 rows, 0.7 minutes.
Blueprint #002 follows the exact same 8-asset structure.
No new infrastructure needed — the blueprint engine, dlt adapter, and dbt profile pattern are all proven.

## Confirm Your Understanding Of

1. The 8 required assets and what each contains
2. What SourceConfig fields need to be added for Salesforce
3. How the dlt adapter handles a new source type
4. What Smell 15 (Blueprint Shortcut) means for this sprint
5. What files are READ ONLY

Confirm when ready.
