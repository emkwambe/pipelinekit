# Blueprint Guide

A complete reference for the PipelineKit blueprint system: what a blueprint is, how to use the ones that ship, how AI proposes new ones, and how to author and verify your own.

---

## What is a Blueprint?

A **blueprint** is a complete, self-contained, verifiable pipeline package. It bundles everything needed to ingest a source, transform it, enforce a contract, run quality checks, alert on failure, and operate it — as human-readable files under `blueprints/<name>/`.

A blueprint is not a template you edit blindly: it is a reference implementation that has (or will be) verified end-to-end, with a recorded runbook. Blueprints are how PipelineKit standardizes "from requirements to deployable pipeline."

---

## The 8 Required Assets

Every blueprint must provide these eight assets. The registry verifies each one is present before a blueprint is written to disk (layout is lenient — a hand-crafted `transform/` and an AI-proposed `dbt/` both satisfy the transform asset).

| # | Asset | Path (candidates) | Purpose |
|---|---|---|---|
| 1 | Manifest | `blueprint.json` | Identity, source/destination types, contracts, KPIs, deploy/TTTD targets |
| 2 | Ingestion | `ingestion/` | The dlt ingestion pipeline (extract → load) |
| 3 | Transform | `transform/` or `dbt/` | The dbt project (staging → core models) |
| 4 | Contracts | `contracts/` | Data contract definitions (one YAML per table) |
| 5 | Quality | `quality/` or `dbt/tests` | Soda quality checks |
| 6 | Alerts | `alerts/` | Notification/alert configuration |
| 7 | Readme | `docs/README.md` or `README.md` | What the blueprint does and how to use it |
| 8 | Runbook | `docs/runbook.md` / `RUNBOOK.md` | Verification recipe and operational steps |

---

## Using Existing Blueprints

```bash
# List blueprints installed locally (under ./blueprints/)
pipelinekit blueprint list

# Show details for one blueprint
pipelinekit blueprint info postgres-to-snowflake

# Validate a blueprint's structure against the schema
pipelinekit blueprint validate                 # all installed blueprints
pipelinekit blueprint validate postgres-to-snowflake

# Install a blueprint from the remote registry (validated before write)
pipelinekit blueprint install postgres-to-snowflake
pipelinekit blueprint install postgres-to-snowflake --version 1.0.0
pipelinekit blueprint install postgres-to-snowflake --force   # overwrite
```

`blueprint info` shows the source, destination, contract count, KPIs, deploy-time target, and Time-to-Trusted-Data target. `blueprint validate` checks `blueprint.json` against `schemas/blueprint.schema.json` and reports detected contracts, dbt project, and quality checks.

> **Registry status:** the public registry (`registry.pipelinekit.dev`) is not yet deployed. Until it is, `blueprint search` and `blueprint install` return `PK-REGISTRY-001` (registry unreachable). The three catalog blueprints are already present in the repo under `blueprints/`.

---

## The Blueprint Catalog

| Blueprint | Source → Destination | Origin | Verification |
|---|---|---|---|
| `postgres-to-snowflake` | Postgres → Snowflake | Hand-crafted | Locally verified — 1,000 rows |
| `salesforce-to-snowflake` | Salesforce → Snowflake | Hand-crafted | Locally verified — 800 rows |
| `stripe-to-snowflake` | Stripe → Snowflake | AI-proposed, human-approved | Local verification pending |

`postgres-to-snowflake` and `salesforce-to-snowflake` were authored by hand and verified end-to-end against a local warehouse. `stripe-to-snowflake` was produced by the AI Blueprint Proposal system, reviewed and approved by a human, and uses the AI-proposed layout (`dbt/` rather than `transform/`, a root-level runbook).

---

## AI Blueprint Proposal

PipelineKit can propose a complete blueprint from a short specification. **AI proposes; a human approves; `apply()` writes.** Nothing is written without review, and `can_auto_apply` is always `false`.

```bash
# Plan only (the safe default): print a plan ID, write no files
pipelinekit generate blueprint \
  --source stripe --destination snowflake --tables charges,customers --plan

# Review each proposed asset and apply the approved ones in one session
pipelinekit generate blueprint \
  --source stripe --destination snowflake --tables charges,customers --interactive

# Re-display a stored proposal
pipelinekit generate show <plan-id>

# Write the approved assets from a stored proposal
pipelinekit apply plan <plan-id> --interactive
```

Before any AI call, the source and destination are checked against the adapter capability registry; an unsupported connector fails fast with `PK-GEN-006`. Supported sources today are `postgres`, `salesforce`, and `stripe`; supported destinations are `snowflake`, `bigquery`, and `duckdb`.

