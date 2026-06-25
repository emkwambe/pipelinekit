# PipelineKit — Master Development Architecture
## The Full Coherence Map: Agents, MCPs, Phases, and How Everything Connects

**Version:** 1.0  
**Date:** June 24, 2026  
**Owner:** Command Center (Claude Chat)  
**Status:** Authoritative planning document — governs all sprint prompts

---

## 1. The Single Governing Principle

Every architectural decision in this document traces back to one sentence:

> **PipelineKit is the AI-native operating system for trusted analytics pipelines.**

Every agent, every MCP, every sprint, every SPEC exists to make that sentence more true.
If a proposed piece of work cannot be traced back to that sentence, it does not get built.

---

## 2. The Four-Phase Build Map

### Overview

```
Phase 1 — Foundation         Weeks 1–2    CLI + Config + State + Tests
Phase 2 — Data Layer         Weeks 3–4    dlt + dbt + Contracts + Quality
Phase 3 — Trust Layer        Weeks 5–6    Observability + Doctor + Alerts + Blueprint #001
Phase 4 — Intelligence Layer Weeks 7+     AI Diagnostics + MCP + Agent Activation
```

No phase begins until the previous phase's Definition of Done is met.
No agent is activated until the layer it operates on exists.
No MCP is introduced until the CLI is stable and the data layer is running.

---

## 3. Agent Architecture — Full Map

The repo has 7 agents pre-defined. Here is when each activates, what it owns, and what it must not touch.

### Agent Activation Sequence

```
Phase 1:   cli-engineer          ACTIVE    Owns: src/pipelinekit/cli/
Phase 1:   quality-engineer      ACTIVE    Owns: tests/
Phase 2:   runtime-engineer      ACTIVATES Owns: src/pipelinekit/runtime/
Phase 2:   blueprint-engineer    STANDBY   Owns: blueprints/ (Phase 3)
Phase 3:   diagnostics-engineer  STANDBY   Owns: src/pipelinekit/diagnostics/
Phase 3:   release-engineer      ACTIVATES Owns: .github/workflows/, release process
Phase 4:   documentation-engineer STANDBY  Owns: docs/ updates post-implementation
```

### Agent Ownership Rules (non-negotiable)

| Agent | Creates | Never Touches |
|---|---|---|
| cli-engineer | `src/pipelinekit/cli/`, `tests/cli/` | runtime, adapters, AI, state logic |
| quality-engineer | `tests/` (all non-cli) | src/ code, contracts, schemas |
| runtime-engineer | `src/pipelinekit/runtime/`, `src/pipelinekit/adapters/` | CLI layer, AI layer |
| blueprint-engineer | `blueprints/`, `examples/` | core runtime, CLI internals |
| diagnostics-engineer | `src/pipelinekit/ai/`, `src/pipelinekit/diagnostics/` | contracts, runtime, adapters |
| release-engineer | `.github/workflows/`, `pyproject.toml` versioning | source code, tests |
| documentation-engineer | `docs/` (only after implementation is done) | any source code, any spec |

### The CLI/Runtime Boundary (critical rule)

This boundary must never be violated:

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

## 4. MCP Architecture — When and Why

MCPs are not a Week 1 concern. They are a Phase 4 concern with one Phase 3 exception.

### Why MCPs Are Deferred

MCPs extend PipelineKit's reach into external systems — they are the connective tissue between the CLI and the outside world at AI-assisted operation time. They cannot be introduced before:

1. The CLI is stable (Phase 1 complete)
2. The runtime is executing pipelines (Phase 2 complete)
3. The diagnostic schemas are validated (Phase 3 complete)
4. The AI provider interface is defined (Phase 4 gate)

Introducing MCPs before these layers exist would mean building connectors to a system that doesn't yet have stable interfaces. That produces wasted work and architectural drift.

### MCP Activation Map

```
Phase 1–2:  NO MCPs. Zero external connections from PipelineKit itself.
Phase 3:    ONE MCP — Resend (alerts only). Introduced only when the
            notification contract is satisfied and alerts are Phase 3 scope.
Phase 4:    FULL MCP layer activates.
```

### Phase 4 MCP Architecture

When Phase 4 activates, MCPs enable the AI diagnostic and operator layer:

```
pipelinekit diagnose
    → Evidence collector gathers: logs, contract violations, quality results
    → Evidence package → AI Decision Layer (LLMProvider interface)
        → Sprinter MCP: fast classification (log triage, issue categorization)
        → Thinker MCP: root cause analysis, remediation planning
    → Structured JSON output (diagnostic.schema.json)
    → Human review prompt
    → Approved action execution
```

The `.mcp/` directory in the repo is already scaffolded with:
- `servers/` — where MCP server definitions will live
- `configs/` — where per-environment MCP configs will live
- `registry/servers.md` — the registry of available servers
- `templates/` — reusable MCP config templates

