# PipelineKit — Phase 6 Sprint Plan
## Blueprint Catalog + Auto-Generation + Ecosystem

**Version:** 1.0  
**Date:** June 25, 2026  
**Owner:** Command Center  
**Governs:** All Phase 6 development sprints

---

## Phase 6 Thesis

Phase 1-5 built the operating system.  
Phase 6 builds the catalog and distribution layer on top of it.

The operating system is complete. The value compounds through blueprints — every blueprint installed is a customer who cannot easily leave, because leaving means rebuilding not just connectors but contracts, models, quality checks, and runbooks.

Phase 6 priority order is fixed. Do not skip ahead.

---

## Sprint 6-1: pipelinekit health (SPEC-012)

**Type:** Internal infrastructure  
**Effort:** Small (1 sprint, ~2 hours)  
**Blocks:** Nothing — but must ship before design partner outreach  
**SPEC:** SPEC-012-Health-Command-System.md (already written and committed)  
**ADR:** None required — within existing CLI architecture

**What it builds:**
```
src/pipelinekit/cli/health.py
src/pipelinekit/health/
├── deps.py
├── security.py
├── blueprints.py
├── specs.py
└── tests.py
tests/health/
```

**Why first:** Design partners need to be able to run `pipelinekit health` and see a green report. It is the first thing a technical evaluator runs after install. It also catches the `architecture.schema.json` adr_compliance type drift automatically via `pipelinekit health specs`.

**Schema fix included in this sprint:**
- Update `schemas/architecture.schema.json` — change `adr_compliance` from `"type": "object"` to `"type": "array"`
- This is the drift flagged in Phase 5. Fix it here.

---

## Sprint 6-2: Blueprint #002 — Salesforce → Snowflake

**Type:** Blueprint  
**Effort:** Medium (1 sprint, ~3 hours)  
**SPEC:** Write SPEC-013-Blueprint-002 before this sprint fires  
**ADR:** None required — follows SPEC-006 blueprint pattern

**What it builds:**
```
blueprints/salesforce-to-snowflake/
├── blueprint.json
├── ingestion/pipeline.py         dlt salesforce source
├── transform/
│   ├── dbt_project.yml
│   ├── sources.yml
│   └── models/
│       ├── staging/stg_accounts.sql
│       ├── staging/stg_opportunities.sql
│       ├── staging/stg_contacts.sql
│       └── core/fct_opportunities.sql
├── contracts/
│   ├── accounts.yaml
│   └── opportunities.yaml
├── quality/checks.yaml
├── alerts/config.yaml
└── docs/
    ├── README.md
    └── runbook.md
```

**Why second:** Salesforce → Snowflake is the highest-demand ICP-002 and ICP-004 combination. It is the pipeline that analytics consultancies build most often. It proves PipelineKit works beyond Postgres.

---

## Sprint 6-3: Blueprint #003 — Stripe → Snowflake

**Type:** Blueprint  
**Effort:** Medium (1 sprint, ~3 hours)  
**SPEC:** Write SPEC-014-Blueprint-003 before this sprint fires  
**ADR:** None required

**What it builds:**
```
blueprints/stripe-to-snowflake/
├── blueprint.json
├── ingestion/pipeline.py         dlt stripe source
├── transform/
│   └── models/
│       ├── staging/stg_charges.sql
│       ├── staging/stg_customers.sql
│       └── core/fct_revenue.sql
├── contracts/
│   └── charges.yaml
├── quality/checks.yaml
└── docs/README.md + runbook.md
```

**Why third:** Stripe → Snowflake is the ICP-001 (Solo Founder) primary use case. Every SaaS company needs revenue analytics. Short runbook, fast deployment.

---

## Sprint 6-4: AI Blueprint Generation (SPEC-015)

**Type:** AI capability extension  
**Effort:** Large (1-2 sprints)  
**SPEC:** Write SPEC-015-Blueprint-Generation before this sprint fires  
**ADR:** ADR-017-Blueprint-Generation-Governance (write before SPEC-015)

**What it builds:**
```
src/pipelinekit/ai/blueprint_generator.py
src/pipelinekit/cli/generate.py
schemas/blueprint_draft.schema.json
tests/ai/test_blueprint_generator.py
```

**New CLI command:**
```
pipelinekit generate blueprint \
  --source salesforce \
  --destination bigquery \
  --tables accounts,opportunities,contacts
```

**AI boundary for blueprint generation (ADR-017):**
- AI generates draft artifacts: dlt pipeline, dbt models (staging + core), contract definitions, Soda checks
- Every generated artifact is written to a `drafts/` directory — never directly to `blueprints/`
- Human reviews each artifact and approves with `pipelinekit generate apply`
- Approved artifacts move from `drafts/` to `blueprints/<name>/`
- `can_auto_generate = True` — first time AI moves from advisor to co-author, under human review
- Generated blueprint.json validated against `schemas/blueprint.schema.json` before apply

