# PipelineKit — Sprint 6-3 Implementation Prompt
## Blueprint #002 — Salesforce → Snowflake

---

## Your Identity

You are Claude Code operating as **blueprint-engineer** and **quality-engineer**.

Primary SPEC: `docs/specifications/SPEC-013-Blueprint-002-Salesforce-Snowflake.md`  
Pattern: `blueprints/postgres-to-snowflake/` — follow exactly

---

## Repository

```
C:\Users\HP\Documents\pipelinekit
```

---

## Sprint Goal

```powershell
poetry run pipelinekit blueprint list
# shows: postgres-to-snowflake, salesforce-to-snowflake

poetry run pipelinekit blueprint validate
# both blueprints valid

poetry run pipelinekit blueprint info salesforce-to-snowflake
# shows correct details

poetry run pytest --cov=src/pipelinekit --cov-fail-under=80
poetry run ruff check .
poetry run black --check .
poetry run mypy src/pipelinekit
```

All 225 prior tests must still pass.

---

## Files You Are Allowed To Create

```
blueprints/salesforce-to-snowflake/
├── blueprint.json
├── pipelinekit.example.yaml
├── ingestion/
│   └── pipeline.py
├── transform/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/
│       ├── sources.yml
│       ├── staging/
│       │   ├── stg_accounts.sql
│       │   ├── stg_opportunities.sql
│       │   └── stg_contacts.sql
│       └── core/
│           └── fct_opportunities.sql
├── contracts/
│   └── opportunities.yaml
├── quality/
│   └── checks.yaml
├── alerts/
│   └── config.yaml
└── docs/
    ├── README.md
    └── runbook.md

scripts/verify-blueprint-002.ps1

tests/blueprints/test_blueprint_002.py
```

You may also modify:
```
src/pipelinekit/config/schema.py          Add username, security_token to SourceConfig only
src/pipelinekit/adapters/ingestion/dlt/adapter.py   Add salesforce source handling only
docs/reference/Error-Codes.md            No new codes needed
```

---

## Files You Must Not Modify

```
docs/reference/PROJECT-STATUS.md         ← NEVER — Command Center owns it
blueprints/postgres-to-snowflake/        ← READ ONLY — do not touch Blueprint #001
All Phase 1-5 source files               ← READ ONLY (except schema.py + dlt adapter above)
All existing test files                  ← READ ONLY
schemas/                                 ← READ ONLY
contracts/                               ← READ ONLY (repo root contracts)
```

---

## Implementation Requirements

### 1. SourceConfig extension (schema.py)

Add two fields alongside existing credential fields:

```python
# Salesforce
username: Optional[str] = None
security_token: Optional[str] = None
```

`password` already exists. All new fields optional — backward compatible.

---

### 2. dlt adapter — add Salesforce source handling

In `_build_source()`, add a branch for Salesforce:

```python
elif source.type == "salesforce":
    from dlt.sources.salesforce import salesforce_source
    tables = source.tables or ["accounts", "opportunities", "contacts"]
    return salesforce_source(
        username=source.username,
        password=source.password,
        security_token=source.security_token,
    ).with_resources(*tables)
```

All salesforce imports stay inside this method — never at module level.
Add `dlt[salesforce]` to pyproject.toml if not already present.

---

### 3. blueprint.json

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

Validate against `schemas/blueprint.schema.json` before committing.

---

### 4. pipelinekit.example.yaml

All 8 config sections. All credentials use `${VAR}` interpolation. No ignored fields.

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

Verify it loads cleanly through `PipelineConfig` with `${VAR}` interpolation.

---

### 5. dbt models

See SPEC-013 for exact SQL. Key requirements:
- `sources.yml` uses `{{ env_var() }}` for database and schema — no hardcoded values
- All staging models use `{{ source('salesforce_raw', 'table_name') }}`
- `fct_opportunities.sql` joins opportunities + accounts
- `profiles.yml` has both `prod` (Snowflake) and `local` (DuckDB) targets — same pattern as Blueprint #001

---

### 6. contracts/opportunities.yaml

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

### 7. quality/checks.yaml

```yaml
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

### 8. alerts/config.yaml

```yaml
alerts:
  on_failure:
    - channel: email
      subject: "Blueprint #002 pipeline failed"
  on_contract_violation:
    - channel: email
      subject: "Blueprint #002 contract violated"
