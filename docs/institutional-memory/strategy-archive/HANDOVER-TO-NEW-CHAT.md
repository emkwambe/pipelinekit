# PipelineKit — Handover Summary v2
## For the Next Claude Chat Session

**Written by:** Command Center (Claude Chat, June 25, 2026)  
**Repository:** https://github.com/emkwambe/pipelinekit  
**Raw URL:** https://raw.githubusercontent.com/emkwambe/pipelinekit/main/docs/institutional-memory/strategy-archive/HANDOVER-TO-NEW-CHAT.md  
**Main branch HEAD:** `3d7e143`  
**Local path:** C:\Users\HP\Documents\pipelinekit

---

## Your Role

You are the **Command Center** — strategy, SPECs, sprint prompts, PROJECT-STATUS.  
You write no code. You own exactly one file: `docs/reference/PROJECT-STATUS.md`.  
Update it only after a phase is fully verified and pushed to main. Never during a sprint.

**The trio:**
```
Command Center (Claude Chat) — strategy, architecture, SPECs, sprint prompts
Claude Code                  — implementation, testing, commits
Eddy (Founder)               — verification, PowerShell, final commit authority
```

---

## Governing Principle — Immutable

> **PipelineKit is the AI-native operating system for trusted analytics pipelines.**

Every decision traces to this or does not get made.

---

## Current Build State

| Phase | Status | Tests | Coverage | Commit |
|---|---|---|---|---|
| Phase 1 — Foundation | ✅ Complete | 36 | 92.65% | 8d8865f |
| Phase 2 — Data Layer | ✅ Complete | 87 | 84.70% | f337cfe |
| Phase 3 — Trust Layer | ✅ Complete | 112 | 82.00% | d938e50 |
| Phase 4 — Intelligence | ⏳ Next | — | — | — |
| Phase 5 — Architecture | 📋 Named | — | — | — |

**All housekeeping complete. Phase 4 gate fully cleared.**

---

## Read These First — In Order

```
1.  docs/reference/PROJECT-STATUS.md
2.  docs/institutional-memory/strategy-archive/PIPELINEKIT-MASTER-ARCHITECTURE.md
3.  docs/constitution/Product-Constitution.md
4.  docs/decisions/ADR-000-Foundational-Architecture-Decisions.md
5.  docs/decisions/ADR-007-* (AI is Operator not Owner)
6.  docs/decisions/ADR-014-AI-Provider-MCP-Layer.md   ← NEW — read before SPEC-005
7.  docs/specifications/SPEC-005-AI-Diagnostics.md    ← NEW — full spec, ready
8.  docs/reference/Architectural-Smells.md            ← 16 smells with direction
9.  .claude/CLAUDE.md                                 ← v3, TTTD dimensions
10. schemas/diagnostic.schema.json                    ← authoritative AI output contract
11. docs/ai/PIPELINEKIT-AI & Model Strategy Standard.md
```

---

## Phase 4 — What to Build Next

SPEC-005 and ADR-014 are complete and committed. The sprint prompt is the next task.

**What Claude Code will build:**
```
src/pipelinekit/ai/
├── provider.py          LLMProvider Protocol
├── evidence.py          EvidenceCollector + EvidencePackage
├── models.py            DiagnosticResult, RecommendedAction
├── diagnostics.py       DiagnosticsEngine
└── providers/
    ├── openai.py
    ├── anthropic.py
    └── ollama.py

src/pipelinekit/cli/
└── diagnose.py          pipelinekit diagnose command

tests/ai/               All mocked — no real API calls
```

**Critical constraint — AI boundary (ADR-007 + Smell 13):**
- AI may: inspect, diagnose, recommend, summarize
- AI may not: execute, modify production, auto-fix
- `can_auto_fix` is always `False` in Phase 4
- All AI output validates against `schemas/diagnostic.schema.json`

**Three providers:** Anthropic (default), OpenAI, Ollama (local/air-gapped)  
**BYOK:** `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OLLAMA_HOST`  
**No MCPs for AI in Phase 4** — direct API calls. MCP deferred to Phase 5.

**New error codes needed:**
```
PK-AI-001    AI provider unavailable
PK-AI-002    AI response failed schema validation
PK-AI-003    AI confidence below threshold
PK-DIAG-001  Run ID not found in state.db
PK-DIAG-002  Evidence collection failed
PK-DIAG-003  Diagnostics engine initialization failed
```

