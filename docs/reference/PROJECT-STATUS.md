# PipelineKit — Project Status

**File:** `docs/reference/PROJECT-STATUS.md`  
**Rule:** Updated only at the end of each completed phase. Never mid-sprint.  
**Owner:** Command Center (Claude Chat)

---

## Current State

**Active Phase:** Phase 4 — Intelligence Layer  
**Last Completed Phase:** Phase 3 — Trust Layer  
**Last Updated:** June 25, 2026  
**Main Branch:** `d938e50` (Phase 3 trust layer)

---

## Phase Completion Record

### ✅ Phase 1 — Foundation
**Completed:** June 25, 2026  
**Commit:** `8d8865f`

**What was built:**
- `pyproject.toml` — Poetry project, typer `>=0.16,<1.0`, pydantic v2, rich, pyyaml
- `src/pipelinekit/core/errors.py` — PK error hierarchy
- `src/pipelinekit/config/schema.py` — PipelineConfig Pydantic model, all 8 sections
- `src/pipelinekit/config/loader.py` — load_config(), config_exists(), write_default_config()
- `src/pipelinekit/state/db.py` — SQLite state store
- `src/pipelinekit/cli/` — init, validate, status commands
- `tests/` — 36 tests, 92.65% coverage

**Quality gates:** pytest 36 passed 92.65% | ruff ✅ | black ✅ | mypy 13 files ✅  
**SPECs satisfied:** SPEC-001, SPEC-002, SPEC-007, SPEC-010  
**Agents active:** cli-engineer, quality-engineer  
**Key decisions:**
- typer pinned to `>=0.16,<1.0` — click 8.4 broke make_metavar() in typer <0.16
- `cwd: Path | None = None` pattern — Path.cwd() default binds at import time
- `ensure_gitignore_entry()` in state/db.py — SPEC-001 forbids file I/O in CLI
- PK-CONFIG-005 added — write failure needed a code not in Error-Codes.md

---

### ✅ Phase 2 — Data Layer
**Completed:** June 25, 2026  
**Commit:** `f337cfe`

**What was built:**
- `src/pipelinekit/runtime/` — PipelineRunner, PipelineResult, StepResult, executor
- `src/pipelinekit/adapters/` — BaseAdapter, AdapterFactory, dlt/dbt/Soda adapters
- `src/pipelinekit/contracts/` — ContractDefinition, ContractViolation, ContractResult, ContractValidator (6 checks)
- `src/pipelinekit/cli/run.py` — pipelinekit run + --dry-run
- `src/pipelinekit/cli/validate.py` — --contracts flag
- `src/pipelinekit/state/db.py` — contract_results table + insert_contract_result()
- `tests/runtime/`, `tests/adapters/`, `tests/contracts/` — 51 new tests

**Quality gates:** pytest 87 passed 84.70% | ruff ✅ | black 57 files ✅ | mypy 33 files ✅  
**SPECs satisfied:** SPEC-003, SPEC-004, SPEC-009  
**Agent activated:** runtime-engineer  
**Key decisions:**
- Python 3.13 + dlt 1.28 + dbt-core 1.x + soda-core 3.5.6 resolved cleanly
- Scoped `[[tool.mypy.overrides]]` for dlt.*/soda.* — numpy PEP 695 crash prevention
- `run --dry-run` always exits 0 — informational preview
- AcceptedValuesRule as plain dict — Pydantic v2 removed `__root__`

---

### ✅ Phase 3 — Trust Layer
**Completed:** June 25, 2026  
**Commit:** `d938e50`  
**Branch:** `phase-3-trust-layer` → fast-forward merged to `main`

**What was built:**
- `src/pipelinekit/blueprints/` — models, registry (local scan, never raises), validator (jsonschema)
- `src/pipelinekit/notifications/` — models, templates (3 events, structured evidence), dispatcher (never raises, only when enabled)
- `src/pipelinekit/adapters/alerts/resend/adapter.py` — ResendNotificationAdapter (BYOK via RESEND_API_KEY, all imports isolated)
- `blueprints/postgres-to-snowflake/` — Blueprint #001 complete: dlt pipeline, dbt project (staging + core models), orders contract, Soda checks, alerts config, honest README + runbook
- `src/pipelinekit/cli/blueprint.py` — blueprint list, validate, info commands
- `.github/workflows/ci.yml` — CI pipeline (Python 3.13, ruff, black, mypy, pytest ≥80%)
- `.mcp/registry/servers.md` — Resend MCP entry (first MCP in the stack)
- `src/pipelinekit/core/errors.py` — BlueprintError added
- `src/pipelinekit/config/schema.py` — NotificationsSection extended (provider, from_address, recipients, notify_on — all backward-compatible with defaults)
- `src/pipelinekit/runtime/runner.py` — notification dispatch in finally block after state update

**Quality gates (all green):**
| Gate | Result |
|---|---|
| pytest --cov-fail-under=80 | 112 passed (87 prior + 25 new), 82.00% coverage |
| ruff check | All checks passed |
| black --check | 78 files unchanged |
| mypy src/pipelinekit | No issues, 45 files |

