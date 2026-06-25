# PipelineKit — Project Status

**File:** `docs/reference/PROJECT-STATUS.md`  
**Rule:** Updated only at the end of each completed phase. Never mid-sprint.  
**Owner:** Command Center (Claude Chat)

---

## Current State

**Active Phase:** Phase 5 — Architecture Layer  
**Last Completed Phase:** Phase 4 — Intelligence Layer  
**Last Updated:** June 25, 2026  
**Main Branch:** `47bdd51` (Phase 4 intelligence layer)

---

## Phase Completion Record

### ✅ Phase 1 — Foundation
**Completed:** June 25, 2026 | **Commit:** `8d8865f`

- CLI (init, validate, status), config system, SQLite state, error hierarchy
- 36 tests, 92.65% coverage
- SPECs: SPEC-001, 002, 007, 010 | Agents: cli-engineer, quality-engineer

---

### ✅ Phase 2 — Data Layer
**Completed:** June 25, 2026 | **Commit:** `f337cfe`

- Runtime (PipelineRunner), adapters (dlt/dbt/Soda), contracts (6 checks), pipelinekit run
- 87 tests, 84.70% coverage
- SPECs: SPEC-003, 004, 009 | Agent: runtime-engineer

---

### ✅ Phase 3 — Trust Layer
**Completed:** June 25, 2026 | **Commit:** `d938e50`

- Blueprint engine, Blueprint #001 (Postgres→Snowflake complete), notifications, Resend adapter, CI pipeline
- 112 tests, 82.00% coverage, 45 source files
- SPECs: SPEC-006, 008 | Agents: blueprint-engineer, release-engineer
- First MCP: Resend (ADR-013)

---

### ✅ Phase 4 — Intelligence Layer
**Completed:** June 25, 2026  
**Commit:** `47bdd51`  
**Branch:** `phase-4-intelligence-layer` → fast-forward merged to `main`

**What was built:**
- `src/pipelinekit/ai/provider.py` — LLMProvider Protocol
- `src/pipelinekit/ai/evidence.py` — EvidenceCollector + EvidencePackage (read-only)
- `src/pipelinekit/ai/models.py` — DiagnosticResult, RecommendedAction
- `src/pipelinekit/ai/diagnostics.py` — DiagnosticsEngine (schema validation trust boundary)
- `src/pipelinekit/ai/providers/openai.py` — OpenAIProvider
- `src/pipelinekit/ai/providers/anthropic.py` — AnthropicProvider
- `src/pipelinekit/ai/providers/ollama.py` — OllamaProvider (local/air-gapped)
- `src/pipelinekit/cli/diagnose.py` — pipelinekit diagnose command
- `src/pipelinekit/state/db.py` — diagnostic_results table + insert_diagnostic_result()
- `src/pipelinekit/core/errors.py` — DiagnosticsError + LLMError
- `tests/ai/` — 39 new tests

**Quality gates (all green):**
| Gate | Result |
|---|---|
| pytest --cov-fail-under=80 | 151 passed (112 prior + 39 new), 82.16% coverage |
| ruff check | All checks passed |
| black --check | 97 files unchanged |
| mypy src/pipelinekit | No issues, 55 files |

**ai/ coverage vs SPEC-005 target (≥85%):**
| Module | Coverage |
|---|---|
| ai/diagnostics.py | 100% |
| ai/providers/__init__.py | 100% |
| ai/providers/ollama.py | 100% |
| ai/evidence.py | 96% |
| ai/models.py | 96% |
| ai/providers/anthropic.py | 88% |
| ai/providers/openai.py | 88% |
| **ai/ overall** | **~95%** |

**SPECs satisfied:** SPEC-005  
**ADR satisfied:** ADR-014 (AI provider MCP layer)  
**Agent activated:** diagnostics-engineer  
**AI boundary enforced by design:**
- `can_auto_fix` forced False in engine — provider returning True is corrected (tested)
- No execution path exists — `test_no_action_is_auto_executed` asserts this
- Schema validation mandatory — invalid output raises `LLMError(PK-AI-002)`, never reaches CLI
- EvidenceCollector is read-only — no writes to state.db
- Provider imports isolated — exactly 3 files, each inside its own provider file (verified by grep)
- BYOK via env vars: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OLLAMA_HOST`

**Key decisions:**
- Provider factory in `ai/providers/__init__.py` not `adapters/factory.py` — adapters/ was READ ONLY; documents win over prompt (CLAUDE.md v3)
- `confidence_threshold` as module default (0.7) not config — config/schema.py was READ ONLY; **SPEC-005 drift flagged — add to housekeeping**
- mypy overrides extended for openai/anthropic/ollama — same numpy PEP 695 pattern as Phase 2
- No MCP added — ADR-014 mandates direct API calls in Phase 4

---

### ⏳ Phase 5 — Architecture Layer
**Status:** Named, not started  
**Target:** Post-Phase 4 validation with design partners

**What Architecture Intelligence means:**
- Phase 4 AI answers: "Why did this pipeline fail?"
- Phase 5 AI answers: "What architecture should this pipeline use?"

**Capabilities planned:**
- Tool selection reasoning (dbt vs SQLMesh, Fivetran vs dlt, DuckDB vs Snowflake)
- Cost and reliability architecture comparison
- ADR compliance checking for proposed changes
- Continuous architecture monitoring across the stack

**SPECs to write:** SPEC-011 (Architecture Intelligence)  
**ADRs to write:** ADR-015 (Architecture Intelligence scope), ADR-016 (can_auto_fix=True gate)  
**Agent activating:** documentation-engineer (post-implementation doc updates)

---

## Post-Phase-4 Housekeeping (before Phase 5 or design partner outreach)

```
□ SPEC-005 drift: add confidence_threshold to pipelinekit.yaml config schema
  (currently module default 0.7 — should be configurable per SPEC-005)
