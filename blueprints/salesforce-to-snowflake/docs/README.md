# Blueprint #002 — Salesforce → Snowflake

A complete, trusted analytics pipeline: replicate Salesforce CRM objects
(accounts, opportunities, contacts) into Snowflake, transform them with dbt,
enforce data contracts, run quality checks, and alert on failures.

**Deploy time:** < 60 minutes · **Time-to-Trusted-Data:** < 4 hours

---

## What this blueprint delivers

| Stage | Tool | Asset |
|---|---|---|
| Ingestion | dlt (`salesforce` source) | `ingestion/pipeline.py` |
| Transformation | dbt Core | `transform/` |
| Contracts | PipelineKit | `contracts/opportunities.yaml` |
| Quality | Soda | `quality/checks.yaml` |
| Alerts | Resend | `alerts/config.yaml` |

KPIs surfaced: **Pipeline Value, Win Rate, Avg Deal Size, Opportunities by
Stage, Revenue by Industry.**

---

## Prerequisites

- A Salesforce org with API access (username, password, security token).
- A Snowflake account (database, warehouse, and a role that can create schemas).
- Python 3.11+ and PipelineKit installed (`pipelinekit --version`).
- dbt Core with the Snowflake adapter (`dbt --version`).
- The dlt Salesforce extra for real runs: `poetry add 'dlt[salesforce]'`.
- A Resend account and API key (for alerts).

---

## Required environment variables

Credentials are supplied via the environment (BYOK, ADR-005) — never committed.

```bash
# Salesforce source
export SALESFORCE_USERNAME="you@example.com"
export SALESFORCE_PASSWORD="your-password"
export SALESFORCE_SECURITY_TOKEN="your-security-token"

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
   cp -r blueprints/salesforce-to-snowflake ./my-pipeline
   cd ./my-pipeline
   ```

2. **Point your `pipelinekit.yaml`** at these assets (see
   `pipelinekit.example.yaml`):
   - `ingestion.source` → your Salesforce credentials
   - `ingestion.destination` → Snowflake
   - `transformation.project_dir` → the blueprint `transform/`
   - `contracts.directory` → the blueprint `contracts/`
   - `quality.checks_dir` → the blueprint `quality/`
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
# Dry run: check config without moving data
pipelinekit run --dry-run

# Full run: ingestion → transformation → quality
pipelinekit run

# Inspect history
pipelinekit status
```

A successful first run lands raw `accounts`, `opportunities`, and `contacts`
in Snowflake, builds the staging models and `fct_opportunities`, validates the
`opportunities` contract, and runs the Soda checks. If any step fails, an alert
is dispatched to the configured recipients.

See [`runbook.md`](./runbook.md) for troubleshooting and verified deployments.