None of these get content until Phase 4 — except `servers.md` which gets a planning entry in Phase 3 for the Resend alert MCP.

### The LLMProvider Interface (Phase 4 foundation)

This interface must be defined in Phase 3 (as a stub) so Phase 4 can implement against it:

```python
class LLMProvider(Protocol):
    def diagnose(self, evidence: EvidencePackage) -> DiagnosticResult: ...
    def summarize(self, logs: list[str]) -> str: ...
    def recommend(self, diagnosis: DiagnosticResult) -> list[RecommendedAction]: ...
    def generate_contract(self, schema: dict) -> ContractDefinition: ...
```

Every AI provider (OpenAI, Anthropic, Ollama, local) implements this interface.
No provider-specific code exists outside `src/pipelinekit/ai/providers/`.
This is ADR-005 (BYOK) and ADR-006 (Multi-Model) made concrete.

---

## 5. The SPEC Writing Sequence

The 10 SPEC stubs must be filled in a specific order. SPECs gate sprint work — Claude Code cannot build what is not specified.

### SPEC Writing Order and Gate Rules

| SPEC | Title | Written When | Blocks |
|---|---|---|---|
| SPEC-001 | CLI Framework | NOW (pre-Phase 1) | Phase 1 sprint |
| SPEC-002 | Configuration System | NOW (pre-Phase 1) | Phase 1 sprint |
| SPEC-007 | State Store | NOW (pre-Phase 1) | Phase 1 sprint |
| SPEC-010 | Testing & Quality Gates | NOW (pre-Phase 1) | All sprints |
| SPEC-003 | Pipeline Runtime | Pre-Phase 2 | Phase 2 sprint |
| SPEC-009 | Provider Adapters | Pre-Phase 2 | Phase 2 sprint |
| SPEC-004 | Contracts | Pre-Phase 2 | Phase 2 sprint |
| SPEC-008 | Notification System | Pre-Phase 3 | Phase 3 sprint |
| SPEC-006 | Blueprint Engine | Pre-Phase 3 | Phase 3 sprint |
| SPEC-005 | AI Diagnostics | Pre-Phase 4 | Phase 4 sprint |

**Rule:** No SPEC is written until the implementation layer below it exists or is being built.
**Exception:** SPEC-001, 002, 007, 010 are written NOW because Phase 1 cannot start without them.

---

## 6. The pipelinekit.yaml Contract

This is the canonical configuration file. It is defined by `docs/reference/Configuration-Schema.md` and `contracts/pipeline.yaml`. It must be respected exactly — no improvisation.

### Required Sections (8 total)

```yaml
pipeline:          # name, version, description
  name: my-project
  version: "0.1.0"

runtime:           # execution environment config
  environment: local

ingestion:         # dlt source + destination config
  source:
    type: postgres
  destination:
    type: snowflake

transformation:    # dbt project config
  enabled: false
  project_dir: ./transform

contracts:         # contract enforcement settings
  enabled: true
  directory: ./contracts

quality:           # Soda / quality check config
  enabled: false
  checks_dir: ./quality

diagnostics:       # AI diagnostics config
  enabled: false
  provider: none

notifications:     # alert routing config
  enabled: false
  channels: []
```

### Contract Compliance

From `contracts/pipeline.yaml`, the required fields are:
`name`, `runtime`, `ingestion`, `transformation`, `contracts`, `diagnostics`

This means `pipelinekit init` must generate a YAML with all 8 sections.
`pipelinekit validate` must check all 6 contract-required fields exist and are structurally valid.
Exit code 0 = valid. Exit code 1 = invalid (with structured error using PK-CONFIG-001 format).

---

## 7. The Source Code Architecture (Full Map)

From `SPEC-002-OLD-Repository-Standards.md` — this is the authoritative layout:

