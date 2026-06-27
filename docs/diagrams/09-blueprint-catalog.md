# Blueprint Catalog and Registry

The blueprint ecosystem — local, AI-proposed, and registry. Verified against `PROJECT-STATUS.md`, `blueprints/`, `src/pipelinekit/blueprints/remote.py`, and `registry/v1/catalog.json`.

## Catalog

| Blueprint | Source → Destination | Origin | Verification | Registry `verified` |
|---|---|---|---|---|
| `postgres-to-snowflake` v1.0.0 | postgres → snowflake | Hand-crafted | Locally verified — 1,000 rows | `true` |
| `salesforce-to-snowflake` v1.0.0 | salesforce → snowflake | Hand-crafted | Locally verified — 800 rows | `true` |
| `stripe-to-snowflake` v1.0.0 | stripe → snowflake | AI-proposed, human-approved | Local verification pending | `false` |

The registry (`registry.pipelinekit.dev`) serves `v1/catalog.json` once deployed to Cloudflare Pages. Until then, `pipelinekit blueprint search` / `install` return `PK-REGISTRY-001`; the three blueprints already exist in the repo under `blueprints/`.

## The 8 Required Assets

Each blueprint must provide these eight assets. The registry verifies all eight are present before writing a blueprint to disk (layout is lenient — each row passes if any candidate path exists).

| # | Asset | Path (candidates) | Purpose |
|---|---|---|---|
| 1 | Manifest | `blueprint.json` | Identity, source/destination, contracts, KPIs, targets |
| 2 | Ingestion | `ingestion/` | dlt ingestion pipeline |
| 3 | Transform | `transform/` or `dbt/` | dbt project (staging → core) |
| 4 | Contracts | `contracts/` | Data contract definitions |
| 5 | Quality | `quality/` or `dbt/tests` | Soda quality checks |
| 6 | Alerts | `alerts/` | Notification / alert configuration |
| 7 | Readme | `docs/README.md` or `README.md` | What the blueprint does |
| 8 | Runbook | `docs/runbook.md` / `RUNBOOK.md` | Verification recipe and operations |

## Verification Lifecycle

| Stage | Meaning |
|---|---|
| `proposed` | AI proposed the asset (or hand-authored draft) |
| `approved` | A human approved it |
| `written` | `apply()` wrote it to `blueprints/<name>/` |
| `validated` | Passed `blueprint validate` (schema + assets) |
| `locally verified` | Ran end-to-end against a local source + DuckDB, recorded in the runbook |
| `production verified` | Ran against the real warehouse — the bar for registry `verified: true` |