**Per-module coverage vs SPEC targets:**
| Module | Coverage | Target |
|---|---|---|
| blueprints/models | 100% | ≥80% ✓ |
| blueprints/registry | 97% | ≥80% ✓ |
| blueprints/validator | 100% | ≥80% ✓ |
| notifications/models | 100% | ≥80% ✓ |
| notifications/dispatcher | 94% | ≥80% ✓ |
| notifications/templates | 89% | ≥80% ✓ |
| adapters/alerts/resend | 82% | ≥80% ✓ |

**SPECs satisfied:** SPEC-006, SPEC-008  
**Agents activated:** blueprint-engineer, release-engineer  
**MCP entered:** Resend (Phase 3, email alerts only)  
**Key decisions:**
- Error-Codes.md not updated — not on Phase 3 allowed-modify list. PK-BLUEPRINT-* and PK-NOTIFY-* codes defined in SPECs and code. **Post-Phase-3 housekeeping: add to Error-Codes.md**
- NotificationsSection extended with backward-compatible fields (all have defaults, 87 prior tests unaffected)
- Runner finally restructured minimally — PipelineResult built inside finally so notifications can reference it; validate() untouched
- No sources.yml in dbt project — not on allowed-create list; strict boundary compliance
- Blueprint #001 deploy target: < 60 minutes (design principle, not yet a measured benchmark)

---

### ⏳ Phase 4 — Intelligence Layer
**Status:** In progress  
**Target:** Weeks 7+

**What will be built:**
- `src/pipelinekit/ai/` — LLMProvider Protocol, EvidenceCollector, DiagnosticsEngine
- `src/pipelinekit/ai/providers/` — OpenAI, Anthropic, Ollama adapters
- `pipelinekit diagnose` — AI-assisted root cause analysis
- Full MCP layer — `.mcp/servers/` populated
- `pipelinekit doctor --ai` flag

**SPECs to write:** SPEC-005 (AI Diagnostics)  
**ADRs to write:** ADR-014 (AI provider MCP layer)  
**Agent activating:** diagnostics-engineer  
**MCP entering:** Full AI provider MCP layer

**Definition of done:**
```
pipelinekit diagnose         AI root cause analysis exits 0
diagnostic.schema.json       all AI output validates against it
LLMProvider interface        OpenAI + Anthropic + Ollama implemented
pytest                       all tests green, coverage >= 80%
ruff / black / mypy          all clean
```

---

### 📋 Phase 5 — Architecture Layer
**Status:** Named, not started  
**Target:** Post-Phase 4

**What Architecture Intelligence means:**
- Phase 4 AI answers: "Why did this pipeline fail?"
- Phase 5 AI answers: "What architecture should this pipeline use?"

**Capabilities planned:**
- Tool selection reasoning (dbt vs SQLMesh, Fivetran vs dlt, DuckDB vs Snowflake)
- Cost and reliability architecture comparison
- ADR compliance checking for proposed changes
- Continuous architecture monitoring

**SPECs to write:** SPEC-011 (Architecture Intelligence)  
**ADRs to write:** ADR-015 (Architecture Intelligence scope)

---

## Post-Phase-3 Housekeeping (do before Phase 4 sprint fires)

```
□ Add PK-BLUEPRINT-001 to 004 to docs/reference/Error-Codes.md
□ Add PK-NOTIFY-001 to 004 to docs/reference/Error-Codes.md
□ Write ADR-013 (Resend MCP governance — formalize what master arch authorized)
□ Update SPEC-004 (Contracts) — cwd pattern drift from Phase 2
□ Update SPEC-002 (Configuration) — cwd pattern drift from Phase 2
□ Add sources.yml to Blueprint #001 dbt project
□ Update placeholder status headers across docs/specifications/ stubs
□ Confirm CI green on GitHub after push
```

---

## Repository Structure — Current

