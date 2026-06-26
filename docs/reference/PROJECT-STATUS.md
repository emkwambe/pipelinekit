# PipelineKit — Project Status

**File:** `docs/reference/PROJECT-STATUS.md`  
**Rule:** Updated only at the end of each completed phase. Never mid-sprint.  
**Owner:** Command Center (Claude Chat)

---

## Current State

**Active Phase:** Phase 6 — Blueprint Catalog + Ecosystem  
**Last Completed:** Sprint 6-3 — Blueprint #002 Salesforce → Snowflake  
**Last Updated:** June 26, 2026  
**Main Branch:** `04ffd50` (Sprint 6-3)

---

## Phase Completion Record

### ✅ Phase 1 — Foundation | `8d8865f` | 36 tests | 92.65%
### ✅ Phase 2 — Data Layer | `f337cfe` | 87 tests | 84.70%
### ✅ Phase 3 — Trust Layer | `d938e50` | 112 tests | 82.00%
### ✅ Phase 4 — Intelligence Layer | `47bdd51` | 151 tests | 82.16%
### ✅ Phase 5 — Architecture Layer | `ede343a` | 174 tests | 81.27%
### ✅ Provider Diversity (ADR-016) | `d6e4a4b` | 184 tests | 5 providers
### ✅ Sprint 6-1 — pipelinekit health | `c613640` | 209 tests | 82.42%
### ✅ Sprint 6-2a — dlt Adapter + Credential Wiring | `fe6341f` | 225 tests | 82.67%
### ✅ Blueprint #001 Local Verification | `d01ca36` | 1,000 rows | 0.7 min

---

### ✅ Sprint 6-3 — Blueprint #002 Salesforce → Snowflake
**Completed:** June 26, 2026  
**Commit:** `04ffd50` | 229 tests | 82.42% | 19 files +763/−4

**What was built:**
- `blueprints/salesforce-to-snowflake/` — all 8 required assets
- `src/pipelinekit/config/schema.py` — username, security_token fields added
- `src/pipelinekit/adapters/ingestion/dlt/adapter.py` — Salesforce source handling (lazy import)
- `scripts/verify-blueprint-002.ps1` — verification harness with -Local synthetic DuckDB seed
- `tests/blueprints/test_blueprint_002.py` — 4 blueprint tests

**Quality gates:**
| Gate | Result |
|---|---|
| pytest | 229 passed (225 prior + 4 new) |
| coverage | 82.42% |
| ruff / black / mypy | Clean |
| blueprint validate | Both blueprints valid |
| Blueprint #001 | Untouched ✅ |

**Key decisions:**
- blueprint.json extended with contracts + dlt_source/dlt_destination — schema requires them
- contracts/opportunities.yaml uses real ContractDefinition shape — SPEC-013 snippet was wrong (Smell 12)
- `dlt[salesforce]` not added to pyproject.toml — not on allowed-modify list; lazy import pattern used; add before real Salesforce run
- Local verification uses synthetic DuckDB seed — no Salesforce API required

**SPEC-013 drift to fix:**
- blueprint.json snippet needs contracts + dlt fields added
- contracts/opportunities.yaml snippet needs real ContractDefinition shape
- dlt[salesforce] dependency decision needs documenting

---

## Blueprint Catalog

| Blueprint | Status | Local Verified | Production Verified |
|---|---|---|---|
| postgres-to-snowflake | ✅ Built | ✅ 1,000 rows, 0.7 min | ⏳ Snowflake credentials needed |
| salesforce-to-snowflake | ✅ Built | ⏳ Pending -Local run | ⏳ Salesforce credentials needed |

---

## Phase 6 Sprint Queue

```
✅ Sprint 6-1:   pipelinekit health              c613640
✅ Sprint 6-2a:  dlt adapter + credential wiring  fe6341f
✅ Blueprint #001 local verification              d01ca36
✅ Sprint 6-3:   Blueprint #002 Salesforce → SF   04ffd50
⏳ Blueprint #002 local verification              -Local run pending
⏳ Sprint 6-2b:  PK-CONFIG-006 wiring
⏳ Sprint 6-4:   Blueprint #003 Stripe → Snowflake
📋 Sprint 6-5:   AI Blueprint Generation
📋 Sprint 6-6:   Remote Blueprint Registry
📋 Sprint 6-7:   Migration Intelligence
```

---

## Hardening Checklist

```
✅ pipelinekit health (SPEC-012)
✅ dlt adapter real implementation (ADR-017)
✅ Blueprint #001 locally verified (1,000 rows, 0.7 min)
✅ Blueprint #002 built (all 8 assets)
□  Blueprint #002 local verification (-Local run)
□  .gitignore generalized for all blueprint dbt artifacts
□  SPEC-013 drift reconciliation
□  dlt[salesforce] dependency decision
□  PK-CONFIG-006 wired into validate/run
□  Blueprint #001 production Snowflake verification
□  SPEC-005 confidence_threshold drift fix
□  ICP-001, ICP-002, ICP-003 stubs
□  CI green confirmed on GitHub
```

---

## Repository Numbers

**Tests:** 229 | **Coverage:** 82.42% | **Source files:** ~70  
**Blueprints:** 2 | **AI providers:** 5 | **ADRs:** 017 | **SPECs:** 013

---

> **PipelineKit is the AI-native operating system for trusted analytics pipelines.**
