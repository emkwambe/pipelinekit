# PipelineKit — Master Development Architecture
## The Full Coherence Map: Agents, MCPs, Phases, and How Everything Connects

**Version:** 2.0  
**Date:** June 25, 2026  
**Owner:** Command Center (Claude Chat)  
**Status:** Authoritative planning document — governs all sprint prompts  
**Change from v1.0:** Phase 5 Architecture Intelligence added; control plane positioning clarified post-dbt/Fivetran merger

---

## 1. The Single Governing Principle

Every architectural decision in this document traces back to one sentence:

> **PipelineKit is the AI-native operating system for trusted analytics pipelines.**

Every agent, every MCP, every sprint, every SPEC exists to make that sentence more true.
If a proposed piece of work cannot be traced back to that sentence, it does not get built.

---

## 2. The Control Plane Position

PipelineKit does not own ingestion. Fivetran, dlt, and Airbyte own ingestion.  
PipelineKit does not own transformation. dbt owns transformation.  
PipelineKit does not own storage. Snowflake, BigQuery, and DuckDB own storage.  
PipelineKit does not own orchestration. Dagster and Kestra own orchestration.

**PipelineKit owns the operating layer above all of them.**

```
                    PipelineKit
                   (Control Plane)
                        │
        ┌───────────────┼───────────────┐
        │               │               │
   Ingestion      Transformation    Quality
  (dlt/Fivetran)    (dbt/SQLMesh)   (Soda)
        │               │               │
        └───────────────┼───────────────┘
                        │
                   Storage Layer
            (Snowflake/BigQuery/DuckDB)
```

This position is not a workaround. It is the architecture the market needs.

As platforms consolidate, enterprises run more heterogeneous environments — not fewer.
The Fortune 500 running Informatica + Fivetran + custom Python + Spark needs a control plane.
PipelineKit is that control plane.

---

## 3. The Five-Phase Build Map

### Overview

```
Phase 1 — Foundation           Weeks 1–2    CLI + Config + State + Tests
Phase 2 — Data Layer           Weeks 3–4    dlt + dbt + Contracts + Quality
Phase 3 — Trust Layer          Weeks 5–6    Observability + Alerts + Blueprint #001 + CI
Phase 4 — Intelligence Layer   Weeks 7+     AI Diagnostics + MCP + Agent Activation
Phase 5 — Architecture Layer   Future       Architecture Intelligence + Multi-Stack Coordination
```

No phase begins until the previous phase's Definition of Done is met.
No agent is activated until the layer it operates on exists.
No MCP is introduced until the CLI is stable and the data layer is running.

### Phase 5 — Architecture Intelligence (Intent Only)

Phase 5 is named but not yet specified. It activates after Phase 4 is complete and validated with design partners.

**What Architecture Intelligence means:**

Phase 4 AI answers: *"Why did this pipeline fail?"*  
Phase 5 AI answers: *"What architecture should this pipeline use?"*

Examples of Phase 5 capabilities:
- "Should this pipeline use dbt or SQLMesh for transformation?"
- "Should this workload run in DuckDB or Snowflake given cost and volume?"
- "Should this use Fivetran or dlt given licensing and operational constraints?"
- "What is the cheapest reliable architecture for this data volume?"
- "Will this deployment violate our existing ADRs?"
- "What changed in the data landscape since last week?"

No one currently owns this decision layer. PipelineKit is positioned to own it because:
1. It already sits above the tool layer
2. It already has contracts and schemas that define truth
3. It already has structured diagnostic evidence from Phase 4
4. It already has the ADR system that captures architectural decisions

**Phase 5 SPEC:** SPEC-011-Architecture-Intelligence.md (to be written pre-Phase 5)  
**Phase 5 ADR:** ADR-015-Architecture-Intelligence-Scope.md (to be written pre-Phase 5)

---

## 4. Agent Architecture — Full Map

The repo has 7 agents pre-defined. Here is when each activates, what it owns, and what it must not touch.

### Agent Activation Sequence

```
Phase 1:   cli-engineer          ACTIVE      Owns: src/pipelinekit/cli/
Phase 1:   quality-engineer      ACTIVE      Owns: tests/
Phase 2:   runtime-engineer      ACTIVE      Owns: src/pipelinekit/runtime/
Phase 3:   blueprint-engineer    ACTIVE      Owns: blueprints/
Phase 3:   release-engineer      ACTIVATES   Owns: .github/workflows/
Phase 4:   diagnostics-engineer  STANDBY     Owns: src/pipelinekit/diagnostics/
Phase 4+:  documentation-engineer STANDBY   Owns: docs/ (post-implementation only)
```

### Agent Ownership Rules (non-negotiable)

