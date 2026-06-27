# Configuration Reference

Every field in `pipelinekit.yaml`, validated against the Pydantic models in `src/pipelinekit/config/schema.py`. All eight top-level sections are required; a missing section is a `PK-CONFIG-001` validation failure.

---

## `pipelinekit.yaml` — Complete Schema

### `pipeline`
Pipeline identity.

| Field | Type | Required | Default |
|---|---|---|---|
| `name` | string | yes | — |
| `version` | string | no | `0.1.0` |
| `description` | string | no | `""` |

### `runtime`
Execution environment.

| Field | Type | Required | Default |
|---|---|---|---|
| `environment` | string | no | `local` |

### `ingestion`
Source and destination connection descriptors. Both `source` and `destination` use the same connection model — only `type` is required, and the remaining fields depend on the connector. The single model carries fields for every supported backend; set only the ones your connector needs.

```yaml
ingestion:
  source:
    type: postgres        # postgres | salesforce | stripe
    # ... source fields
  destination:
    type: snowflake       # snowflake | bigquery | duckdb
    # ... destination fields
```

**Source fields by type**

| Source `type` | Fields |
|---|---|
| `postgres` | `host`, `port`, `database`, `user`, `password`, `tables` |
| `salesforce` | `username`, `password`, `security_token`, `tables` |
| `stripe` | `api_key`, `tables` |

`tables` is a list of table/object names to ingest.

**Destination fields by type**

| Destination `type` | Fields |
|---|---|
| `snowflake` | `account`, `user`, `password`, `database`, `warehouse`, `schema` |
| `bigquery` | `project`, `dataset`, `credentials_path`, `location` |
| `duckdb` | `path` |

> The connection model is shared, so any field is technically accepted on either side; use the fields listed for your connector. `schema` is written as `schema:` in YAML.

### `transformation`
dbt transformation settings.

| Field | Type | Required | Default |
|---|---|---|---|
| `enabled` | bool | no | `false` |
| `project_dir` | string | no | `./transform` |

### `contracts`
Data-contract settings.

| Field | Type | Required | Default |
|---|---|---|---|
| `enabled` | bool | no | `true` |
| `directory` | string | no | `./contracts` |

### `quality`
Data-quality (Soda) settings.

| Field | Type | Required | Default |
|---|---|---|---|
| `enabled` | bool | no | `false` |
| `checks_dir` | string | no | `./quality` |

### `diagnostics`
AI settings. Required for `diagnose`, `architect`, `generate`, and AI-backed `migrate`.

| Field | Type | Required | Default |
|---|---|---|---|
| `enabled` | bool | no | `false` |
| `provider` | string | no | `none` |

`provider` is one of `anthropic`, `openai`, `ollama`, `deepseek`, `mistral`.

### `notifications`
Notification settings (Resend email).

| Field | Type | Required | Default |
|---|---|---|---|
| `enabled` | bool | no | `false` |
| `channels` | list of string | no | `[]` |
| `provider` | string | no | `resend` |
| `from_address` | string | no | `""` |
| `recipients` | list of string | no | `[]` |
| `notify_on` | list of string | no | `["pipeline_failed", "contract_violated"]` |

`provider` selects the alert channel:

| `provider` | Channel | Required env var | Notes |
|---|---|---|---|
| `resend` | Email | `RESEND_API_KEY` | Uses `from_address` and `recipients` |
| `slack` | Slack incoming webhook | `SLACK_WEBHOOK_URL` | Posts a Block Kit alert to the webhook's channel |

```yaml
# Slack alerting example
notifications:
  enabled: true
  provider: slack          # SLACK_WEBHOOK_URL must be set
  notify_on: ["pipeline_failed", "contract_violated"]
```

Credentials are never stored in config — Resend reads `RESEND_API_KEY` and Slack reads `SLACK_WEBHOOK_URL` from the environment (BYOK, ADR-005). A failing alert channel never blocks the pipeline; the failure is recorded with a `PK-NOTIFY-*` code. One `provider` is active at a time — simultaneous multi-channel delivery (email + Slack together) is a planned enhancement.

---

## Environment Variable Interpolation

Any string value may reference an environment variable with `${VAR}`. References are expanded from the environment when the config is loaded, before validation:

```yaml
ingestion:
  source:
    type: postgres
    host: "${PG_HOST}"
    user: "${PG_USER}"
    password: "${PG_PASSWORD}"
```

- **Which fields support it** — all string fields. It is intended for credentials and any environment-specific value.
- **Unset variables** resolve to an empty string; interpolation never raises. A required credential that ends up empty is caught later as `PK-CONFIG-006`.
- **Never hardcode credentials.** `pipelinekit.yaml` is committed; secrets must come from the environment (BYOK).

---

## Contract Format (`contracts/*.yaml`)

One file per table. A contract declares what "correct" means for that table.

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

| Key | Meaning |
|---|---|
| `table` | The table the contract applies to |
| `freshness` | Maximum age (`max_age_hours`) measured on a timestamp `column` |
| `required_columns` | Columns that must exist |
| `uniqueness` | Columns whose values must be unique |
| `not_null` | Columns that must contain no nulls |
| `row_count` | Acceptable row-count range (`min`, optionally `max`) |

Structural validity is checked by `pipelinekit validate --contracts`; data-level enforcement runs during `pipelinekit run`.

---

## Soda Checks Format (`quality/checks.yaml`)

Soda checks run against the destination during a run.

```yaml
checks for orders:
  - freshness(updated_at) < 12h
  - row_count > 0
  - missing_count(order_id) = 0
  - duplicate_count(order_id) = 0
  - invalid_count(status) = 0:
      valid values: [pending, confirmed, shipped, delivered, cancelled]
```

---

## Blueprint Manifest (`blueprint.json`)

Each blueprint declares its identity and capabilities. Validated against `schemas/blueprint.schema.json`.

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

| Field | Required | Meaning |
|---|---|---|
| `name`, `version` | yes | Blueprint identity |
| `source`, `destination` | yes | `type` plus the dlt source/destination name |
| `description` | no | One-line description |
| `contracts` | no | Paths to the blueprint's contract files |
| `tags`, `kpis` | no | Discovery metadata and the KPIs the pipeline serves |
| `deploy_time_minutes` | no | Target deploy time (default 60) |
| `time_to_trusted_data_hours` | no | Target Time-to-Trusted-Data (default 24) |
