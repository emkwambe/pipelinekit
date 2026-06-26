# stripe-to-snowflake Pipeline Blueprint

Version: 1.0.0  
Status: **Proposed — requires human review before apply**

## Overview

This blueprint delivers a trusted analytics pipeline for Stripe payments data into Snowflake.
It ingests `charges` and `customers` from the Stripe API using dlt, transforms them with dbt,
and enforces data quality contracts.

## Architecture


Stripe API
    │
    ▼
[dlt ingestion] ──► Snowflake RAW (stripe_raw schema)
    │
    ▼
[dbt staging]   ──► stg_stripe__charges, stg_stripe__customers
    │
    ▼
[dbt core]      ──► fct_charges, dim_customers
    │
    ▼
[BI / Analytics]


## KPIs Enabled

| KPI | Source Model |
|---|---|
| Daily Revenue | `fct_charges` |
| Charge Volume | `fct_charges` |
| Refund Rate | `fct_charges` |
| Average Charge Value | `fct_charges` |
| New Customers | `dim_customers` |
| Customer Lifetime Value | `dim_customers` |

## Prerequisites

- Stripe account with a secret API key (`sk_live_...` or `sk_test_...`)
- Snowflake account with a dedicated role, warehouse, database, and schema
- Python 3.9+ with `dlt` installed
- dbt-core + dbt-snowflake adapter installed

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `STRIPE_API_KEY` | Stripe secret API key | Yes |
| `SNOWFLAKE_ACCOUNT` | Snowflake account identifier | Yes |
| `SNOWFLAKE_USERNAME` | Snowflake username | Yes |
| `SNOWFLAKE_PASSWORD` | Snowflake password | Yes |
| `SNOWFLAKE_ROLE` | Snowflake role | Yes |
| `SNOWFLAKE_WAREHOUSE` | Snowflake warehouse | Yes |
| `SNOWFLAKE_DATABASE` | Snowflake destination database | Yes |
| `SNOWFLAKE_SCHEMA` | Snowflake destination schema | Yes |
| `DBT_SOURCE_DATABASE` | Database for dbt source resolution | Yes |
| `DBT_SOURCE_SCHEMA` | Schema for dbt source resolution | Yes |
| `CRON_SCHEDULE` | Pipeline schedule (cron format) | Yes |
| `SLACK_WEBHOOK_URL` | Slack webhook for alerts | Recommended |
| `PAGERDUTY_INTEGRATION_KEY` | PagerDuty key for critical alerts | Recommended |
| `PIPELINE_DATASET_NAME` | dlt dataset name (default: stripe_raw) | No |

## Deployment Steps

1. **Review this blueprint** — a human must approve before any files are written.
2. **Verify dlt Stripe source** — confirm the correct package name and import path for the dlt Stripe verified source. Update `ingestion/pipeline.py` accordingly.
3. **Provision Snowflake resources** — create the role, warehouse, database, and schema. Grant appropriate permissions.
4. **Set environment variables** — export all required variables in your deployment environment.
5. **Install dependencies:**
bash
   pip install dlt dbt-core dbt-snowflake
   # Install the correct dlt Stripe source package (verify name):
   pip install dlt[stripe]  # or: pip install dlt-stripe-analytics

6. **Run ingestion pipeline:**
bash
   python ingestion/pipeline.py

7. **Run dbt transformations:**
bash
   cd dbt
   dbt deps
   dbt run
   dbt test

8. **Schedule the pipeline** — configure your orchestrator (Airflow, Prefect, etc.) using `CRON_SCHEDULE`.

## Data Contracts

| Table | Contract File | Freshness SLA |
|---|---|---|
| charges | `contracts/charges.yaml` | 6 hours |
| customers | `contracts/customers.yaml` | 6 hours |

## Known Assumptions & Limitations

- **Amount conversion**: Raw Stripe amounts are in smallest currency units (cents). Staging models divide by 100 for USD. Multi-currency normalization is NOT implemented.
- **Nested fields**: Stripe `payment_method_details` and `metadata` are complex/nested objects. dlt may auto-flatten them; exact column names must be verified after first load.
- **dlt source name**: The exact dlt Stripe verified source package name was assumed. Verify at https://dlthub.com/docs/dlt-ecosystem/verified-sources/stripe before deploying.
- **Polling mode**: This pipeline uses polling/batch ingestion. Webhook-based real-time ingestion is not implemented.
- **Tables not included**: `subscriptions`, `invoices`, `refunds`, `events` are supported by the adapter but not included in this blueprint per the provided specification.