### The review process

`--interactive` walks each proposed asset and prompts:

```
[a]ccept  [r]eject  [e]dit  [x]explain  [y-all]accept remaining  [q]uit
```

- **accept / reject** — approve or discard the asset.
- **edit** — open the content in your editor; the edited version is re-proposed and approved.
- **explain** — show the asset's provenance (what evidence it was based on, assumptions, decisions you must make).
- **accept remaining** — approve every remaining asset.

If the source is not PipelineKit-verified (e.g. `stripe`, `salesforce`), each asset shows `⚠ Unverified adapter source — verify import path before deploying`.

### Trust model: proposed → approved → written → validated

Each asset moves through an explicit, code-enforced state machine:

```
proposed → approved → written → validated
proposed → rejected
proposed → edited → proposed   (re-proposed after an edit)
```

`apply()` writes **only** assets a human has APPROVED, strips provenance from the file content, and refuses to write if nothing is approved (`PK-GEN-003`) or the target directory already exists (`PK-GEN-004`). An invalid state transition raises `PK-GEN-007`.

---

## Creating a Blueprint Manually

### Directory structure

```
blueprints/<name>/
├── blueprint.json
├── pipelinekit.example.yaml
├── ingestion/
│   └── pipeline.py
├── transform/                # dbt project
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/
│       ├── sources.yml
│       ├── staging/
│       └── core/
├── contracts/
│   └── <table>.yaml
├── quality/
│   └── checks.yaml
├── alerts/
│   └── config.yaml
└── docs/
    ├── README.md
    └── runbook.md
```

### `blueprint.json` schema

```json
{
  "name": "postgres-to-snowflake",
  "version": "1.0.0",
  "description": "Postgres to Snowflake trusted analytics pipeline",
  "source": { "type": "postgres", "dlt_source": "sql_database" },
  "destination": { "type": "snowflake", "dlt_destination": "snowflake" },
  "contracts": ["contracts/orders.yaml"],
  "tags": ["postgres", "snowflake", "product-analytics"],
  "kpis": ["Daily Orders", "Revenue", "Customers", "Order Value", "Retention"],
  "deploy_time_minutes": 60,
  "time_to_trusted_data_hours": 24
}
```

Validated against `schemas/blueprint.schema.json`. `name`, `version`, `source`, and `destination` are required.

### dbt project conventions

- `models/sources.yml` declares the raw source, using `{{ env_var('DBT_SOURCE_DATABASE') }}` / `{{ env_var('DBT_SOURCE_SCHEMA') }}`.
- Staging models reference the source: `{{ source('source_name', 'table') }}`.
- Core models reference staging models: `{{ ref('staging_model') }}`.
- `profiles.yml` is environment-driven so the same project targets a local DuckDB or a production Snowflake without edits.

### Contract format (`contracts/*.yaml`)

```yaml
version: 1
table: orders
description: "Order transaction records"

freshness:
  max_age_hours: 12
  column: updated_at

required_columns:
  - order_id
  - customer_id
  - amount
  - status

uniqueness:
  - order_id

not_null:
  - order_id
  - customer_id
  - amount

row_count:
  min: 1
```

### Soda checks format (`quality/checks.yaml`)

```yaml
checks for orders:
  - freshness(updated_at) < 12h
  - row_count > 0
  - missing_count(order_id) = 0
  - missing_count(customer_id) = 0
  - duplicate_count(order_id) = 0
  - invalid_count(status) = 0:
      valid values: [pending, confirmed, shipped, delivered, cancelled]
```

### Verification script

Each blueprint's `docs/runbook.md` records how it was verified — the prerequisites, the exact commands, and the observed result (rows loaded, duration). Keep it accurate: a blueprint is only "verified" once a real run is recorded there.

---

## Blueprint Verification

A blueprint moves through verification stages:

1. **Local verification** — run end-to-end against a local source and a local DuckDB destination (Docker Postgres for Blueprint #001). This proves ingestion, transform, contracts, and quality all execute against real rows. Both hand-crafted blueprints are locally verified.
2. **Production verification** — run against the real warehouse (Snowflake/BigQuery). This is the bar for marking a blueprint `verified: true` in the registry.
3. **Recording in the runbook** — write the observed result (rows, duration, date) into `docs/runbook.md`. Verification that is not recorded does not count.

`pipelinekit health blueprints` re-validates every installed blueprint's structure; run it after installing or editing a blueprint.
