# PipelineKit — Project Status

**File:** `docs/reference/PROJECT-STATUS.md`  
**Rule:** Updated only at the end of each completed phase. Never mid-sprint.  
**Owner:** Command Center (Claude Chat)

---

## Current State

**Active Phase:** Phase 6 — Blueprint Catalog + Ecosystem  
**Last Completed:** Sprint 6-5 — AI Blueprint Proposal  
**Last Updated:** June 26, 2026  
**Main Branch:** `9fc034a` (Sprint 6-5)

---

## Phase Completion Record

### ✅ Phases 1–5 + Provider Diversity
See prior PROJECT-STATUS entries. All complete.

### ✅ Sprint 6-1 — pipelinekit health | `c613640` | 209 tests | 82.42%
### ✅ Sprint 6-2a — dlt Adapter + Credential Wiring | `fe6341f` | 225 tests | 82.67%
### ✅ Blueprint #001 Local Verification | `d01ca36` | 1,000 rows | 0.7 min
### ✅ Sprint 6-3 — Blueprint #002 Salesforce → Snowflake | `04ffd50` | 229 tests | 82.42%

---

### ✅ Sprint 6-5 — AI Blueprint Proposal
**Completed:** June 26, 2026  
**Commit:** `9fc034a` | 251 tests | 80.21% | 19 files +1640/−3

**What was built:**
- `src/pipelinekit/ai/proposal_models.py` — BlueprintProposal, ProposedAsset, AssetState (6 states + transition enforcement), AssetProvenance (9 fields)
- `src/pipelinekit/ai/blueprint_proposer.py` — BlueprintProposer (propose + apply)
- `src/pipelinekit/ai/adapter_registry.py` — AdapterCapabilityRegistry (postgres, salesforce, stripe → snowflake, bigquery, duckdb)
- `src/pipelinekit/cli/generate.py` — `pipelinekit generate blueprint --plan/--interactive`, `pipelinekit generate show`, `pipelinekit apply plan`
- `schemas/blueprint_proposal.schema.json` — output contract
- All 5 providers — `propose_blueprint()` implemented
- `state/db.py` — blueprint_proposals table
- `core/errors.py` — ProposalError (PK-GEN-001 to 007)

**Quality gates:**
| Gate | Result |
|---|---|
| pytest | 251 passed (229 prior + 22 new) |
| coverage | 80.21% (above 80% minimum) |
| ruff / black / mypy | Clean |
| All 5 --help commands | Exit 0 |
| Existing blueprints | Untouched ✅ |

**Key decisions:**
- Anthropic MAX_TOKENS raised to 8192 — 1024 truncates 13-asset proposals
- Interactive loop at 44% coverage — hard to unit-test typer.prompt; important paths covered
- `dlt[stripe]` not added — not on allowed-modify list; declared in generated blueprint.json requires
- Naming: `BlueprintProposal` not `BlueprintGeneration` throughout — trust model is explicit

**The governance model (ADR-018):**
```
proposed → approved → written → validated
```
- `propose()` returns `BlueprintProposal` — zero files written
- `PK-GEN-006` fires before AI call for unsupported sources
- Provenance (9 fields) attached to every asset, stripped on write
- `can_auto_apply` always False
- `PK-GEN-007` on any state transition violation

---

## CLI Surface — Complete

```
pipelinekit init
pipelinekit validate [--contracts]
pipelinekit run [--dry-run]
pipelinekit status
pipelinekit blueprint list / validate / info <name>
pipelinekit diagnose [run_id] [--provider] [--approve]
pipelinekit architect analyze / check-adrs / compare
pipelinekit health [deps|security|blueprints|specs|tests] [--strict]
pipelinekit generate blueprint --source <s> --destination <d> --tables <t> [--plan|--interactive]
pipelinekit generate show <plan_id>
pipelinekit apply plan <plan_id>
```

---

## Blueprint Catalog

| Blueprint | Built | Local Verified | AI Proposable |
|---|---|---|---|
| postgres-to-snowflake | ✅ | ✅ 1,000 rows, 0.7 min | ✅ (pattern source) |
| salesforce-to-snowflake | ✅ | ✅ 800 rows, 0.2 min | ✅ (pattern source) |
| stripe-to-snowflake | 📋 | 📋 | ✅ Can be proposed now |

---

## Phase 6 Sprint Queue

```
✅ Sprint 6-1:   pipelinekit health
✅ Sprint 6-2a:  dlt adapter + credential wiring
✅ Sprint 6-3:   Blueprint #002 Salesforce → Snowflake
✅ Sprint 6-5:   AI Blueprint Proposal
⏳ Manual test:  pipelinekit generate blueprint --source stripe → Blueprint #003
⏳ Sprint 6-2b:  PK-CONFIG-006 wiring
⏳ Sprint 6-6:   Remote Blueprint Registry
⏳ Sprint 6-7:   Migration Intelligence
📋 Cleanup:      Archive superseded ADR-018/SPEC-015 "Generation" files
```

---

## Hardening Checklist

```
✅ pipelinekit health (SPEC-012)
✅ dlt adapter real implementation (ADR-017)
✅ Blueprint #001 locally verified
✅ Blueprint #002 locally verified
✅ AI Blueprint Proposal (ADR-018, SPEC-015)
✅ 6-state asset machine enforced
✅ AdapterCapabilityRegistry — unsupported sources blocked
✅ Provenance on every asset
□  Manual: pipelinekit generate blueprint --source stripe → review → apply → verify
□  Blueprint #001 production Snowflake verification
□  PK-CONFIG-006 wired into validate/run
□  Archive ADR-018-Blueprint-Generation-Governance.md (superseded)
□  Archive SPEC-015-AI-Blueprint-Generation.md (superseded)
□  SPEC-013 drift reconciliation
□  ICP-001, ICP-002, ICP-003 stubs
□  CI green confirmed on GitHub
```

---

## Repository Numbers

**Tests:** 251 | **Coverage:** 80.21% | **Source files:** ~75  
**Blueprints:** 2 (locally verified) | **AI providers:** 5  
**ADRs:** 018 | **SPECs:** 015 | **State tables:** 7

---

> **PipelineKit is the AI-native operating system for trusted analytics pipelines.**