| Agent | Creates | Never Touches |
|---|---|---|
| cli-engineer | `src/pipelinekit/cli/`, `tests/cli/` | runtime, adapters, AI, state logic |
| quality-engineer | `tests/` (all non-cli) | src/ code, contracts, schemas |
| runtime-engineer | `src/pipelinekit/runtime/`, `src/pipelinekit/adapters/` | CLI layer, AI layer |
| blueprint-engineer | `src/pipelinekit/blueprints/`, `blueprints/` | runtime, adapters, CLI internals |
| diagnostics-engineer | `src/pipelinekit/ai/`, `src/pipelinekit/diagnostics/` | contracts, runtime, adapters |
| release-engineer | `.github/workflows/`, `pyproject.toml` versioning | source code, tests |
| documentation-engineer | `docs/` (only after implementation confirmed) | any source code, any spec |

### The CLI/Runtime Boundary (critical rule)

```
CLI layer (cli-engineer owns)
    ↓ calls
Runtime layer (runtime-engineer owns)
    ↓ calls
Adapter layer (runtime-engineer owns)
    ↓ calls
Providers (external: dlt, dbt, Soda, Resend)
```

The CLI never calls providers directly.
The CLI never contains business logic.
The runtime never imports from CLI.
Adapters never call each other.

---

## 5. MCP Architecture — When and Why

MCPs are not a Phase 1-2 concern. They are phased deliberately.

### MCP Activation Map

```
Phase 1–2:  NO MCPs.
Phase 3:    ONE MCP — Resend (alerts only).
Phase 4:    AI provider MCP layer activates.
Phase 5:    Architecture intelligence MCP layer (multi-tool query capability).
```

### MCP Governance Rule

Every new MCP requires an approved ADR before activation.

No MCP is added because it is useful.
MCPs are added because they serve the governing principle and have an ADR justifying them.

### Phase 4 MCP Architecture

```
pipelinekit diagnose
    → Evidence collector (logs, contract violations, quality results)
    → Evidence package → LLMProvider interface
        → Sprinter MCP: fast classification
        → Thinker MCP: root cause analysis
    → Structured JSON output (diagnostic.schema.json)
    → Human review prompt
    → Approved action execution
```

### The LLMProvider Interface (Phase 3 stub, Phase 4 implementation)

```python
class LLMProvider(Protocol):
    def diagnose(self, evidence: EvidencePackage) -> DiagnosticResult: ...
    def summarize(self, logs: list[str]) -> str: ...
    def recommend(self, diagnosis: DiagnosticResult) -> list[RecommendedAction]: ...
    def generate_contract(self, schema: dict) -> ContractDefinition: ...
```

---

## 6. The SPEC Writing Sequence

| SPEC | Title | Status |
|---|---|---|
| SPEC-001 | CLI Framework | ✅ Approved, Implemented |
| SPEC-002 | Configuration System | ✅ Approved, Implemented |
| SPEC-003 | Pipeline Runtime | ✅ Approved, Implemented |
| SPEC-004 | Contracts | ✅ Approved, Implemented |
| SPEC-005 | AI Diagnostics | 📋 Placeholder (Phase 4) |
| SPEC-006 | Blueprint Engine | ✅ Approved, In Progress (Phase 3) |
| SPEC-007 | State Store | ✅ Approved, Implemented |
| SPEC-008 | Notification System | ✅ Approved, In Progress (Phase 3) |
| SPEC-009 | Provider Adapters | ✅ Approved, Implemented |
| SPEC-010 | Testing & Quality Gates | ✅ Approved, Implemented |
| SPEC-011 | Architecture Intelligence | 📋 Placeholder (Phase 5) |

---

## 7. The pipelinekit.yaml Contract

The canonical 8-section configuration file. Unchanged from v1.0.

Required sections: `pipeline`, `runtime`, `ingestion`, `transformation`,
`contracts`, `quality`, `diagnostics`, `notifications`

Contract-required fields (from contracts/pipeline.yaml):
`pipeline.name`, `runtime`, `ingestion`, `transformation`, `contracts`, `diagnostics`

---

## 8. The Source Code Architecture (Full Map)

```
src/pipelinekit/
├── cli/                    ✅ Phase 1 (init, validate, status, run)
│                           ⏳ Phase 3 (blueprint commands)
├── config/                 ✅ Phase 1
├── core/                   ✅ Phase 1 (errors)
├── state/                  ✅ Phase 1 + Phase 2 extension
├── runtime/                ✅ Phase 2
├── adapters/               ✅ Phase 2 (dlt, dbt, Soda)
│                           ⏳ Phase 3 (Resend)
├── contracts/              ✅ Phase 2
├── blueprints/             ⏳ Phase 3
├── notifications/          ⏳ Phase 3
├── observability/          ⏳ Phase 3
├── ai/                     📋 Phase 4
└── diagnostics/            📋 Phase 4
```