```
pipelinekit/
├── .claude/CLAUDE.md                    ✅ v3 — TTTD dimensions, intelligence layer
├── .github/workflows/ci.yml             ✅ Phase 3 — CI pipeline live
├── .mcp/registry/servers.md             ✅ Resend entry added
├── agents/                              ✅ 7 agent definitions
├── blueprints/
│   └── postgres-to-snowflake/           ✅ Blueprint #001 — complete
├── contracts/                           ✅ All 4 contracts
├── docs/
│   ├── reference/
│   │   ├── Architectural-Smells.md      ✅ v3 — 16 smells with direction
│   │   └── PROJECT-STATUS.md           ✅ This file
│   ├── specifications/
│   │   ├── SPEC-001 to SPEC-004        ✅ Approved, satisfied
│   │   ├── SPEC-005-AI-Diagnostics     📋 TBD stub — write pre-Phase 4
│   │   ├── SPEC-006-Blueprint-Engine   ✅ Approved, satisfied
│   │   ├── SPEC-007-State-Store        ✅ Approved, satisfied
│   │   ├── SPEC-008-Notification       ✅ Approved, satisfied
│   │   ├── SPEC-009-Provider-Adapters  ✅ Approved, satisfied
│   │   ├── SPEC-010-Testing-Gates      ✅ Approved, satisfied
│   │   └── SPEC-011-Arch-Intelligence  📋 TBD stub — write pre-Phase 5
│   └── institutional-memory/
│       ├── customers/ICP-004           ✅ Mixed-Stack Enterprise added
│       └── strategy-archive/
│           ├── PIPELINEKIT-MASTER-ARCHITECTURE.md  ✅ v2 — Phase 5 named
│           ├── VISION-STATEMENT-UPDATE.md          ✅ v2 — intelligence layer
│           └── PRD-Executive-Summary-v2.md         ✅ positive framing, TTTD
├── schemas/                             ✅ blueprint + diagnostic schemas
├── src/pipelinekit/
│   ├── core/                            ✅ Phase 1 + BlueprintError (Phase 3)
│   ├── config/                          ✅ Phase 1 + NotificationsSection ext.
│   ├── state/                           ✅ Phase 1 + Phase 2 extension
│   ├── cli/ (init,validate,status,run,blueprint) ✅ Phase 1-3
│   ├── runtime/                         ✅ Phase 2 + notification dispatch
│   ├── adapters/ (dlt,dbt,Soda,Resend)  ✅ Phase 2-3
│   ├── contracts/                       ✅ Phase 2
│   ├── blueprints/                      ✅ Phase 3
│   ├── notifications/                   ✅ Phase 3
│   ├── observability/                   📋 Phase 4 (doctor/freshness/reporter)
│   └── ai/                              📋 Phase 4
└── tests/
    ├── cli/ + config/ + state/          ✅ Phase 1 (36 tests)
    ├── runtime/ + adapters/ + contracts/ ✅ Phase 2 (51 tests)
    ├── blueprints/ + notifications/     ✅ Phase 3 (25 tests)
    └── ai/                              📋 Phase 4
```

**Total tests:** 112 | **Coverage:** 82.00% | **Source files:** 45

---

## Decision Log

| Date | Decision | Reason |
|---|---|---|
| 2026-06-24 | typer pinned to `>=0.16,<1.0` | click 8.4 broke make_metavar() |
| 2026-06-24 | `cwd: Path \| None = None` pattern | Path.cwd() binds at import time |
| 2026-06-24 | ensure_gitignore_entry() in state/db.py | SPEC-001 forbids file I/O in CLI |
| 2026-06-24 | PK-CONFIG-005 added | Write failure needed a code |
| 2026-06-24 | Feature branch per sprint | Safety — fast-forward merge after verification |
| 2026-06-25 | mypy overrides for dlt.*/soda.* | numpy PEP 695 crash under Python 3.13 |
| 2026-06-25 | dlt connectivity via stdlib socket | Fast, deterministic, no credentials |
| 2026-06-25 | AcceptedValuesRule as plain dict | Pydantic v2 removed `__root__` |
| 2026-06-25 | run --dry-run always exits 0 | Informational preview per DoD |
| 2026-06-25 | Error-Codes.md deferred Phase 3 | Not on allowed-modify list — housekeeping |
| 2026-06-25 | NotificationsSection extended | Backward-compatible; all fields have defaults |
| 2026-06-25 | Runner finally restructured | PipelineResult needed inside finally for notifications |
| 2026-06-25 | No sources.yml in Blueprint #001 | Not on allowed-create list; strict boundary |
| 2026-06-25 | Control plane → intelligence layer | dbt/Fivetran merger — avoid orchestrator bucket |
| 2026-06-25 | TTTD 5 dimensions as design principles | Not metrics until real usage data exists |
| 2026-06-25 | ICP-004 Mixed-Stack Enterprise added | Post-merger customer model expansion |
| 2026-06-25 | Phase 5 Architecture Intelligence named | Pre-empt the decision layer opportunity |

---

## Key File Locations

| Artifact | Path |
|---|---|
| Master Architecture v2 | `docs/institutional-memory/strategy-archive/PIPELINEKIT-MASTER-ARCHITECTURE.md` |
| Architectural Smells v3 | `docs/reference/Architectural-Smells.md` |
| Phase 1 Sprint Prompt | `docs/institutional-memory/strategy-archive/PHASE-1-CLAUDE-CODE-PROMPT.md` |
| Phase 2 Sprint Prompt | `docs/institutional-memory/strategy-archive/PHASE-2-CLAUDE-CODE-PROMPT.md` |
| Phase 3 Sprint Prompt | `docs/institutional-memory/strategy-archive/PHASE-3-CLAUDE-CODE-PROMPT.md` |
| Product Constitution | `docs/constitution/Product-Constitution.md` |
| All ADRs | `docs/decisions/ADR-000-Foundational-Architecture-Decisions.md` |
| Error Codes | `docs/reference/Error-Codes.md` |

---

## Verification Commands

```powershell
cd C:\Users\HP\Documents\pipelinekit
poetry run pytest --cov=src/pipelinekit --cov-fail-under=80
poetry run ruff check .
poetry run black --check .
poetry run mypy src/pipelinekit
```

All four must exit 0 before any phase is considered complete.
