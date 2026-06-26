# Getting Started with PipelineKit

This guide takes you from an empty directory to a running, verified pipeline using **Blueprint #001 (`postgres-to-snowflake`)**, executed locally against a throwaway Postgres source and a local DuckDB destination.

Time required: about 20 minutes.

---

## Prerequisites

| Tool | Version | Why |
|---|---|---|
| Python | 3.11+ | PipelineKit runtime (`requires-python = ^3.11`) |
| Poetry | 2.x recommended | Dependency management and the `pipelinekit` entry point |
| Docker Desktop | current | Runs a local Postgres source for end-to-end verification |

> The repository is developed and tested on Python 3.13. Any 3.11+ interpreter satisfies the package constraint.

---

## Installation

```bash
git clone https://github.com/emkwambe/pipelinekit.git
cd pipelinekit
poetry install
poetry run pipelinekit --version
```

`poetry run pipelinekit` is the entry point. On Windows use PowerShell; commands are identical.

---

## Your First Pipeline (Blueprint #001)

Blueprint #001 ingests a Postgres `orders` table, transforms it with dbt, and enforces a data contract and Soda quality checks. The shipped example config lives at `blueprints/postgres-to-snowflake/pipelinekit.example.yaml`.

### Step 1 — Initialize a project

In a working directory of your choice:

```bash
poetry run pipelinekit init
```

This writes a default `pipelinekit.yaml` and adds `.pipelinekit/` (the local state directory) to `.gitignore`. If a config already exists, `init` refuses to overwrite it.

### Step 2 — Configure `pipelinekit.yaml`

Replace the generated config with the Blueprint #001 shape. Credentials are read from environment variables via `${VAR}` interpolation — never hardcode them.

```yaml
pipeline:
  name: postgres-to-snowflake-blueprint-001
  version: "1.0.0"
  description: "Blueprint #001 — Postgres to Snowflake trusted analytics"

runtime:
  environment: local

ingestion:
  source:
    type: postgres
    host: "${PG_HOST}"
    port: 5432
    database: "${PG_DATABASE}"
    user: "${PG_USER}"
    password: "${PG_PASSWORD}"
    tables:
      - orders
  destination:
    type: snowflake
    account: "${SNOWFLAKE_ACCOUNT}"
    database: "${SNOWFLAKE_DATABASE}"
    user: "${SNOWFLAKE_USER}"
    password: "${SNOWFLAKE_PASSWORD}"
    warehouse: "${SNOWFLAKE_WAREHOUSE}"
    schema: "raw"

transformation:
  enabled: true
  project_dir: ./transform

contracts:
  enabled: true
  directory: ./contracts

quality:
  enabled: true
  checks_dir: ./quality

diagnostics:
  enabled: true
  provider: anthropic

notifications:
  enabled: false
  channels: []
```

Set the referenced environment variables before running. For a fully local run, point the source at a Docker Postgres and use a DuckDB destination (see the blueprint's `docs/runbook.md` for the exact local-verification recipe and environment variables).

### Step 3 — Validate

```bash
poetry run pipelinekit validate
poetry run pipelinekit validate --contracts
```

`validate` confirms `pipelinekit.yaml` is well-formed. `--contracts` additionally loads and structurally checks the data contracts under `contracts/` — it confirms the definitions are present and valid. Data-level contract checks run later, during `run`, because they need a live warehouse connection.

### Step 4 — Run locally

```bash
poetry run pipelinekit run --dry-run   # validate adapters, move no data
poetry run pipelinekit run             # execute ingestion → transform → quality
```

`--dry-run` checks that each configured adapter is reachable and reports a per-step table. A full `run` executes the pipeline and records the run in local state.

### Step 5 — Verify results

```bash
poetry run pipelinekit status
```

`status` lists the most recent runs with their status and duration. Blueprint #001 has been locally verified at 1,000 rows in roughly 0.7 minutes; your local run against the same fixture should match.

---

## Understanding the Output

**What each step means**

- **ingestion** — dlt extracts rows from the source and lands them in the destination's raw schema.
- **transformation** — dbt builds staging and core models (`stg_orders` → `fct_orders`).
- **quality** — Soda runs the checks in `quality/checks.yaml` against the destination.

A run is reported step by step with status, duration, and rows processed. A failed step carries a structured `PK-*` error code; see the [Operations Runbook](OPERATIONS-RUNBOOK.md).

**What "trusted" means in PipelineKit**

Trust is not a feeling — it is enforced. A pipeline is *trusted* when its data contract holds (required columns present, uniqueness and not-null satisfied, freshness within SLA, row counts in range) and its quality checks pass. PipelineKit makes those checks part of the run, so "the pipeline succeeded" and "the data is correct" are the same statement.

---

## Next Steps

- **Browse the blueprint catalog** — `pipelinekit blueprint list`, then `pipelinekit blueprint info postgres-to-snowflake`. See the [Blueprint Guide](BLUEPRINT-GUIDE.md).
- **Try AI Blueprint Proposal** — `pipelinekit generate blueprint --source postgres --destination snowflake --tables orders --plan`. See [AI Features](AI-FEATURES.md).
- **Migrate an existing pipeline** — `pipelinekit migrate analyze <airbyte-or-fivetran-or-python-config>`. See the [Migration Guide](MIGRATION-GUIDE.md).
