# PipelineKit — Phase 5 Claude Code Session Opener

You are Claude Code working inside the PipelineKit repository.

## Repository Location

```
C:\Users\HP\Documents\pipelinekit
```

## Before Anything Else

Read these files completely right now, in this order:

```
1. .claude/CLAUDE.md
2. agents/diagnostics-engineer/AGENT.md
3. agents/diagnostics-engineer/SYSTEM.md
4. docs/reference/PROJECT-STATUS.md
5. docs/decisions/ADR-015-Architecture-Intelligence.md
6. docs/specifications/SPEC-011-Architecture-Intelligence.md
7. schemas/blueprint.schema.json
8. src/pipelinekit/ai/provider.py
9. src/pipelinekit/ai/diagnostics.py
10. src/pipelinekit/ai/models.py
```

Items 5–10 are Phase 5 specific. Read them completely — SPEC-011 and ADR-015
define everything you build. The existing Phase 4 AI interfaces define exactly
what you extend.

## Your Environment

- Windows 11, PowerShell
- Python 3.13.7, Poetry 2.4.1
- Phases 1–4 complete — 151 tests at 82.16% coverage
- src/pipelinekit/ai/ exists with provider.py, diagnostics.py, models.py,
  evidence.py, and three providers

## What Is Coming Next

After you confirm all 10 files read, I will give you the Phase 5 brief.

Do not write any code yet.
Do not install anything yet.

Confirm your understanding of:

1. What Phase 5 builds and how it differs from Phase 4
2. The five Architecture Intelligence reasoning types
3. The new schema — what fields it requires beyond diagnostic.schema.json
4. How LLMProvider is extended — what the architect() method does
5. What can_auto_apply means and why it is always False in Phase 5
6. What must never be touched

Confirm when ready.