```
src/pipelinekit/
├── cli/                    (cli-engineer owns)
│   ├── __init__.py
│   ├── main.py             Typer app, command registration
│   ├── init.py             pipelinekit init
│   ├── validate.py         pipelinekit validate
│   ├── status.py           pipelinekit status
│   ├── run.py              pipelinekit run        (Phase 2)
│   ├── doctor.py           pipelinekit doctor     (Phase 3)
│   ├── diagnose.py         pipelinekit diagnose   (Phase 4)
│   ├── migrate.py          pipelinekit migrate    (Phase 3)
│   └── report.py           pipelinekit report     (Phase 3)
│
├── config/                 (cli-engineer scaffolds, runtime-engineer fills)
│   ├── __init__.py
│   ├── schema.py           Pydantic config model (8 sections)
│   └── loader.py           load_config(), validate_config()
│
├── state/                  (cli-engineer scaffolds, runtime-engineer fills)
│   ├── __init__.py
│   └── db.py               SQLite init, run log CRUD
│
├── runtime/                (runtime-engineer owns — Phase 2)
│   ├── __init__.py
│   ├── runner.py           PipelineRunner
│   └── executor.py         Execution orchestration
│
├── adapters/               (runtime-engineer owns — Phase 2)
│   ├── ingestion/
│   │   └── dlt/            dlt adapter
│   ├── transformation/
│   │   └── dbt/            dbt Core adapter
│   ├── quality/
│   │   └── soda/           Soda adapter
│   └── alerts/
│       └── resend/         Resend adapter (Phase 3)
│
├── contracts/              (runtime-engineer owns — Phase 2)
│   ├── __init__.py
│   ├── validator.py        ContractValidator
│   └── models.py           Contract Pydantic models
│
├── observability/          (runtime-engineer owns — Phase 3)
│   ├── __init__.py
│   ├── doctor.py           Health checks
│   ├── freshness.py        Freshness monitoring
│   └── reporter.py         Report generation
│
├── ai/                     (diagnostics-engineer owns — Phase 4)
│   ├── __init__.py
│   ├── provider.py         LLMProvider Protocol
│   ├── evidence.py         Evidence collector
│   ├── diagnostics.py      DiagnosticsEngine
│   └── providers/
│       ├── openai.py
│       ├── anthropic.py
│       └── ollama.py
│
└── blueprints/             (blueprint-engineer owns — Phase 3)
    ├── __init__.py
    ├── registry.py         Blueprint registry
    ├── installer.py        Blueprint installer
    └── validator.py        Blueprint validator
```

---

## 8. Error Code Implementation Plan

From `docs/reference/Error-Codes.md` — errors follow `PK-[AREA]-[NUMBER]` format.

### Phase 1 Error Codes (implement now)

```
PK-CONFIG-001   Invalid pipelinekit.yaml structure
PK-CONFIG-002   Required section missing
PK-CONFIG-003   pipelinekit.yaml not found
PK-STATE-001    State database unavailable
PK-STATE-002    Cannot write to .pipelinekit/state.db
```

### Phase 2 Error Codes (implement with runtime)

```
PK-RUNTIME-001  Pipeline execution failed
PK-RUNTIME-002  Provider initialization failed
PK-ADAPTER-001  Adapter connection failed
PK-CONTRACT-001 Required column missing
PK-CONTRACT-002 Freshness SLA violated
```

### Phase 3–4 Error Codes (implement with their layers)

```
PK-AI-001       AI provider unavailable
PK-AI-002       AI response failed schema validation
PK-AI-003       Confidence below threshold
```

All errors must be structured, not free-form strings. Pattern:

```python
class PipelineKitError(Exception):
    def __init__(self, code: str, message: str, context: dict = {}):
        self.code = code        # e.g. "PK-CONFIG-001"
        self.message = message
        self.context = context
```

---

## 9. The Test Architecture

From `SPEC-002-OLD` — 80% minimum coverage is the standard.

### Test Structure

```
tests/
├── __init__.py
├── cli/
│   ├── test_init.py
│   ├── test_validate.py
│   └── test_status.py
├── config/
│   ├── test_schema.py
│   └── test_loader.py
├── state/
│   └── test_db.py
├── runtime/            (Phase 2)
├── adapters/           (Phase 2)
├── contracts/          (Phase 2)
├── observability/      (Phase 3)
└── ai/                 (Phase 4)
```

### CI Pipeline (Phase 1 gate — must exist before first merge)

```yaml
# .github/workflows/ci.yml
on: [push, pull_request]
jobs:
  test:
    steps:
      - poetry install
      - poetry run ruff check .
      - poetry run black --check .
      - poetry run mypy src/
      - poetry run pytest --cov=src/pipelinekit --cov-fail-under=80
```

The release-engineer agent activates at end of Phase 1 to write this file.

---

## 10. The Blueprint Architecture (Phase 3)

Blueprints are the moat. They are not a collection of connectors — they are complete analytics systems.

### Blueprint File Structure

```
blueprints/
└── postgres-to-snowflake/
    ├── blueprint.json          (validated against schemas/blueprint.schema.json)
    ├── ingestion/
    │   └── pipeline.py         dlt pipeline definition
    ├── transform/
    │   ├── dbt_project.yml
    │   └── models/
    ├── contracts/
    │   └── orders.yaml
    ├── quality/
    │   └── checks.yaml
    ├── alerts/
    │   └── config.yaml
    └── docs/
        └── runbook.md
```

`blueprint.json` is validated against `schemas/blueprint.schema.json` which requires:
`name`, `version`, `source`, `destination`, `contracts`

### Blueprint CLI Commands (Phase 3)

```
pipelinekit blueprint list
pipelinekit blueprint install postgres-to-snowflake
pipelinekit blueprint validate
```

---

## 11. The Institutional Memory Completion Plan

