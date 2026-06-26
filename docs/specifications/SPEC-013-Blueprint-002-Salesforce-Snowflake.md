# SPEC-013-Blueprint-002-Salesforce-Snowflake.md

**Status:** Approved  
**Owner:** blueprint-engineer  
**Phase:** 6 — Sprint 6-3  
**Date:** June 26, 2026  
**ADRs:** ADR-005 (BYOK), ADR-008 (Deterministic), ADR-017 (dlt Credential Integration)  
**Depends on:** SPEC-006 (Blueprint Engine), SPEC-009 (Provider Adapters)  
**Pattern:** blueprints/postgres-to-snowflake/ — follow exactly

---

## Purpose

Define Blueprint #002 — the second production-ready blueprint for PipelineKit.

Blueprint #002 ingests Salesforce CRM data into Snowflake, transforms it into trusted analytics models, enforces contracts, and validates quality. It follows the exact same 8-asset structure as Blueprint #001.

---

## Source / Destination

| Property | Value |
|---|---|
| Source | Salesforce (dlt `salesforce` source) |
| Destination | Snowflake |
| Primary tables | accounts, opportunities, contacts |
| dlt extra required | `dlt[salesforce]` |
| BYOK credentials | `SALESFORCE_USERNAME`, `SALESFORCE_PASSWORD`, `SALESFORCE_SECURITY_TOKEN`, `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`, `SNOWFLAKE_DATABASE`, `SNOWFLAKE_WAREHOUSE` |

---

## The 8 Required Blueprint Assets

All 8 must exist. No shortcuts (Smell 15).

```
blueprints/salesforce-to-snowflake/
├── blueprint.json                   ← Blueprint manifest
├── pipelinekit.example.yaml         ← Reference config (no ignored fields)
├── ingestion/
│   └── pipeline.py                  ← dlt Salesforce source
├── transform/
│   ├── dbt_project.yml
│   ├── profiles.yml                 ← Snowflake + local DuckDB targets
│   ├── models/
│   │   ├── sources.yml
│   │   ├── staging/
│   │   │   ├── stg_accounts.sql
│   │   │   ├── stg_opportunities.sql
│   │   │   └── stg_contacts.sql
│   │   └── core/
│   │       └── fct_opportunities.sql
├── contracts/
│   └── opportunities.yaml           ← Primary contract
├── quality/
│   └── checks.yaml                  ← Soda freshness + volume checks
├── alerts/
│   └── config.yaml
└── docs/
    ├── README.md
    └── runbook.md                   ← Includes Verified Deployments table
```

---

## blueprint.json

```json
{
  "name": "salesforce-to-snowflake",
  "version": "1.0.0",
  "description": "Salesforce CRM to Snowflake trusted analytics pipeline",
  "source": {"type": "salesforce"},
  "destination": {"type": "snowflake"},
  "tables": ["accounts", "opportunities", "contacts"],
  "deploy_time_minutes": 60,
  "time_to_trusted_data_hours": 4,
  "requires": ["dlt[salesforce]", "dbt-snowflake", "soda-core-snowflake"],
  "status": "stable"
}
```

---

## pipelinekit.example.yaml

All 8 config sections. All credential fields are first-class (ADR-017). All use `${VAR}` interpolation.

```yaml
pipeline:
  name: salesforce-to-snowflake-blueprint-002
  version: "1.0.0"
  description: "Blueprint #002 — Salesforce to Snowflake trusted analytics"

runtime:
  environment: production

ingestion:
  source:
    type: salesforce
    username: "${SALESFORCE_USERNAME}"
    password: "${SALESFORCE_PASSWORD}"
    security_token: "${SALESFORCE_SECURITY_TOKEN}"
    tables:
      - accounts
      - opportunities
      - contacts
  destination:
    type: snowflake
    account: "${SNOWFLAKE_ACCOUNT}"
    user: "${SNOWFLAKE_USER}"
    password: "${SNOWFLAKE_PASSWORD}"
    database: "${SNOWFLAKE_DATABASE}"
    warehouse: "${SNOWFLAKE_WAREHOUSE}"
    schema: "raw"

transformation:
  enabled: true
  project_dir: ./blueprints/salesforce-to-snowflake/transform

contracts:
  enabled: true
  directory: ./blueprints/salesforce-to-snowflake/contracts

quality:
  enabled: true
  checks_dir: ./blueprints/salesforce-to-snowflake/quality

diagnostics:
  enabled: true
  provider: anthropic

notifications:
  enabled: false
  channels: []
```

---

## SourceConfig Extension Needed

Salesforce credentials (`username`, `password`, `security_token`) are not yet in `SourceConfig`. Add to `src/pipelinekit/config/schema.py`:

```python
# Salesforce
username: Optional[str] = None
security_token: Optional[str] = None
```

`password` already exists from Sprint 6-2a.

---

## dlt Salesforce Source

