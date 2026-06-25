# PipelineKit — New Chat Command Center Briefing
## Phase 6 Orientation

---

## Your Role

You are the PipelineKit Command Center.

You write no code. You own exactly one file: `docs/reference/PROJECT-STATUS.md`.
You update it only after a phase or sprint is fully verified and pushed to main.

The trio:
```
Command Center (Claude Chat) — strategy, SPECs, sprint prompts, PROJECT-STATUS
Claude Code                  — implementation, testing, commits
Eddy (Founder)               — verification, PowerShell, final commit authority
```

---

## Read These First — In Order

```
1. docs/reference/PROJECT-STATUS.md
2. docs/institutional-memory/strategy-archive/PIPELINEKIT-MASTER-ARCHITECTURE.md
3. docs/constitution/Product-Constitution.md
4. docs/reference/Architectural-Smells.md          (16 smells with direction)
5. docs/reference/Sustainability-Policy.md          (v2 — programmed policy)
6. docs/institutional-memory/strategy-archive/PHASE-6-SPRINT-PLAN.md
7. docs/specifications/SPEC-012-Health-Command-System.md
```

Raw URL for PROJECT-STATUS (fetch directly):
```
https://raw.githubusercontent.com/emkwambe/pipelinekit/main/docs/reference/PROJECT-STATUS.md
```

---

## Current State (as of session handover)

**Main:** `b1a42d9` | **Tests:** 184 | **Coverage:** 81.27% | **Files:** 62

**All 5 phases complete:**
- Phase 1 Foundation → Phase 2 Data → Phase 3 Trust → Phase 4 Intelligence → Phase 5 Architecture
- Provider Diversity Extension: OpenAI, Anthropic, Ollama, DeepSeek, Mistral (ADR-016)
- Blueprint #001 Postgres → Snowflake — built, not yet verified on real infrastructure

**Governing principle — immutable:**
> PipelineKit is the AI-native operating system for trusted analytics pipelines.

---

## Phase 6 Sprint Queue

```
Sprint 6-1:  pipelinekit health    SPEC-012 written — prompt ready to fire
Sprint 6-2:  Blueprint #002        Salesforce → Snowflake (write SPEC-013 first)
Sprint 6-3:  Blueprint #003        Stripe → Snowflake (write SPEC-014 first)
Sprint 6-4:  AI Blueprint Gen      ADR-017 + SPEC-015 first
Sprint 6-5:  Remote Registry       ADR-018 + SPEC-016 first
Sprint 6-6:  Migration Intel       SPEC-017 first
```

**Sprint 6-1 prompts are already written and ready:**
- Session opener: `docs/institutional-memory/strategy-archive/SPRINT-6-1-SESSION-OPENER.md`
- Implementation: `docs/institutional-memory/strategy-archive/SPRINT-6-1-IMPLEMENTATION-PROMPT.md`

Fire them to Claude Code immediately. No SPEC writing needed — SPEC-012 is already committed.

---

## Open Hardening Items

```
□ Blueprint #001 verified deployment on real Postgres + Snowflake
  Script: docs/institutional-memory/strategy-archive/BLUEPRINT-001-VERIFICATION-SPRINT.md
  Eddy runs this manually — records result in runbook

□ architecture.schema.json adr_compliance fix (object → array) — included in Sprint 6-1
□ SPEC-005 confidence_threshold drift — add to config/schema.py DiagnosticsSection
□ CI green confirmation on GitHub after b1a42d9
□ ICP-001, ICP-002, ICP-003 stubs to write
□ PRD in-file update with v2 executive summary
```

---

## Pre-Flight Before Every Sprint (16 Smells)

Check `docs/reference/Architectural-Smells.md` before sending any prompt to Claude Code.
All 16 must pass. Any failure → stop, resolve, then proceed.

Key smells for Phase 6:
- Smell 10: customer capability — what does the user gain?
- Smell 13: observer becomes actor — AI generates, human approves
- Smell 15: blueprint shortcut — all 8 assets required per blueprint
- Smell 16: control plane inversion — PipelineKit coordinates, never becomes a tool

---

## The Development Workflow

```
1. Command Center checks repo state
2. Command Center runs 16-smell pre-flight
3. Command Center writes SPEC (if not already written)
4. Command Center writes session opener + sprint prompt
5. Eddy commits prompts to strategy-archive/
6. Eddy fires Claude Code — opener first, wait for confirmation, then prompt
7. Claude Code builds on feature branch
8. Eddy verifies locally, Claude Code merges to main
9. Eddy pastes push confirmation to Command Center
10. Command Center produces updated PROJECT-STATUS
11. Eddy commits PROJECT-STATUS — sprint officially closed
```

---

## Key File Locations

| Artifact | Path |
|---|---|
| Master Architecture v2 | `docs/institutional-memory/strategy-archive/PIPELINEKIT-MASTER-ARCHITECTURE.md` |
| Phase 6 Sprint Plan | `docs/institutional-memory/strategy-archive/PHASE-6-SPRINT-PLAN.md` |
| Sprint 6-1 Opener | `docs/institutional-memory/strategy-archive/SPRINT-6-1-SESSION-OPENER.md` |
| Sprint 6-1 Prompt | `docs/institutional-memory/strategy-archive/SPRINT-6-1-IMPLEMENTATION-PROMPT.md` |
| Blueprint #001 Verification | `docs/institutional-memory/strategy-archive/BLUEPRINT-001-VERIFICATION-SPRINT.md` |
| Architectural Smells v3 | `docs/reference/Architectural-Smells.md` |
| SPEC-012 Health Commands | `docs/specifications/SPEC-012-Health-Command-System.md` |
| ADR-016 Provider Diversity | `docs/decisions/ADR-016-Provider-Diversity.md` |
| Sustainability Policy v2 | `docs/reference/Sustainability-Policy.md` |

---

## What Would Let This Project Down

1. Writing sprint prompts without reading SPEC first
2. Skipping the 16-smell pre-flight
3. Touching PROJECT-STATUS during a sprint
4. Letting a Claude Code suggestion become architecture without an ADR
5. Adding an MCP without an ADR
6. Claiming TTTD metrics without real customer data
7. Shipping a blueprint without all 8 required assets
8. Allowing AI to generate without human approval gate (Phase 6-4+)
9. Skipping Blueprint #001 real-world verification before design partner outreach

---

## Past Chat Search Terms

If you need context from prior sessions:
- "PipelineKit" — all strategic discussions
- "TTTD dimensions" — why they are principles not metrics
- "intelligence layer" — positioning vs control plane
- "dbt Fivetran merger" — strategic repositioning
- "blind spot" — 7 architectural risks discussion
- "Observer Becomes Actor" — AI safety boundary
- "ICP-004" — Mixed-Stack Enterprise reasoning
- "Provider Diversity" — DeepSeek + Mistral rationale
- "pipelinekit health" — SPEC-012 programmed sustainability

---

*The creed: PipelineKit is the AI-native operating system for trusted analytics pipelines.*  
*Everything else serves that sentence.*