**Why fourth:** After 3 hand-crafted blueprints the pattern is proven. AI generation compounds the catalog. Every approved generated blueprint becomes a new hand-crafted asset — the AI learns the pattern, the human validates the output.

---

## Sprint 6-5: Remote Blueprint Registry

**Type:** Distribution infrastructure  
**Effort:** Large  
**SPEC:** Write SPEC-016-Remote-Registry before this sprint fires  
**ADR:** ADR-018-Registry-Governance

**What it builds:**
```
src/pipelinekit/blueprints/remote.py    RemoteRegistry client
src/pipelinekit/cli/blueprint.py        Add install, search, publish commands
```

**New CLI commands:**
```
pipelinekit blueprint search <query>
pipelinekit blueprint install <name>
pipelinekit blueprint publish          (for approved contributors)
```

**Why fifth:** The registry is the distribution channel. Once 3+ blueprints exist, the catalog needs a discovery mechanism. This is where PipelineKit becomes a platform — not just a tool.

---

## Sprint 6-6: Migration Intelligence

**Type:** AI capability extension  
**Effort:** Medium  
**SPEC:** Write SPEC-017-Migration-Intelligence before this sprint fires  
**ADR:** None beyond existing ADR-007

**What it builds:**
```
src/pipelinekit/cli/migrate.py         pipelinekit migrate command (was a stub)
src/pipelinekit/ai/migration.py        MigrationAnalyzer
```

**New CLI command:**
```
pipelinekit migrate analyze \
  --from airbyte \
  --config ./airbyte-connection.json
```

**What it does:**
- Reads an existing pipeline definition (Airbyte connection, Fivetran config, custom Python)
- Produces a migration plan: what maps cleanly, what needs manual work, what PipelineKit replaces
- Generates a draft pipelinekit.yaml pre-populated from the existing config
- Human reviews and approves before any changes are made

**Why sixth:** ICP-004 (Mixed-Stack Enterprise) is the largest revenue opportunity and their primary blocker is migration cost. Migration Intelligence reduces that cost — it is the sales tool that closes ICP-004 deals.

---

## Phase 6 Pre-Flight Checklist

Before each Phase 6 sprint fires, verify all 16 smells:

| Sprint | Key smells to check |
|---|---|
| 6-1 health | Smell 10 (customer capability: ops teams get maintenance visibility) |
| 6-2/6-3 blueprints | Smell 15 (blueprint shortcut: all 8 assets required) |
| 6-4 AI generation | Smell 13 (observer becomes actor: human approval before apply) |
| 6-5 registry | Smell 11 (capability creep: registry serves blueprints, not general packages) |
| 6-6 migration | Smell 16 (control plane inversion: PipelineKit reads other tools, never becomes them) |

---

## Phase 6 SPEC Writing Order

Write these SPECs before their sprint fires — same discipline as Phases 1-5:

```
SPEC-013  Blueprint #002 (Salesforce → Snowflake)    Before Sprint 6-2
SPEC-014  Blueprint #003 (Stripe → Snowflake)         Before Sprint 6-3
SPEC-015  AI Blueprint Generation                     Before Sprint 6-4
SPEC-016  Remote Blueprint Registry                   Before Sprint 6-5
SPEC-017  Migration Intelligence                      Before Sprint 6-6
```

SPEC-012 (health commands) is already written. Sprint 6-1 can fire immediately.

---

## Phase 6 ADR Writing Order

```
ADR-017  Blueprint Generation Governance   Before SPEC-015
ADR-018  Registry Governance               Before SPEC-016
```

---

## Phase 6 Definition of Done

Phase 6 is complete when:

```
✓ pipelinekit health runs all 5 checks green
✓ Blueprint #002 (Salesforce → Snowflake) deployable in < 60 minutes
✓ Blueprint #003 (Stripe → Snowflake) deployable in < 60 minutes
✓ pipelinekit generate blueprint produces valid draft
✓ pipelinekit blueprint install <name> works against remote registry
✓ pipelinekit migrate analyze produces migration plan
✓ All tests green, coverage >= 80%
✓ Blueprint #001 verified deployment record exists in runbook
✓ CI green on every push
```

---

## What Changes After Phase 6

After Phase 6, PipelineKit has:
- 3 production blueprints (hand-crafted + verified)
- AI-generated blueprint capability
- A remote registry for distribution
- Migration tooling for ICP-004
- A programmed sustainability policy
- 5 AI providers across 3 continents

That is the product ready for Series A positioning and enterprise sales.

The governing principle remains unchanged:

> **PipelineKit is the AI-native operating system for trusted analytics pipelines.**

Phase 6 makes it undeniably true.