```python
# ingestion/pipeline.py
from dlt.sources.salesforce import salesforce_source

source = salesforce_source(
    username=config.source.username,
    password=config.source.password,
    security_token=config.source.security_token,
).with_resources("accounts", "opportunities", "contacts")
```

dlt adapter must handle `type: salesforce` in `_build_source()`.

---

## dbt Models

### sources.yml

```yaml
sources:
  - name: salesforce_raw
    database: "{{ env_var('DBT_SOURCE_DATABASE') }}"
    schema: "{{ env_var('DBT_SOURCE_SCHEMA', 'pipelinekit_pipeline_raw') }}"
    tables:
      - name: accounts
      - name: opportunities
        columns:
          - name: id
            tests: [unique, not_null]
          - name: amount
            tests: [not_null]
          - name: stage_name
            tests: [not_null]
          - name: close_date
            tests: [not_null]
      - name: contacts
```

### stg_accounts.sql

```sql
with source as (
    select * from {{ source('salesforce_raw', 'accounts') }}
),
renamed as (
    select
        id as account_id,
        name as account_name,
        industry,
        annual_revenue,
        number_of_employees,
        billing_city,
        billing_country,
        created_date,
        last_modified_date
    from source
)
select * from renamed
```

### stg_opportunities.sql

```sql
with source as (
    select * from {{ source('salesforce_raw', 'opportunities') }}
),
renamed as (
    select
        id as opportunity_id,
        account_id,
        name as opportunity_name,
        amount,
        stage_name,
        close_date,
        probability,
        is_won,
        is_closed,
        created_date,
        last_modified_date
    from source
)
select * from renamed
```

### stg_contacts.sql

```sql
with source as (
    select * from {{ source('salesforce_raw', 'contacts') }}
),
renamed as (
    select
        id as contact_id,
        account_id,
        first_name,
        last_name,
        email,
        title,
        department,
        created_date
    from source
)
select * from renamed
```

### fct_opportunities.sql

```sql
with opportunities as (
    select * from {{ ref('stg_opportunities') }}
),
accounts as (
    select * from {{ ref('stg_accounts') }}
),
final as (
    select
        o.opportunity_id,
        o.opportunity_name,
        o.account_id,
        a.account_name,
        a.industry,
        o.amount,
        o.stage_name,
        o.close_date,
        o.probability,
        o.is_won,
        o.is_closed,
        o.created_date
    from opportunities o
    left join accounts a on o.account_id = a.account_id
)
select * from final
```

---

## contracts/opportunities.yaml

```yaml
version: 1
table: opportunities
source: salesforce_raw
columns:
  - name: id
    required: true
    unique: true
  - name: amount
    required: true
  - name: stage_name
    required: true
  - name: close_date
    required: true
freshness:
  max_age_hours: 4
row_count:
  min: 1
```

---

## quality/checks.yaml

```yaml
# Soda checks for Salesforce → Snowflake Blueprint #002
checks for opportunities:
  - freshness(last_modified_date) < 4h:
      name: opportunities_freshness
  - row_count > 0:
      name: opportunities_not_empty
  - missing_count(id) = 0:
      name: opportunities_id_not_null
  - missing_count(amount) = 0:
      name: opportunities_amount_not_null
```

---

## runbook.md Structure

Must include:
1. Overview
2. Prerequisites (env vars list)
3. Installation steps
4. First run walkthrough
5. Troubleshooting
6. Verified Deployments table (empty — filled after real run)
7. Claim validation table (Unverified until real run)

---

## Verification Script Addition

Add `-Local` support to `scripts/verify-blueprint-002.ps1` — same pattern as Blueprint #001 but with a mock Salesforce source for local testing (Salesforce requires real credentials, unlike Postgres).

Local mode for Blueprint #002 uses a seeded DuckDB file with synthetic accounts/opportunities/contacts data instead of live Salesforce API.

---

## Acceptance Criteria

```
✓ All 8 blueprint assets exist
✓ blueprint.json validates against schemas/blueprint.schema.json
✓ pipelinekit blueprint validate exits 0
✓ pipelinekit blueprint info salesforce-to-snowflake shows correct details
✓ All credential fields use ${VAR} interpolation — no hardcoded values
✓ SourceConfig extended with username, security_token fields
✓ dlt adapter handles type: salesforce in _build_source()
✓ dbt models parse cleanly (dbt parse exits 0)
✓ contracts/opportunities.yaml loads and validates
✓ quality/checks.yaml is valid Soda syntax
✓ runbook.md has Verified Deployments table (empty, pending real run)
✓ All 225 prior tests still pass
✓ coverage >= 80%
✓ ruff, black, mypy clean
✓ PROJECT-STATUS.md untouched
```

---

## Out of Scope

- Live Salesforce API test in CI — requires credentials
- Production Snowflake verification — manual run after deployment
- Blueprint #003 (Stripe → Snowflake) — separate SPEC-014
