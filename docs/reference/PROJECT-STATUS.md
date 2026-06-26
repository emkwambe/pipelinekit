# PipelineKit — Project Status

**File:** `docs/reference/PROJECT-STATUS.md`  
**Rule:** Updated only at the end of each completed phase. Never mid-sprint.  
**Owner:** Command Center (Claude Chat)

---

## Current State

**Active Phase:** Phase 6 — Complete  
**Last Completed:** Sprint 6-7 — Migration Intelligence  
**Last Updated:** June 26, 2026  
**Main Branch:** `91f39c3`

---

## Phase 6 — Complete Sprint Record

| Sprint | Commit | Tests | What shipped |
|---|---|---|---|
| 6-1 pipelinekit health | `c613640` | 209 | Health commands, pip-audit |
| 6-2a dlt adapter | `fe6341f` | 225 | Real dlt, credential wiring, ADR-017 |
| Blueprint #001 verified | `d01ca36` | — | 1,000 rows, 0.7 min |
| 6-3 Blueprint #002 | `04ffd50` | 229 | Salesforce → Snowflake |
| 6-5 AI Blueprint Proposal | `9fc034a`+ | 256 | ADR-018, state machine, provenance |
| Blueprint #003 AI-proposed | `617e5ec` | — | stripe-to-snowflake |
| 6-6 Remote Registry | `8d40dbd` | 268 | search, install, catalog, ADR-019 |
| **6-7 Migration Intelligence** | **`91f39c3`** | **286** | **Airbyte/Fivetran/Python parsers, ADR-020** |

---

### ✅ Sprint 6-7 — Migration Intelligence
**Completed:** June 26, 2026  
**Commit:** `91f39c3` | 286 tests | 81.40% | 18 new tests

**What was built:**
- `src/pipelinekit/ai/migration_models.py` — MigrationProposal, MappingResult, MigrationGap, MappingStatus
- `src/pipelinekit/ai/config_parsers.py` — AirbyteParser, FivetranParser, PythonParser (ast.parse only — never exec), MigrationConfigParser router
- `src/pipelinekit/ai/migration_analyzer.py` — MigrationAnalyzer (analyze + apply)
- `src/pipelinekit/cli/migrate.py` — `pipelinekit migrate analyze`
- All 5 providers — `analyze_migration()` implemented
- MigrationError + PK-MIGRATE-001 to 005

**Trust model:**
- AI reads existing config → proposes migration → human approves → apply() writes
- `apply()` writes `pipelinekit.proposed.yaml` — never `pipelinekit.yaml`
- Blocking gaps prevent apply without `--force`
- `can_auto_apply` always False
- `PythonParser` uses `ast.parse()` only — never exec/eval/subprocess

**ADR satisfied:** ADR-020 (Migration Intelligence Governance)

---

## CLI Surface — Complete

```
pipelinekit init / validate / run / status
pipelinekit blueprint list / validate / info / search / install
pipelinekit diagnose / architect / health
pipelinekit generate blueprint --plan/--interactive
pipelinekit generate show <plan_id>
pipelinekit apply plan <plan_id> [--interactive]
pipelinekit migrate analyze <config> [--apply] [--force]
```

---

## Blueprint Catalog

| Blueprint | Built | Local Verified | Registry | Source |
|---|---|---|---|---|
| postgres-to-snowflake | ✅ | ✅ 1,000 rows | ⏳ deploy pending | Hand-crafted |
| salesforce-to-snowflake | ✅ | ✅ 800 rows | ⏳ deploy pending | Hand-crafted |
| stripe-to-snowflake | ✅ | ⏳ pending | ⏳ deploy pending | **AI-proposed** |

---

## Real Infrastructure Testing Plan (6-6 + 6-7)

These must be completed before design partner outreach:

### Sprint 6-6 Registry Testing
```
□ Create pipelinekit-registry GitHub repo
□ Add v1/catalog.json with 3 blueprint entries
□ Zip each blueprint: postgres-to-snowflake-1.0.0.zip etc.
□ Deploy to Cloudflare Pages at registry.pipelinekit.dev
□ Run: pipelinekit blueprint search stripe
□ Run: pipelinekit blueprint install postgres-to-snowflake
□ Verify install writes to blueprints/ and validates
□ Record verified test in PROJECT-STATUS
```

### Sprint 6-7 Migration Testing
```
□ Create sample Airbyte connection.json (postgres → snowflake)
□ Run: pipelinekit migrate analyze airbyte-connection.json
□ Verify: MigrationProposal shows mappings, gaps, confidence
□ Run: pipelinekit migrate analyze airbyte-connection.json --apply
□ Verify: pipelinekit.proposed.yaml written correctly
□ Run: pipelinekit validate (against proposed yaml)
□ Record verified test in PROJECT-STATUS
```

---

## Open Housekeeping

```
□ ADR-020 filename reconciliation (migration.py → migration_analyzer.py)
□ Archive ADR-018-Blueprint-Generation-Governance.md (superseded)
□ Archive SPEC-015-AI-Blueprint-Generation.md (superseded)
□ Blueprint #003 dbt parse + local verification
□ SPEC-013 drift reconciliation
□ ICP-001, ICP-002, ICP-003 stubs
□ PK-CONFIG-006 wired into validate/run
□ CI green confirmed on GitHub
```

---

## Repository Numbers

**Tests:** 286 | **Coverage:** 81.40% | **Blueprints:** 3  
**AI providers:** 5 | **ADRs:** 020 | **SPECs:** 017 | **State tables:** 8  
**CLI commands:** 13+ across 6 command groups

---

## What PipelineKit Can Do Now

```
Initialize and validate pipeline projects
Run pipelines (dlt ingestion, dbt transformation, Soda quality)
Enforce data contracts
Deploy production blueprints (3 available)
Alert on failures (Resend email)
Diagnose failures with AI root cause analysis (5 providers)
Reason about architecture decisions
Monitor health (deps, security, blueprints, specs, tests)
Propose new blueprints from source/destination specification
Search and install blueprints from registry
Analyze existing Airbyte/Fivetran/Python pipelines and propose migration
```

---

> **PipelineKit is the AI-native operating system for trusted analytics pipelines.**
