# PipelineKit — Sprint 6-5 Session Opener
## AI Blueprint Generation

You are Claude Code working inside the PipelineKit repository.

## Repository

```
C:\Users\HP\Documents\pipelinekit
```

## Read First — In This Exact Order

```
1.  .claude/CLAUDE.md
2.  docs/reference/PROJECT-STATUS.md
3.  docs/decisions/ADR-018-Blueprint-Generation-Governance.md  ← New — read completely
4.  docs/decisions/ADR-007-* (AI is Operator not Owner)
5.  docs/specifications/SPEC-015-AI-Blueprint-Generation.md    ← Primary SPEC
6.  docs/specifications/SPEC-005-AI-Diagnostics.md             ← LLMProvider pattern
7.  docs/specifications/SPEC-006-Blueprint-Engine.md           ← Blueprint pattern
8.  src/pipelinekit/ai/provider.py                             ← You extend this
9.  src/pipelinekit/ai/diagnostics.py                          ← Pattern to follow
10. blueprints/postgres-to-snowflake/                          ← Generation pattern source
11. blueprints/salesforce-to-snowflake/                        ← Generation pattern source
12. schemas/blueprint.schema.json                              ← Output must satisfy this
13. docs/reference/Architectural-Smells.md                     ← Especially Smell 13 + 15
```

## Context

Sprint 6-5 is the most architecturally significant sprint since Phase 4. This is the first time AI generates new artifacts in PipelineKit. ADR-018 governs the boundary precisely — AI proposes, human approves, only approved assets touch the filesystem.

## Confirm Your Understanding Of

1. What the "Plan then Apply" pattern means — specifically, when does anything touch the filesystem?
2. What `can_auto_apply = False` means in the context of generation (different from Phase 4/5)
3. The `GenerationPlan` data structure — what it contains and what it is NOT
4. Which existing blueprints the generator reads as patterns
5. What Smell 13 means when extended to generation (Observer Becomes Actor → Generator Becomes Actor)
6. What must never be touched

Confirm when ready. Do not write any code until confirmation is complete.