The 15 empty stub files are not blocked by implementation. They are blocked by strategic decisions that are already made. Here is the writing order:

### Write immediately (this session or next):

1. `SPEC-001-CLI-Framework.md` — unblocks Phase 1
2. `SPEC-002-Configuration-System.md` — unblocks Phase 1
3. `SPEC-007-State-Store.md` — unblocks Phase 1
4. `SPEC-010-Testing-and-Quality-Gates.md` — unblocks Phase 1
5. `ADR-002-Drop-Sling.md` — decision already made in ADR-000
6. `ADR-003-Adopt-dlt.md` — decision already made in ADR-000
7. `ADR-004-BYOK-AI-Policy.md` — decision already made in ADR-000
8. `ADR-005-Apache-2.0-Preference.md` — decision already made in Principles doc
9. `ICP-001-Solo-Founder.md` — fully defined in Strategic Operating Document
10. `ICP-002-Analytics-Consultancy.md` — fully defined in Strategic Operating Document
11. `ICP-003-Internal-Data-Team.md` — fully defined in Strategic Operating Document
12. `Customer-Interview-Template.md` — questions already in Strategic Operating Document
13. `PipelineKit-Category-Thesis.md` — fully written in Principles.md (extract and format)
14. `PipelineKit-Principles.md` — already exists in philosophy/ as full document

### Write after beta (real data required):

15. `Airbyte-Analysis.md` — needs customer migration evidence
16. `Fivetran-Analysis.md` — needs customer migration evidence
17. `Meltano-Analysis.md` — needs competitive positioning from real use
18. `Dagster-Analysis.md` — needs competitive positioning from real use
19. `dbt-Cloud-Analysis.md` — needs competitive positioning from real use
20. `Kestra-Analysis.md` — needs competitive positioning from real use

---

## 12. Command Center Operating Rules

These are the rules that govern every Claude Code prompt I write:

1. **Every prompt references the authoritative SPEC.** No prompt is written before the relevant SPEC exists and is filled.

2. **Every prompt names the active agent.** Claude Code adopts the agent role defined in `agents/[agent]/AGENT.md` and `agents/[agent]/SYSTEM.md`.

3. **Every prompt enforces ownership boundaries.** Files outside the agent's ownership are explicitly listed as DO NOT MODIFY.

4. **Every prompt ends with a Definition of Done** that Eddy can verify in PowerShell.

5. **No prompt introduces a dependency not in CLAUDE.md** without first proposing an ADR.

6. **MCPs are not mentioned in any Phase 1–2 prompt.** They enter Phase 3 (Resend only) and Phase 4 (full AI layer).

7. **The diagnostic schema is authoritative.** Any AI output must validate against `schemas/diagnostic.schema.json`.

8. **The blueprint schema is authoritative.** Any blueprint must validate against `schemas/blueprint.schema.json`.

---

## 13. The Immediate Next Actions (Sequenced)

```
Action 1 — THIS SESSION
  Write SPEC-001-CLI-Framework.md
  Write SPEC-002-Configuration-System.md
  Write SPEC-007-State-Store.md
  Write SPEC-010-Testing-and-Quality-Gates.md
  → These 4 files unlock Phase 1 entirely

Action 2 — THIS SESSION
  Write the Phase 1 Claude Code prompt
  → Adopts cli-engineer + quality-engineer agent roles
  → References SPEC-001, 002, 007, 010
  → Builds: pyproject.toml, src/pipelinekit/cli/, src/pipelinekit/config/,
            src/pipelinekit/state/, tests/

Action 3 — CLAUDE CODE executes
  Eddy verifies with PowerShell validation commands
  Commit to main on green

Action 4 — NEXT SESSION (pre-Phase 2)
  Write SPEC-003-Pipeline-Runtime.md
  Write SPEC-009-Provider-Adapters.md
  Write SPEC-004-Contracts.md
  Write Phase 2 Claude Code prompt (runtime-engineer agent activates)

Action 5 — NEXT SESSION (pre-Phase 3)
  Write SPEC-008-Notification-System.md
  Write SPEC-006-Blueprint-Engine.md
  Write Phase 3 Claude Code prompt (blueprint-engineer + release-engineer activate)
  Resend MCP entry added to .mcp/registry/servers.md

Action 6 — PHASE 4 SESSION
  Write SPEC-005-AI-Diagnostics.md
  Write LLMProvider interface stub (Phase 3 deliverable, now implemented)
  Full MCP layer designed and implemented
  diagnostics-engineer agent activates
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
7. Is AI deferred until Phase 4 (except Resend in Phase 3)?

If any answer is no — stop, resolve, then proceed.

---

*This document is the master planning artifact for PipelineKit development.*  
*All sprint prompts, all SPEC content, and all agent activations trace back to this document.*  
*Updates require a new Command Center session and a revised version of this file.*
