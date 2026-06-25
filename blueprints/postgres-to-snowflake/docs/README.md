# Blueprint #001 — Postgres → Snowflake

A complete, trusted analytics pipeline: replicate operational orders data from
PostgreSQL into Snowflake, transform it with dbt, enforce data contracts, run
quality checks, and alert on failures.

**Deploy time:** < 60 minutes · **Time-to-Trusted-Data:** < 24 hours

---

## What this blueprint delivers

| Stage | Tool | Asset |
|---|---|---|
| Ingestion | dlt | `ingestion/pipeline.py` |
| Transformation | dbt Core | `transform/` |
| Contracts | PipelineKit | `contracts/orders.yaml` |
| Quality | Soda | `quality/checks.yaml` |
| Alerts | Resend | `alerts/config.yaml` |

KPIs surfaced: **Daily Orders, Revenue, Customers, Order Value, Retention.**

---

## Prerequisites

- A PostgreSQL database with an `orders` table (read access).
- A Snowflake account (database, warehouse, and a role that can create schemas).
- Python 3.11+ and PipelineKit installed (`pipelinekit --version`).
- dbt Core with the Snowflake adapter (`dbt --version`).
- A Resend account and API key (for alerts).

---

## Required environment variables

Credentials are supplied via the environment (BYOK) — never committed.

```bash
# Source
export POSTGRES_CONN_STR="postgresql://user:pass@host:5432/dbname"

# Snowflake destination (used by dlt and dbt)
export SNOWFLAKE_ACCOUNT="your-account"
export SNOWFLAKE_USER="your-user"
export SNOWFLAKE_PASSWORD="your-password"
export SNOWFLAKE_DATABASE="ANALYTICS"
export SNOWFLAKE_WAREHOUSE="TRANSFORMING"
export SNOWFLAKE_ROLE="TRANSFORMER"

# Alerts
export RESEND_API_KEY="re_xxxxxxxx"
```

---

## Installation

1. **Copy the blueprint** into your project (it is yours to version-control):
   ```bash
   cp -r blueprints/postgres-to-snowflake ./my-pipeline
   cd ./my-pipeline
   ```

2. **Point your `pipelinekit.yaml`** at these assets:
   - `ingestion.source` → your Postgres connection
   - `ingestion.destination` → Snowflake
   - `transformation.project_dir` → `./transform`
   - `contracts.directory` → `./contracts`
   - `quality.checks_dir` → `./quality`
   - `notifications` → copy from `alerts/config.yaml`

3. **Validate before running:**
   ```bash
   pipelinekit validate
   pipelinekit validate --contracts
   pipelinekit blueprint validate
   ```

---

## First run

```bash
# Dry run: check connectivity and config without moving data
pipelinekit run --dry-run

# Full run: ingestion → transformation → quality
pipelinekit run

# Inspect history
pipelinekit status
```

A successful first run lands raw orders in Snowflake, builds `stg_orders` and
`fct_orders`, validates the `orders` contract, and runs the Soda checks. If any
step fails, an alert is dispatched to the configured recipients.

See [`runbook.md`](./runbook.md) for troubleshooting and KPI definitions.
