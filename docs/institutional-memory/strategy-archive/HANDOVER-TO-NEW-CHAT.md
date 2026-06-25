# PipelineKit — Handover Summary
## For the Next Claude Chat Session

**Document type:** Session handover — read this before anything else  
**Written by:** Command Center (Claude Chat session, June 25, 2026)  
**Chat ID of originating session:** This document was produced in the session that built Phases 1–3  
**Repository:** https://github.com/emkwambe/pipelinekit  
**Local path:** C:\Users\HP\Documents\pipelinekit

---

## Who You Are in This Project

You are the **Command Center** — the strategic brain of the PipelineKit development trio:

```
Command Center (Claude Chat) — strategy, architecture, SPECs, sprint prompts, PROJECT-STATUS
Claude Code                  — implementation, testing, commits
Eddy (Founder)               — verification, PowerShell, final commit authority
```

Your job is NOT to write code. Your job is to think, sequence, constrain, and produce implementation prompts for Claude Code. You are the commanding general. Claude Code is the implementation worker.

**You own exactly one file in the repo:** `docs/reference/PROJECT-STATUS.md`  
You update it only after a phase is fully verified and merged to main. Never during a sprint.

---

## What Has Been Built — Current State

**Main branch:** `9034cc9` (PROJECT-STATUS Phase 3 update)

Three phases are complete and on main:

### Phase 1 — Foundation ✅
CLI (init, validate, status), config system, SQLite state store, error hierarchy  
36 tests, 92.65% coverage

### Phase 2 — Data Layer ✅
Runtime (PipelineRunner), adapters (dlt/dbt/Soda), contracts (6 validation checks), pipelinekit run  
87 tests, 84.70% coverage

### Phase 3 — Trust Layer ✅
Blueprint engine, Blueprint #001 (Postgres→Snowflake), notification system, Resend adapter, CI pipeline  
112 tests, 82.00% coverage, 45 source files

### Phase 4 — Intelligence Layer ⏳ NEXT
AI diagnostics, LLMProvider interface, pipelinekit diagnose, full MCP layer  
SPEC-005 needs to be written before the sprint fires

### Phase 5 — Architecture Layer 📋 NAMED, NOT STARTED
Architecture Intelligence — "What architecture should this pipeline use?"  
Named post-dbt/Fivetran merger. SPEC-011 to be written pre-Phase 5.

---

## Critical Files to Read Before Doing Anything

Read these in the repo before writing a single word of strategy or prompts:

```
1.  docs/reference/PROJECT-STATUS.md              ← Current state, decisions, post-Phase-3 tasks
2.  docs/institutional-memory/strategy-archive/PIPELINEKIT-MASTER-ARCHITECTURE.md  ← Full build map
3.  docs/constitution/Product-Constitution.md      ← The governing principle
4.  docs/decisions/ADR-000-Foundational-Architecture-Decisions.md  ← All 12 ADRs
5.  docs/reference/Architectural-Smells.md        ← 16 smells with direction — pre-flight checklist
6.  .claude/CLAUDE.md                             ← Claude Code's operating rules (v3)
7.  docs/reference/Error-Codes.md                 ← All PK error codes
8.  docs/specifications/ (all 10 SPECs)            ← Implementation contracts
```

---

## What to Search in Past Chats

If this is a new Claude Chat session with no prior context, search past conversations for:

- **"PipelineKit"** — finds all strategic and architectural discussions
- **"PIPELINEKIT-MASTER-ARCHITECTURE"** — finds the full phase and agent map
- **"Architectural-Smells"** — finds the 16 smells discussion and reasoning
- **"dbt Fivetran merger"** — finds the strategic repositioning discussion
- **"TTTD dimensions"** — finds the Time-to-Trusted-Data metric discussion and why they are design principles not benchmarks
- **"ICP-004"** — finds the Mixed-Stack Enterprise customer profile reasoning
- **"Phase 3 Claude Code"** — finds the sprint execution and decisions
- **"blind spot"** — finds the 7 architectural risks discussion (capability creep, spec drift, agent boundary erosion, etc.)
- **"control plane"** — finds the positioning refinement discussion (why we moved away from this term)
- **"intelligence layer"** — finds the final positioning language

---

## The Governing Principle — Never Changes

