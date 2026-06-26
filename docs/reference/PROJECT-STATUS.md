# PipelineKit — Project Status

**File:** `docs/reference/PROJECT-STATUS.md`  
**Rule:** Updated only at the end of each completed phase. Never mid-sprint.  
**Owner:** Command Center (Claude Chat)

---

## Current State

**Active Phase:** Phase 6 — Blueprint Catalog + Ecosystem  
**Last Completed:** Sprint 6-5 — AI Blueprint Proposal + Blueprint #003  
**Last Updated:** June 26, 2026  
**Main Branch:** `62516f7`

---

## Phase Completion Record

### ✅ Phases 1–5 + Provider Diversity — See prior entries

### ✅ Sprint 6-1 — pipelinekit health | `c613640` | 209 tests
### ✅ Sprint 6-2a — dlt Adapter + Credential Wiring | `fe6341f` | 225 tests
### ✅ Blueprint #001 Local Verification | `d01ca36` | 1,000 rows | 0.7 min
### ✅ Sprint 6-3 — Blueprint #002 Salesforce → Snowflake | `04ffd50` | 229 tests

---

### ✅ Sprint 6-5 — AI Blueprint Proposal + Blueprint #003
**Completed:** June 26, 2026  
**Key commits:**
- `9fc034a` — Sprint 6-5 core (AI Blueprint Proposal)
- `d3c6240` — max_tokens 16000 fix
- `e4e534f` — shared parser robust fix (all 5 providers)
- `822f23a` — apply() path-doubling fix
- `617e5ec` — Blueprint #003 stripe-to-snowflake committed
- `62516f7` — ruff fix on AI-generated pipeline.py

**Tests:** 256 | **Coverage:** 80.68% | **All gates green**

**What was built:**
- `src/pipelinekit/ai/proposal_models.py` — BlueprintProposal, ProposedAsset, AssetState (6 states)
- `src/pipelinekit/ai/blueprint_proposer.py` — BlueprintProposer (propose + apply)
- `src/pipelinekit/ai/adapter_registry.py` — AdapterCapabilityRegistry
- `src/pipelinekit/cli/generate.py` — `pipelinekit generate blueprint --plan/--interactive`, `pipelinekit apply plan`
- `schemas/blueprint_proposal.schema.json`
- All 5 providers — `propose_blueprint()` implemented
- Blueprint #003 — stripe-to-snowflake (AI-proposed, human-approved)

**Sprint 6-5 bugs fixed during verification:**
- Anthropic max_tokens 8192 truncated 13-asset proposals → raised to 16000
- Shared parser did not handle markdown fences or preamble → `_extract_json_object()` added
- `apply()` wrote to `blueprints/<name>/<name>/` → `_relative_path()` strips prefix

**ADR satisfied:** ADR-018 (Blueprint Proposal Governance)  
**Governance model enforced:**
- `proposed → approved → written → validated` state machine
- `PK-GEN-006` fires before AI call for unsupported sources
- Provenance (9 fields) on every asset, stripped on write
- `can_auto_apply` always False

---

## Blueprint Catalog

| Blueprint | Built | Local Verified | How Built |
|---|---|---|---|
| postgres-to-snowflake | ✅ | ✅ 1,000 rows, 0.7 min | Hand-crafted |
| salesforce-to-snowflake | ✅ | ✅ 800 rows, 0.2 min | Hand-crafted |
| stripe-to-snowflake | ✅ | ⏳ dbt parse pending | **AI-proposed** ← first |

---

## CLI Surface — Complete

```
pipelinekit init / validate / run / status
pipelinekit blueprint list / validate / info
pipelinekit diagnose / architect / health
pipelinekit generate blueprint --plan/--interactive
pipelinekit generate show <plan_id>
pipelinekit apply plan <plan_id>
```

---

## Phase 6 Sprint Queue

```
✅ Sprint 6-1:   pipelinekit health
✅ Sprint 6-2a:  dlt adapter + credential wiring
✅ Sprint 6-3:   Blueprint #002 Salesforce → Snowflake
✅ Sprint 6-5:   AI Blueprint Proposal + Blueprint #003
⏳ Blueprint #003 dbt parse + local verification
⏳ Sprint 6-2b:  PK-CONFIG-006 wiring
⏳ Sprint 6-6:   Remote Blueprint Registry
⏳ Sprint 6-7:   Migration Intelligence
📋 Cleanup:      Archive superseded "Generation" ADR/SPEC files
📋 Enhancement:  apply() auto-format AI-generated .py assets
```

---

## Hardening Checklist

```
✅ AI Blueprint Proposal system (ADR-018, SPEC-015)
✅ Blueprint #003 AI-proposed and on main
✅ State machine enforced (proposed→approved→written)
✅ Ruff clean repo-wide (including AI-generated code)
□  Blueprint #003 dbt parse + local verification
□  Blueprint #001 production Snowflake verification
□  PK-CONFIG-006 wired
□  Archive superseded Generation files
□  ICP-001, ICP-002, ICP-003 stubs
□  CI green confirmed
```

---

## Repository Numbers

**Tests:** 256 | **Coverage:** 80.68% | **Blueprints:** 3 (1 AI-proposed)  
**AI providers:** 5 | **ADRs:** 018 | **SPECs:** 015 | **State tables:** 7

---

> **PipelineKit is the AI-native operating system for trusted analytics pipelines.**
