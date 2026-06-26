# Runbook — Blueprint #002 (Salesforce → Snowflake)

Operational guide for running, monitoring, and troubleshooting this pipeline.
This runbook is intentionally honest: it documents what can fail and exactly how
to recover.

---

## 1. Overview

```
Salesforce ──dlt──▶ Snowflake (raw) ──dbt staging──▶ stg_accounts
                                     ──dbt staging──▶ stg_opportunities
                                     ──dbt staging──▶ stg_contacts
                                     ──dbt core─────▶ fct_opportunities
                                                          │
                                          contracts (opportunities.yaml)
                                                          │
                                          quality checks (Soda)
                                                          │
                                          alerts (Resend, on failure)
```

Every stage is recorded in `.pipelinekit/state.db`. Failures never go silent:
they are written to state **and** dispatched as alerts.

---

## 2. Prerequisites

Credentials are supplied via the environment (BYOK, ADR-005).

```bash
# Salesforce source
export SALESFORCE_USERNAME="you@example.com"
export SALESFORCE_PASSWORD="your-password"
export SALESFORCE_SECURITY_TOKEN="your-security-token"

# Snowflake destination
export SNOWFLAKE_ACCOUNT="your-account"
export SNOWFLAKE_USER="your-user"
export SNOWFLAKE_PASSWORD="your-password"
export SNOWFLAKE_DATABASE="ANALYTICS"
export SNOWFLAKE_WAREHOUSE="TRANSFORMING"
export SNOWFLAKE_ROLE="TRANSFORMER"

# Alerts
export RESEND_API_KEY="re_xxxxxxxx"
```

Real ingestion requires the dlt Salesforce extra: `poetry add 'dlt[salesforce]'`.

---

## 3. Installation

1. Copy `blueprints/salesforce-to-snowflake/pipelinekit.example.yaml` to your
   project root as `pipelinekit.yaml`.
2. Confirm every `${VAR}` reference resolves (the env vars above are set).
3. Validate: `pipelinekit validate` and `pipelinekit blueprint validate`.

---

## 4. First run walkthrough

```bash
pipelinekit run --dry-run   # config + connectivity only, no data moved
pipelinekit run             # ingestion → transformation → quality
pipelinekit status          # run history
```

A successful run lands `accounts`, `opportunities`, `contacts` in the raw
schema, builds `stg_*` and `fct_opportunities`, validates the `opportunities`
contract, and runs the Soda checks.

---

## 5. Troubleshooting

### `[PK-ADAPTER-001]` — Source unreachable
**Cause:** PipelineKit cannot reach Salesforce.
**Check:** `SALESFORCE_USERNAME`/`PASSWORD`/`SECURITY_TOKEN`; API access enabled
on the org; network reachability.
**Recover:** Fix credentials, re-run `pipelinekit run --dry-run`.

### `[PK-ADAPTER-002]` — Ingestion or transformation failed
**Cause:** dlt load error (e.g. missing `dlt[salesforce]` extra) or a non-zero
`dbt build`.
**Check:** `poetry add 'dlt[salesforce]'` is installed; Snowflake
credentials/role/warehouse; dbt logs in `transform/target/`.
**Recover:** Resolve the failing model or load, then re-run.

### `[PK-CONTRACT-002]` — Freshness violation
**Cause:** Newest `last_modified_date` is older than 4 hours.
**Check:** Is the source sync running often enough? Is upstream CRM data stale?
**Recover:** Increase run frequency or investigate the source org.

### `[PK-CONTRACT-001 / 003 / 004]` — Structural violations
**Cause:** Missing required column, duplicate `id`, or unexpected nulls in
`id`/`amount`/`stage_name`/`close_date`.
**Check:** Salesforce field changes; the `stg_opportunities` casting logic.
**Recover:** Reconcile the source schema with `contracts/opportunities.yaml`.

### `[PK-NOTIFY-004]` — Alerts not delivered
**Cause:** `RESEND_API_KEY` missing or invalid.
**Note:** Notification failure never blocks the pipeline — runs still complete
and are recorded; only the alert is missed.

---

## 6. Verified Deployments

This table records real end-to-end deployments of Blueprint #002.
Each row represents a verified run by a named tester on a real environment.

| Date | Tester | Salesforce Org | Destination | Rows Ingested | Deploy Time | Data Latency | Contracts | Status |
|---|---|---|---|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Unverified |

### How to add a row

After running `scripts/verify-blueprint-002.ps1` successfully:
1. Fill in the row above with your actual results.
2. Commit: `git commit -m "Blueprint #002 verified — [date] by [name]"`.
3. This record is permanent institutional memory.

---

## 7. Claim validation

| Claim in blueprint.json | Status | Evidence |
|---|---|---|
| `deploy_time_minutes: 60` | Unverified until first row above | — |
| `time_to_trusted_data_hours: 4` | Unverified until first row above | — |

| 2026-06-26 | Eddy Mkwambe | Synthetic DuckDB | DuckDB (local) | 100 accts / 500 opps / 200 contacts | 0.2 min | 0.82s dbt | 9/9 dbt tests passed | SUCCESS — LOCAL |
