# scripts/verify-blueprint-001.ps1
# Blueprint #001 — Postgres → Snowflake Verification Script
# Run after setting all required environment variables:
#   PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD
#   SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD
#   SNOWFLAKE_DATABASE, SNOWFLAKE_WAREHOUSE, SNOWFLAKE_SCHEMA
#
# This script times each step of the full Blueprint #001 deployment so the
# 60-minute deploy_time claim can be replaced with verified evidence. Record the
# result in blueprints/postgres-to-snowflake/docs/runbook.md (Verified Deployments).
#
# Pass -Local to run the standard local verification path: Docker Postgres source
# -> DuckDB destination (no Snowflake credentials needed). Without -Local the
# script runs the production path: Postgres -> Snowflake.

param([switch]$Local)

$start = Get-Date

Write-Host "=== Blueprint #001 Verification ===" -ForegroundColor Cyan
Write-Host "Started: $start"

# Step 0: Preflight — required environment variables must be set.
# Local mode (Postgres -> DuckDB) needs only the Postgres source variables.
if ($Local) {
    $required = @("PG_HOST", "PG_DATABASE", "PG_USER", "PG_PASSWORD")
    Write-Host "Mode: LOCAL (Docker Postgres -> DuckDB)" -ForegroundColor Cyan
} else {
    $required = @("POSTGRES_CONN_STR", "PG_HOST", "PG_DATABASE",
                  "SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD",
                  "SNOWFLAKE_DATABASE", "SNOWFLAKE_WAREHOUSE")
    Write-Host "Mode: PRODUCTION (Postgres -> Snowflake)" -ForegroundColor Cyan
}
$missing = $required | Where-Object { -not [Environment]::GetEnvironmentVariable($_) }
if ($missing) {
    Write-Host "✗ Missing env vars: $($missing -join ', ')" -ForegroundColor Red
    Write-Host "  Set all required variables before running this script."
    exit 1
}

# Step 1: Use Blueprint #001 config (copy example config — not pipelinekit init)
$step1_start = Get-Date
Copy-Item "blueprints\postgres-to-snowflake\pipelinekit.example.yaml" "pipelinekit.yaml" -Force
# Point contracts at the blueprint's data contract, not the repo architecture contracts.
$config = Get-Content "pipelinekit.yaml" -Raw
$config = $config -replace "directory: ./contracts", "directory: ./blueprints/postgres-to-snowflake/contracts"
# Point transformation (dbt project) and quality (Soda checks) at the blueprint's
# own directories — applies to both local and production verification.
$config = $config -replace 'project_dir: \./transform', 'project_dir: ./blueprints/postgres-to-snowflake/transform'
$config = $config -replace 'checks_dir: \./quality', 'checks_dir: ./blueprints/postgres-to-snowflake/quality'
# Local mode: replace the Snowflake destination block with a local DuckDB file.
if ($Local) {
    # dlt writes to this exact file (the adapter honors destination.path); dbt
    # reads the same file. Use dlt's conventional <pipeline_name>.duckdb name so
    # both sides — and the catalog (file stem) — align on one database.
    $duckDestination = @"
  destination:
    type: duckdb
    path: "pipelinekit_pipeline.duckdb"
"@
    $config = [regex]::Replace($config, '(?m)^  destination:\r?\n(?:    .*\r?\n?)+', $duckDestination)

    # dbt builds against the same DuckDB file: catalog = file stem, schema = the
    # dlt-loaded dataset name.
    $env:DBT_TARGET = "local"
    $env:DUCKDB_PATH = "pipelinekit_pipeline.duckdb"
    $env:DBT_SOURCE_DATABASE = "pipelinekit_pipeline"
    $env:DBT_SOURCE_SCHEMA = "pipelinekit_pipeline_raw"
}
Set-Content "pipelinekit.yaml" $config
poetry run pipelinekit validate
$step1_end = Get-Date
$step1_time = ($step1_end - $step1_start).TotalSeconds
Write-Host "Step 1 (config + validate): ${step1_time}s" -ForegroundColor Green

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