```

---

### 9. runbook.md

Must include all 7 sections from SPEC-013:
1. Overview
2. Prerequisites (complete env vars list)
3. Installation steps
4. First run walkthrough
5. Troubleshooting
6. Verified Deployments table (empty — Unverified)
7. Claim validation table (Unverified)

---

### 10. scripts/verify-blueprint-002.ps1

Same structure as `verify-blueprint-001.ps1`. Key difference:
- `-Local` mode uses a seeded DuckDB file with synthetic data (Salesforce requires real API credentials)
- Preflight checks for: `SALESFORCE_USERNAME`, `SALESFORCE_PASSWORD`, `SALESFORCE_SECURITY_TOKEN`, `SNOWFLAKE_*`
- Production mode: full Salesforce → Snowflake run

Local synthetic data seed:

```powershell
# In -Local mode, skip Salesforce ingestion
# Seed DuckDB directly with synthetic CRM data
poetry run python -c "
import duckdb
con = duckdb.connect('pipelinekit_pipeline.duckdb')
con.execute('''CREATE SCHEMA IF NOT EXISTS pipelinekit_pipeline_raw''')
con.execute('''CREATE OR REPLACE TABLE pipelinekit_pipeline_raw.accounts AS
  SELECT i as id, 'Account ' || i as name, 'Technology' as industry,
  (random()*10000000)::int as annual_revenue, (random()*500)::int as number_of_employees,
  'San Francisco' as billing_city, 'US' as billing_country,
  current_timestamp as created_date, current_timestamp as last_modified_date
  FROM range(1, 101) t(i)''')
con.execute('''CREATE OR REPLACE TABLE pipelinekit_pipeline_raw.opportunities AS
  SELECT i as id, (i % 100) + 1 as account_id, 'Opp ' || i as name,
  (random()*100000)::int as amount,
  (ARRAY['Prospecting','Qualification','Proposal','Closed Won','Closed Lost'])[floor(random()*5+1)::int] as stage_name,
  current_date + (random()*90)::int as close_date,
  (random()*100)::int as probability,
  false as is_won, false as is_closed,
  current_timestamp as created_date, current_timestamp as last_modified_date
  FROM range(1, 501) t(i)''')
con.execute('''CREATE OR REPLACE TABLE pipelinekit_pipeline_raw.contacts AS
  SELECT i as id, (i % 100) + 1 as account_id,
  'First' || i as first_name, 'Last' || i as last_name,
  'contact' || i || '@example.com' as email,
  'Manager' as title, 'Sales' as department,
  current_timestamp as created_date
  FROM range(1, 201) t(i)''')
print('Seeded: 100 accounts, 500 opportunities, 200 contacts')
"
```

---

## Test Requirements

All 225 prior tests must pass. New tests mock the Salesforce API.

**tests/blueprints/test_blueprint_002.py** — minimum 4 tests:
- Blueprint #002 validates against blueprint.schema.json
- `pipelinekit blueprint info salesforce-to-snowflake` returns correct metadata
- `pipelinekit blueprint list` shows both blueprints
- pipelinekit.example.yaml loads through PipelineConfig cleanly

---

## Smell 15 Enforcement

Before committing — verify all 8 assets exist:

```powershell
$assets = @(
  "blueprints\salesforce-to-snowflake\blueprint.json",
  "blueprints\salesforce-to-snowflake\pipelinekit.example.yaml",
  "blueprints\salesforce-to-snowflake\ingestion\pipeline.py",
  "blueprints\salesforce-to-snowflake\transform\dbt_project.yml",
  "blueprints\salesforce-to-snowflake\contracts\opportunities.yaml",
  "blueprints\salesforce-to-snowflake\quality\checks.yaml",
  "blueprints\salesforce-to-snowflake\alerts\config.yaml",
  "blueprints\salesforce-to-snowflake\docs\runbook.md"
)
$assets | ForEach-Object { 
  if (Test-Path $_) { "✓ $_" } else { "✗ MISSING: $_" }
}
```

All 8 must show ✓ before committing.

---

## Definition of Done

```
✓ All 8 blueprint assets exist and are complete
✓ blueprint.json validates against schemas/blueprint.schema.json
✓ pipelinekit blueprint list shows salesforce-to-snowflake
✓ pipelinekit blueprint validate exits 0 for both blueprints
✓ pipelinekit blueprint info salesforce-to-snowflake shows correct details
✓ pipelinekit.example.yaml loads through PipelineConfig cleanly
✓ SourceConfig has username and security_token fields
✓ dlt adapter handles type: salesforce
✓ dbt models parse cleanly (dbt parse exits 0 against local target)
✓ contracts/opportunities.yaml loads via ContractValidator
✓ scripts/verify-blueprint-002.ps1 exists and parses
✓ runbook.md has Verified Deployments table (empty)
✓ All 225 prior tests still pass
✓ coverage >= 80%
✓ ruff, black, mypy clean
✓ Blueprint #001 untouched — still validates
✓ PROJECT-STATUS.md untouched
```

---

## Commit Message

```
feat: Sprint 6-3 — Blueprint #002 Salesforce → Snowflake

- blueprints/salesforce-to-snowflake/ — all 8 assets
- src/pipelinekit/config/schema.py — username, security_token fields
- src/pipelinekit/adapters/ingestion/dlt/adapter.py — Salesforce source
- scripts/verify-blueprint-002.ps1 — verification harness with -Local mode
- tests/blueprints/test_blueprint_002.py — 4 blueprint tests

SPEC-013 satisfied. Blueprint catalog now has 2 production blueprints.
```
