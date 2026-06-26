# PipelineKit — Project Status

**File:** `docs/reference/PROJECT-STATUS.md`  
**Rule:** Updated only at the end of each completed phase. Never mid-sprint.  
**Owner:** Command Center (Claude Chat)

---

## Current State

**Active Phase:** Phase 6 — Complete (Catalog + Ecosystem)  
**Last Completed:** Sprint 6-6 — Remote Blueprint Registry  
**Last Updated:** June 26, 2026  
**Main Branch:** `8d40dbd`

---

## Phase 6 Completion Record

### ✅ Sprint 6-1 — pipelinekit health | `c613640` | 209 tests
### ✅ Sprint 6-2a — dlt Adapter + Credential Wiring | `fe6341f` | 225 tests
### ✅ Blueprint #001 Local Verification | `d01ca36` | 1,000 rows | 0.7 min
### ✅ Sprint 6-3 — Blueprint #002 Salesforce → Snowflake | `04ffd50` | 229 tests
### ✅ Sprint 6-5 — AI Blueprint Proposal | `9fc034a`+ | 256 tests
### ✅ Blueprint #003 — stripe-to-snowflake (AI-proposed) | `617e5ec`

---

### ✅ Sprint 6-6 — Remote Blueprint Registry
**Completed:** June 26, 2026  
**Commit:** `8d40dbd` | 268 tests | 81.10% | 10 files +793/−14

**What was built:**
- `src/pipelinekit/blueprints/remote.py` — RemoteRegistry, BlueprintCatalog, CatalogEntry
- `pipelinekit blueprint search <query>` — search remote catalog
- `pipelinekit blueprint install <name>` — download, validate, write
- Validation before write: schema + lenient 8-asset check (admits all 3 current blueprints)
- 24h catalog cache with offline graceful degradation
- `installed_blueprints` table in state.db
- RegistryError + PK-REGISTRY-001 to 005

**Trust model hardening (Sprint 6-5 authorized adjustments landed here):**
- `pipelinekit apply plan` — `--yes` removed; `--interactive` added; no generate→auto-apply shortcut
- AdapterCapabilityRegistry `verified` flag: postgres=true, salesforce/stripe=false
- `⚠ Unverified adapter source` warning in interactive review

**Quality gates:**
| Gate | Result |
|---|---|
| pytest | 268 passed (256 prior + 12 new) |
| coverage | 81.10% |
| ruff / black / mypy | Clean |

---

## The Phase 6 Arc — Complete

```
6-1  health      → programmed sustainability policy
6-2a dlt adapter → real credential wiring, Blueprint #001 verified
6-3  Blueprint #002 → Salesforce → Snowflake (hand-crafted, verified)
6-5  AI Proposal → Blueprint #003 Stripe (AI-proposed, human-approved)
6-6  Registry    → install/search/distribute blueprints
```

**The flywheel:**
```
Install blueprint → better AI proposals → better blueprints → install more
```

---

## Blueprint Catalog

| Blueprint | Built | Local Verified | Registry | Adapter Verified |
|---|---|---|---|---|
| postgres-to-snowflake | ✅ | ✅ 1,000 rows | ⏳ pending deploy | ✅ |
| salesforce-to-snowflake | ✅ | ✅ 800 rows | ⏳ pending deploy | ⚠ community-sourced |
| stripe-to-snowflake | ✅ AI-proposed | ⏳ dbt parse pending | ⏳ pending deploy | ⚠ community-sourced |

---

## CLI Surface — Complete

```
pipelinekit init / validate / run / status
pipelinekit blueprint list / validate / info / search / install
pipelinekit diagnose / architect / health
pipelinekit generate blueprint --plan/--interactive
pipelinekit generate show <plan_id>
pipelinekit apply plan <plan_id> [--interactive]
```

---

## Open Items Before Design Partner Outreach

```
□  Deploy registry — pipelinekit-registry Cloudflare Pages repo
   → catalog.json + 3 blueprint zips at registry.pipelinekit.dev
□  Blueprint #003 local verification (dbt parse + synthetic run)
□  Archive superseded ADR-018-Generation + SPEC-015-Generation files
□  Sprint 6-7: Migration Intelligence (ADR + SPEC first)
□  Sprint 6-2b: PK-CONFIG-006 wiring
□  Blueprint #001 production Snowflake verification
□  ICP-001, ICP-002, ICP-003 stubs
□  CI green confirmed on GitHub
```

---

## Repository Numbers

**Tests:** 268 | **Coverage:** 81.10% | **Blueprints:** 3  
**AI providers:** 5 | **ADRs:** 019 | **SPECs:** 016 | **State tables:** 8

---

> **PipelineKit is the AI-native operating system for trusted analytics pipelines.**
