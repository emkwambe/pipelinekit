# PipelineKit — Blueprint #001 Integration Verification Sprint
## Real Postgres → Snowflake End-to-End Test + Runbook Evidence

---

## Purpose

Blueprint #001 claims `deploy_time_minutes: 60` and `time_to_trusted_data_hours: 24`.

These are currently assertions, not evidence.

This sprint turns them into verified facts by running Blueprint #001 against a real Postgres source and Snowflake destination, documenting the result, and updating the runbook with the first verified deployment record.

This is not a Claude Code sprint. This is an Eddy sprint — manual verification with documentation.

Claude Code supports by: writing the verification script, updating the runbook template, and producing the evidence table structure.

---

## Prerequisites (Eddy verifies before starting)

```
□ Postgres instance accessible (local Docker or cloud)
  - Minimum: orders table with 10,000+ rows
  - Columns: id, customer_id, amount, status, created_at, updated_at

□ Snowflake account accessible
  - Warehouse: any XS or S
  - Database: pipelinekit_test (create if needed)
  - Role with CREATE TABLE permissions

□ PipelineKit installed and green
  - poetry run pipelinekit --help works
  - poetry run pytest passes

□ Environment variables set:
  - PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD
  - SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD
  - SNOWFLAKE_DATABASE, SNOWFLAKE_WAREHOUSE, SNOWFLAKE_SCHEMA
```

---

## What Claude Code Builds

### 1. Verification Script

```
scripts/verify-blueprint-001.ps1
```

A PowerShell script that runs the full Blueprint #001 verification sequence and times each step.

```powershell
# scripts/verify-blueprint-001.ps1
# Blueprint #001 — Postgres → Snowflake Verification Script
# Run after setting all required environment variables

$start = Get-Date

Write-Host "=== Blueprint #001 Verification ===" -ForegroundColor Cyan
Write-Host "Started: $start"

# Step 1: Initialize project
$step1_start = Get-Date
poetry run pipelinekit init
poetry run pipelinekit validate
$step1_end = Get-Date
$step1_time = ($step1_end - $step1_start).TotalSeconds
Write-Host "Step 1 (init + validate): ${step1_time}s" -ForegroundColor Green

# Step 2: Run blueprint validate
$step2_start = Get-Date
poetry run pipelinekit blueprint validate
$step2_end = Get-Date
$step2_time = ($step2_end - $step2_start).TotalSeconds
Write-Host "Step 2 (blueprint validate): ${step2_time}s" -ForegroundColor Green

# Step 3: Run pipeline --dry-run
$step3_start = Get-Date
poetry run pipelinekit run --dry-run
$step3_end = Get-Date
$step3_time = ($step3_end - $step3_start).TotalSeconds
Write-Host "Step 3 (dry-run): ${step3_time}s" -ForegroundColor Green

# Step 4: Run full pipeline
$step4_start = Get-Date
poetry run pipelinekit run
$step4_end = Get-Date
$step4_time = ($step4_end - $step4_start).TotalSeconds
Write-Host "Step 4 (full run): ${step4_time}s" -ForegroundColor Green

# Step 5: Validate contracts
$step5_start = Get-Date
poetry run pipelinekit validate --contracts
$step5_end = Get-Date
$step5_time = ($step5_end - $step5_start).TotalSeconds
Write-Host "Step 5 (contract validation): ${step5_time}s" -ForegroundColor Green

# Step 6: Run diagnose
$step6_start = Get-Date
poetry run pipelinekit diagnose
$step6_end = Get-Date
$step6_time = ($step6_end - $step6_start).TotalSeconds
Write-Host "Step 6 (diagnose): ${step6_time}s" -ForegroundColor Green

$end = Get-Date
$total = ($end - $start).TotalMinutes

Write-Host ""
Write-Host "=== Verification Complete ===" -ForegroundColor Cyan
Write-Host "Total time: $([math]::Round($total, 1)) minutes"
Write-Host ""
Write-Host "Record this result in:"
Write-Host "blueprints/postgres-to-snowflake/docs/runbook.md"
Write-Host "Section: Verified Deployments"
```

### 2. Runbook — Add Verified Deployments Section

Add to `blueprints/postgres-to-snowflake/docs/runbook.md`:

```markdown
## Verified Deployments

This table records real end-to-end deployments of Blueprint #001.
Each row represents a verified run by a named tester on a real environment.
This is the evidence behind the `deploy_time_minutes: 60` claim in blueprint.json.

| Date | Tester | Postgres Version | Snowflake Tier | Rows Ingested | Deploy Time | Data Latency | Contracts | Status |
|---|---|---|---|---|---|---|---|---|
| TBD | Eddy Mkwambe | TBD | TBD | TBD | TBD | TBD | All passed | TBD |

### How to Add a Row

After running scripts/verify-blueprint-001.ps1 successfully:
1. Fill in the row above with your actual results
2. Commit: git commit -m "Blueprint #001 verified — [date] by [name]"
3. This record is permanent institutional memory

### Claim Validation

| Claim in blueprint.json | Status | Evidence |
|---|---|---|
| deploy_time_minutes: 60 | Unverified until first row above | — |
| time_to_trusted_data_hours: 24 | Unverified until first row above | — |
```

### 3. pipelinekit.yaml — Blueprint #001 Reference Config

Create `blueprints/postgres-to-snowflake/pipelinekit.example.yaml` — a complete working config for this blueprint:

```yaml
# pipelinekit.example.yaml
# Copy to your project root as pipelinekit.yaml and fill in your credentials

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
    user: "${SNOWFLAKE_USER}"
    password: "${SNOWFLAKE_PASSWORD}"
    database: "${SNOWFLAKE_DATABASE}"
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

---

## Files Claude Code Creates

```
scripts/verify-blueprint-001.ps1
blueprints/postgres-to-snowflake/pipelinekit.example.yaml
```

Files Claude Code modifies:
```
blueprints/postgres-to-snowflake/docs/runbook.md    Add Verified Deployments section
```

Files Claude Code must not touch:
```
docs/reference/PROJECT-STATUS.md    Command Center owns
Any source code in src/
Any test file
```

---

## Definition of Done (Claude Code portion)

```
✓ scripts/verify-blueprint-001.ps1 exists and is valid PowerShell
✓ pipelinekit.example.yaml exists with all 8 config sections
✓ runbook.md has Verified Deployments section with empty table
✓ runbook.md has claim validation table
✓ All existing tests still pass
✓ ruff / black / mypy clean
✓ PROJECT-STATUS.md untouched
```

## Definition of Done (Eddy portion — manual)

```
✓ verify-blueprint-001.ps1 runs successfully against real Postgres + Snowflake
✓ Verified Deployments table has at least one row with real numbers
✓ deploy_time_minutes claim validated (or updated if wrong)
✓ Committed: "Blueprint #001 verified — [date] by Eddy Mkwambe"
```

---

## Commit Message

```
feat: Blueprint #001 verification infrastructure

- scripts/verify-blueprint-001.ps1 — end-to-end timing script
- blueprints/postgres-to-snowflake/pipelinekit.example.yaml — reference config
- blueprints/postgres-to-snowflake/docs/runbook.md — Verified Deployments section added

First actual deployment record to be added by Eddy after running against
real Postgres + Snowflake. That commit closes the loop on the 60-minute claim.
```