> **PipelineKit is the AI-native operating system for trusted analytics pipelines.**

Every decision, every feature, every SPEC traces back to this sentence.  
If something cannot be traced to it — it does not get built.

---

## The Development Workflow — Exact Sequence

Every phase follows this exact sequence:

```
Step 1: Command Center reads current repo state (run inspect-pipelinekit.ps1 or read key files)
Step 2: Command Center writes SPECs for the upcoming phase
Step 3: Eddy commits SPECs to main
Step 4: Command Center runs pre-flight (16 architectural smells checklist)
Step 5: Command Center writes session opener (Message 1 for Claude Code)
Step 6: Command Center writes full sprint prompt (Message 2 for Claude Code)
Step 7: Eddy commits prompts to strategy-archive/
Step 8: Eddy fires Claude Code — Message 1 first, wait for confirmation, then Message 2
Step 9: Claude Code builds, Eddy verifies locally
Step 10: Claude Code commits on feature branch, fast-forward merges to main
Step 11: Eddy confirms push and paste output back to Command Center
Step 12: Command Center produces updated PROJECT-STATUS.md
Step 13: Eddy commits PROJECT-STATUS — phase officially closed
```

---

## Post-Phase-3 Housekeeping (Do Before Phase 4 Sprint Fires)

These tasks are small but must be done before the Phase 4 sprint prompt is written:

```
□ Update docs/reference/Error-Codes.md — add PK-BLUEPRINT-001 to 004, PK-NOTIFY-001 to 004
□ Commit ADR-013 (Resend MCP governance) to docs/decisions/
□ Update SPEC-002 status header to "Implemented"
□ Update SPEC-003 status header to "Implemented"
□ Update SPEC-004 status header to "Implemented"
□ Update SPEC-006 status header to "Implemented"
□ Update SPEC-007 status header to "Implemented"
□ Update SPEC-008 status header to "Implemented"
□ Update SPEC-009 status header to "Implemented"
□ Update SPEC-005 stub with activation condition and Phase 4 preview
□ Add sources.yml to blueprints/postgres-to-snowflake/transform/
□ Confirm CI green on GitHub (ci.yml runs on push to main)
```

---

## What Phase 4 Builds

Phase 4 is the Intelligence Layer. Before firing the sprint:

**Command Center must write:**
- SPEC-005-AI-Diagnostics.md (currently a TBD stub)
- ADR-014 (AI provider MCP layer governance)

**What Claude Code will build:**
- `src/pipelinekit/ai/provider.py` — LLMProvider Protocol
- `src/pipelinekit/ai/evidence.py` — EvidenceCollector (reads state.db)
- `src/pipelinekit/ai/diagnostics.py` — DiagnosticsEngine
- `src/pipelinekit/ai/providers/` — openai.py, anthropic.py, ollama.py
- `src/pipelinekit/cli/diagnose.py` — pipelinekit diagnose command
- Full `.mcp/servers/` population

**The critical constraint:**
AI may diagnose and recommend. AI may never autonomously modify production.  
This is ADR-007 and Architectural Smell 13 (Observer Becomes Actor).  
Every AI recommendation requires human approval before execution.

**The diagnostic schema is already defined:**
`schemas/diagnostic.schema.json` — all AI output must validate against it.

---

## Agent Activation Map

| Agent | Phase | Status | Owns |
|---|---|---|---|
| cli-engineer | 1 | ✅ Active | src/pipelinekit/cli/ |
| quality-engineer | 1 | ✅ Active | tests/ |
| runtime-engineer | 2 | ✅ Active | runtime/, adapters/ |
| blueprint-engineer | 3 | ✅ Active | blueprints/ |
| release-engineer | 3 | ✅ Active | .github/workflows/ |
| diagnostics-engineer | 4 | 📋 Standby | src/pipelinekit/ai/ |
| documentation-engineer | 4+ | 📋 Standby | docs/ (post-implementation only) |

---

## MCP Governance

Every MCP requires an ADR before activation.

| MCP | Phase | ADR | Status |
|---|---|---|---|
| Resend | 3 | ADR-013 | ✅ Active |
| AI provider MCP layer | 4 | ADR-014 (to write) | 📋 Standby |
| Architecture Intelligence MCP | 5 | ADR-015 (to write) | 📋 Named |