---

## 9. The Blueprint Architecture (Phase 3)

Blueprints are the primary product moat.
A blueprint is not a connector — it is a complete analytics system.

### Blueprint #001 — Postgres → Snowflake

The first production blueprint. Ships with Phase 3.
Standard for all future blueprints: deployable in < 60 minutes, trusted data in < 24 hours.

### Blueprint Catalog — Phase 3+ Roadmap

**Tier 1 (Launch with Phase 3):**
- Postgres → Snowflake ⏳

**Tier 2 (Phase 4):**
- Salesforce → Snowflake
- Salesforce → BigQuery
- Stripe → Snowflake
- Stripe → BigQuery
- Postgres → BigQuery

**Tier 3 (Phase 5):**
- HubSpot → Snowflake
- MySQL → Snowflake
- REST API → Snowflake

---

## 10. Competitive Position — Post-Merger

**The dbt Labs / Fivetran merger (June 2026)** consolidated ingestion + transformation into one platform targeting "data infrastructure for trusted AI agents."

PipelineKit's response: operate above them, not against them.

```
Their stack:          PipelineKit's layer:
─────────────         ──────────────────────────────
Sources               Architecture Intelligence (Phase 5)
    ↓                         ↓
Fivetran              Intent → Planning → Architecture
    ↓                         ↓
dbt                   Pipeline Generation → Validation
    ↓                         ↓
Semantic Layer        Diagnostics → Repair → Testing
    ↓                         ↓
Governance            Release → Observability
    ↓                         ↓
AI Agents             Continuous Improvement
```

Their moat: connectors, transformations, semantic layer, enterprise sales, cloud platform.  
PipelineKit's moat: the operating layer that coordinates above all of them.

These are not competing layers. They are adjacent layers.
PipelineKit's strongest customers run Fivetran and dbt — and still need PipelineKit.

---

## 11. Error Code Architecture

### Implemented (Phase 1-2)
```
PK-CONFIG-001 to 005
PK-STATE-001 to 003
PK-RUNTIME-001 to 003
PK-ADAPTER-001 to 003
PK-CONTRACT-001 to 008
```

### Phase 3
```
PK-BLUEPRINT-001 to 004
PK-NOTIFY-001 to 004
```

### Phase 4
```
PK-AI-001 to 003
```

---

## 12. Command Center Operating Rules

1. Every prompt references the authoritative SPEC.
2. Every prompt names the active agent.
3. Every prompt enforces ownership boundaries.
4. Every prompt ends with a Definition of Done.
5. No prompt introduces a dependency without an ADR.
6. Every proposed change is evaluated against Architectural-Smells.md (15 smells).
7. MCPs require ADRs before activation.
8. The diagnostic schema is authoritative for AI output.
9. The blueprint schema is authoritative for blueprint metadata.
10. PROJECT-STATUS.md is updated only by Command Center after phase completion.

---

## 13. The Immediate Next Actions (Current)

```
✅ Phase 1 — Complete (8d8865f)
✅ Phase 2 — Complete (f337cfe)
⏳ Phase 3 — In Progress
   Claude Code building: blueprints, notifications, CI
   Agents active: blueprint-engineer, release-engineer, runtime-engineer

📋 After Phase 3 closes:
   - Update PROJECT-STATUS.md (Command Center)
   - Write ADR-013 (Resend MCP governance)
   - Write ICP-004 (Mixed-Stack Enterprise)
   - Add Smell 16 (Control Plane Inversion) to Architectural-Smells.md
   - Update placeholder status headers across docs/specifications/

📋 Pre-Phase 4:
   - Write SPEC-005 (AI Diagnostics)
   - Write ADR-014 (AI provider MCP layer)
   - LLMProvider interface stub committed

📋 Pre-Phase 5:
   - Write SPEC-011 (Architecture Intelligence)
   - Write ADR-015 (Architecture Intelligence scope)
```

---

## 14. The Coherence Test

Before any work is done, ask:

1. Does this trace to the Constitution?
2. Does this conform to all accepted ADRs?
3. Does this belong to the correct agent?
4. Is the relevant SPEC written and filled?
5. Does this exist in the correct phase?
6. Does this respect the CLI → Runtime → Adapter boundary?
7. Is AI deferred until Phase 4 (except Resend alerts in Phase 3)?
8. Does this pass all 15 architectural smells?
9. Does the control plane position — operating above providers — remain intact?

If any answer is no — stop, resolve, then proceed.

---

*This document is the master planning artifact for PipelineKit development.*  
*All sprint prompts, all SPEC content, and all agent activations trace back to this document.*  
*Updates require a new Command Center session and a version increment.*  
*Version history: 1.0 (June 24) → 2.0 (June 25, post-merger positioning + Phase 5 named)*