**New error classes for core/errors.py:**
```python
class DiagnosticsError(PipelineKitError): ...
class LLMError(PipelineKitError): ...
```

---

## The Workflow Sequence

```
Step 1:  Command Center runs pre-flight (16 smells checklist)
Step 2:  Command Center writes Phase 4 session opener (Message 1)
Step 3:  Command Center writes Phase 4 sprint prompt (Message 2)
Step 4:  Eddy commits prompts to strategy-archive/
Step 5:  Eddy fires Claude Code — Message 1, wait for confirmation, Message 2
Step 6:  Claude Code builds on feature/phase-4-intelligence branch
Step 7:  Eddy verifies locally, Claude Code merges to main
Step 8:  Eddy confirms push, Command Center produces PROJECT-STATUS v4
Step 9:  Eddy commits PROJECT-STATUS — Phase 4 officially closed
```

---

## Pre-Flight Smells Check — Phase 4

Run before writing the sprint prompt:

```
Smell 1  — Untraceable Feature         □ traces to Constitution → ADR-007 → SPEC-005
Smell 2  — Provider leak               □ openai/anthropic/ollama isolated in ai/providers/
Smell 3  — Agent boundary              □ diagnostics-engineer owns ai/, cli/diagnose.py
Smell 4  — Spec drift                  □ SPEC-005 written before implementation
Smell 5  — Contract version            □ no contract changes in Phase 4
Smell 6  — Prompt-driven arch          □ ADR-014 committed before sprint
Smell 7  — MCP without ADR            □ No MCP in Phase 4 AI — direct API calls
Smell 8  — Single-impl abstraction    □ LLMProvider serves 3 implementations
Smell 9  — Placeholder inflation       □ SPEC-005 status: Approved
Smell 10 — Customer capability        □ customer can diagnose pipeline failures
Smell 11 — Capability creep           □ within intelligence layer boundary
Smell 12 — Trust regression           □ schema validation increases trust
Smell 13 — Observer becomes actor     □ can_auto_fix=False, no auto-execution
Smell 14 — State orphan               □ diagnostic results recorded in state.db
Smell 15 — Blueprint shortcut         □ not applicable Phase 4
Smell 16 — Control plane inversion    □ LLMProvider protocol, not concrete imports
```

All 16 green for Phase 4. Sprint prompt is cleared to write.

---

## Key Architectural Decisions — Never Reverse

1. CLI → Runtime → Adapter boundary — never cross it
2. Provider imports isolated in adapter files
3. Contracts define truth, AI interprets
4. AI may diagnose, never act autonomously (ADR-007)
5. Every MCP requires an ADR
6. Schema validation mandatory — trust boundary
7. TTTD dimensions are design principles, not benchmarks
8. Governing principle is immutable

---

## Strategic Context

**Post-dbt/Fivetran merger positioning:**
- PipelineKit = intelligence layer above the stack, not another tool in it
- "AI-native engineering" not "using AI"
- "Intelligence layer" not "control plane"
- Phase 5 = Architecture Intelligence ("what architecture should I use?")

**ICP-004 Mixed-Stack Enterprise** — largest revenue opportunity, runs 3+ heterogeneous tools, needs a control plane above them.

---

## What Would Let This Project Down

1. Writing sprint prompt without reading SPEC-005 and ADR-014 first
2. Skipping the 16-smell pre-flight
3. Touching PROJECT-STATUS.md during a sprint
4. Allowing AI boundary to blur — `can_auto_fix=True` requires ADR-016
5. Adding an MCP without an ADR
6. Provider imports leaking outside `ai/providers/`
7. Claiming TTTD metrics without real customer data

---

## Past Chat Search Terms

If you need to reconstruct reasoning from prior sessions:

- "PipelineKit" — all strategic discussions
- "diagnostic.schema.json" — AI output contract reasoning  
- "Observer Becomes Actor" — AI safety boundary discussion
- "TTTD dimensions" — why they are principles not metrics
- "control plane" — why we moved to "intelligence layer"
- "dbt Fivetran merger" — strategic repositioning
- "blind spot" — 7 architectural risks discussion
- "ICP-004" — Mixed-Stack Enterprise reasoning
- "SPEC-005" — full AI diagnostics spec reasoning

---

*The creed: PipelineKit is the AI-native operating system for trusted analytics pipelines.*  
*Everything else serves that sentence.*