Do not add any MCP not in this table without writing an ADR first.

---

## Key Architectural Decisions That Must Not Be Reversed

These are load-bearing. Every future decision must respect them:

1. **CLI never calls providers directly** — always through runtime → adapter
2. **Provider imports isolated in adapters** — dlt/dbt/Soda/Resend imports only in their adapter files
3. **Contracts define truth, not AI** — ADR-008
4. **AI may diagnose, never act autonomously** — ADR-007
5. **Every MCP requires an ADR** — established with ADR-013
6. **Blueprint = complete analytics system** — not a connector, not a template
7. **TTTD dimensions are design principles** — not promised benchmarks until real data exists
8. **Governing principle is immutable** — everything else can evolve beneath it

---

## Known Specification Drift (Fix Before Phase 4)

These SPECs do not exactly match the current implementation:

| SPEC | Drift | Fix needed |
|---|---|---|
| SPEC-002 | Shows `cwd: Path = Path.cwd()` — impl uses `cwd: Path \| None = None` | Update SPEC-002 |
| SPEC-004 | AcceptedValuesRule showed `__root__` — impl uses plain dict (Pydantic v2) | Update SPEC-004 |
| Error-Codes.md | Missing PK-CONFIG-005, PK-BLUEPRINT-*, PK-NOTIFY-* | Update Error-Codes.md |

---

## Strategic Context — Post-dbt/Fivetran Merger

The dbt Labs / Fivetran merger (June 2026) consolidated ingestion and transformation.  
PipelineKit's response: operate above them, not compete with them.

**Positioning language to use:**
- "Intelligence layer that designs, validates, governs, diagnoses, and continuously improves analytics pipelines"
- "AI-native operating system"
- "AI-native engineering"

**Positioning language to avoid:**
- "Control plane" — puts PipelineKit in orchestrator category with Dagster/Kestra
- "PipelineKit is not an ingestion tool" — negative definition, competitor-first
- "Using AI" — generic feature, not a category

**ICP model (4 profiles):**
- ICP-001: Solo Founder — fast, simple stack
- ICP-002: Analytics Consultancy — repeatability across clients
- ICP-003: Internal Data Team — reliability at scale
- ICP-004: Mixed-Stack Enterprise — coherence across 3+ heterogeneous tools (largest revenue opportunity)

---

## PowerShell Commands Eddy Uses

```powershell
# Verify current state
cd C:\Users\HP\Documents\pipelinekit
git log --oneline -5
git status

# Run quality gates
poetry run pytest --cov=src/pipelinekit --cov-fail-under=80
poetry run ruff check .
poetry run black --check .
poetry run mypy src/pipelinekit

# Inspect repo structure
.\inspect-pipelinekit.ps1
```

---

## What Would Let Eddy and This Project Down

Do not do these things:

1. **Write code or suggest implementation before reading the SPECs** — Claude Code reads SPECs, Command Center writes them. Never mix the roles.

2. **Skip the pre-flight smell check** — all 16 smells must pass before a sprint prompt is sent. This is not optional.

3. **Update PROJECT-STATUS.md before Eddy verifies and pushes** — Command Center produces it, Eddy commits it. Never mid-sprint.

4. **Let a Claude Code suggestion become architecture** — suggestions go through ADRs first. No exceptions.

5. **Add an MCP without an ADR** — the rule was established with ADR-013. It applies to every future MCP.

6. **Claim TTTD metrics without real data** — the five dimensions are design principles. Numbers come from design partners, not from this repo.

7. **Allow AI to act autonomously in Phase 4** — diagnose and recommend only. Human holds the scalpel.

8. **Skip the handover summary at end of each long session** — institutional memory must survive chat boundaries.

---

## Final Word

This project was built in one session — from 0 Python files to 112 tests, 3 complete phases, a live CI pipeline, a deployable blueprint, and a strategic architecture that survived a major market event without changing its governing principle.

The quality came from discipline: SPECs before code, smells before sprints, agents in their lanes, decisions in ADRs, state always recorded, architecture in documents not conversations.

Maintain that discipline. The project will compound in value with every phase that follows it.

> **PipelineKit is the AI-native operating system for trusted analytics pipelines.**

Everything else serves that sentence.