□ Update config/schema.py DiagnosticsSection to include confidence_threshold field
□ Update SPEC-002 to reflect DiagnosticsSection extension
□ Confirm CI green on GitHub after 47bdd51 push
□ Update HANDOVER-TO-NEW-CHAT.md to reflect Phase 4 complete
□ Write ICP-001, ICP-002, ICP-003 stubs (ICP-004 already written)
□ Update PRD in-file (not just the summary doc) with v2 executive summary
□ Update Strategic Operating Document with market context section
```

---

## What PipelineKit Can Do Now (Post Phase 4)

A user with PipelineKit installed can:

```
pipelinekit init                          Initialize a project
pipelinekit validate                      Validate configuration
pipelinekit validate --contracts          Validate data contracts
pipelinekit run                           Execute pipeline
pipelinekit run --dry-run                 Validate without executing
pipelinekit status                        View run history
pipelinekit blueprint list                List installed blueprints
pipelinekit blueprint validate            Validate blueprint structure
pipelinekit blueprint info <name>         Show blueprint details
pipelinekit diagnose                      AI root cause analysis (last run)
pipelinekit diagnose <run_id>             AI root cause analysis (specific run)
pipelinekit diagnose --approve            Review recommended actions
```

Blueprint #001 (Postgres → Snowflake) is deployable.  
AI diagnostics work with Anthropic, OpenAI, or local Ollama.  
CI gates every push.  
Email alerts on failure via Resend.

**This is a complete product.** Phase 5 adds Architecture Intelligence on top of it.

---

## Repository Structure — Current

```
src/pipelinekit/
├── core/           ✅ errors (PK error hierarchy + DiagnosticsError + LLMError)
├── config/         ✅ PipelineConfig (8 sections)
├── state/          ✅ SQLite (pipeline_runs, validation_runs, contract_results, diagnostic_results)
├── cli/            ✅ init, validate, status, run, blueprint, diagnose
├── runtime/        ✅ PipelineRunner, PipelineResult
├── adapters/       ✅ dlt, dbt, Soda, Resend
├── contracts/      ✅ ContractValidator (6 checks)
├── blueprints/     ✅ BlueprintRegistry, BlueprintValidator
├── notifications/  ✅ NotificationDispatcher, templates
└── ai/             ✅ LLMProvider, EvidenceCollector, DiagnosticsEngine, 3 providers

blueprints/
└── postgres-to-snowflake/  ✅ Blueprint #001 — complete

.github/workflows/ci.yml    ✅ CI pipeline live
.mcp/registry/servers.md    ✅ Resend entry (Phase 3)
```

**Total tests:** 151 | **Coverage:** 82.16% | **Source files:** 55

---

## Decision Log

| Date | Decision | Reason |
|---|---|---|
| 2026-06-24 | typer `>=0.16,<1.0` | click 8.4 compatibility |
| 2026-06-24 | `cwd: Path \| None = None` | Path.cwd() binds at import time |
| 2026-06-24 | Feature branch per sprint | Safety — fast-forward after verification |
| 2026-06-25 | mypy overrides dlt/soda/openai/anthropic/ollama | numpy PEP 695 crash Python 3.13 |
| 2026-06-25 | AcceptedValuesRule as plain dict | Pydantic v2 removed `__root__` |
| 2026-06-25 | run --dry-run exits 0 | Informational preview |
| 2026-06-25 | Resend adapter (ADR-013) | First MCP — email alerts Phase 3 |
| 2026-06-25 | Control plane → intelligence layer | Avoid orchestrator bucket post-merger |
| 2026-06-25 | TTTD 5 dimensions as design principles | No benchmarks without real customer data |
| 2026-06-25 | ICP-004 Mixed-Stack Enterprise | Post-merger customer opportunity |
| 2026-06-25 | Phase 5 Architecture Intelligence named | Pre-empt decision layer opportunity |
| 2026-06-25 | Provider factory in ai/providers/ not adapters/ | adapters/ READ ONLY — documents win |
| 2026-06-25 | confidence_threshold as module default | config/schema.py READ ONLY this phase — drift flagged |
| 2026-06-25 | ADR-014: direct API calls not MCP for Phase 4 | MCP complexity unjustified for Phase 4 frequency |
| 2026-06-25 | can_auto_fix forced False in engine | ADR-007 + Smell 13 — AI boundary enforced by design |

---

## Key File Locations

| Artifact | Path |
|---|---|
| Master Architecture v2 | `docs/institutional-memory/strategy-archive/PIPELINEKIT-MASTER-ARCHITECTURE.md` |
| Architectural Smells v3 | `docs/reference/Architectural-Smells.md` |
| Phase 4 Sprint Prompt | `docs/institutional-memory/strategy-archive/PHASE-4-CLAUDE-CODE-PROMPT.md` |
| SPEC-005 AI Diagnostics | `docs/specifications/SPEC-005-AI-Diagnostics.md` |
| ADR-014 AI Provider Governance | `docs/decisions/ADR-014-AI-Provider-MCP-Layer.md` |
| Diagnostic Schema | `schemas/diagnostic.schema.json` |
| Product Constitution | `docs/constitution/Product-Constitution.md` |

---

## Verification Commands

```powershell
cd C:\Users\HP\Documents\pipelinekit
poetry run pytest --cov=src/pipelinekit --cov-fail-under=80
poetry run ruff check .
poetry run black --check .
poetry run mypy src/pipelinekit
```
