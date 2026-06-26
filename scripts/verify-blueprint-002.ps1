# scripts/verify-blueprint-002.ps1
# Blueprint #002 — Salesforce → Snowflake Verification Script
#
# Production (default): requires real Salesforce + Snowflake credentials —
#   SALESFORCE_USERNAME, SALESFORCE_PASSWORD, SALESFORCE_SECURITY_TOKEN,
#   SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD,
#   SNOWFLAKE_DATABASE, SNOWFLAKE_WAREHOUSE
#
# -Local: no credentials needed. Salesforce requires a real API, so local mode
#   seeds a DuckDB file with synthetic accounts/opportunities/contacts and runs
#   dbt against it — proving the transform → contract → quality chain offline.

param([switch]$Local)

$start = Get-Date

Write-Host "=== Blueprint #002 Verification ===" -ForegroundColor Cyan
Write-Host "Started: $start"

# Step 0: Preflight
if ($Local) {
    Write-Host "Mode: LOCAL (synthetic DuckDB — no Salesforce/Snowflake creds)" -ForegroundColor Cyan
    $required = @()
} else {
    Write-Host "Mode: PRODUCTION (Salesforce -> Snowflake)" -ForegroundColor Cyan
    $required = @("SALESFORCE_USERNAME", "SALESFORCE_PASSWORD", "SALESFORCE_SECURITY_TOKEN",
                  "SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD",
                  "SNOWFLAKE_DATABASE", "SNOWFLAKE_WAREHOUSE")
}
$missing = $required | Where-Object { -not [Environment]::GetEnvironmentVariable($_) }
if ($missing) {
    Write-Host "✗ Missing env vars: $($missing -join ', ')" -ForegroundColor Red
    Write-Host "  Set all required variables before running this script."
    exit 1
}

# Step 1: Use Blueprint #002 config (copy example — paths already point at the blueprint).
Copy-Item "blueprints\salesforce-to-snowflake\pipelinekit.example.yaml" "pipelinekit.yaml" -Force

if ($Local) {
    # dbt builds against the seeded local DuckDB file.
    $env:DBT_TARGET = "local"
    $env:DUCKDB_PATH = "pipelinekit_pipeline.duckdb"
    $env:DBT_SOURCE_DATABASE = "pipelinekit_pipeline"
    $env:DBT_SOURCE_SCHEMA = "pipelinekit_pipeline_raw"

    # Seed synthetic Salesforce CRM data into DuckDB (no live API).
    $seed = @'
import duckdb

con = duckdb.connect("pipelinekit_pipeline.duckdb")
con.execute("CREATE SCHEMA IF NOT EXISTS pipelinekit_pipeline_raw")
con.execute("""
    CREATE OR REPLACE TABLE pipelinekit_pipeline_raw.accounts AS
    SELECT i AS id, 'Account ' || i AS name, 'Technology' AS industry,
        (random()*10000000)::int AS annual_revenue,
        (random()*500)::int AS number_of_employees,
        'San Francisco' AS billing_city, 'US' AS billing_country,
        current_timestamp AS created_date, current_timestamp AS last_modified_date
    FROM range(1, 101) t(i)
""")
con.execute("""
    CREATE OR REPLACE TABLE pipelinekit_pipeline_raw.opportunities AS
    SELECT i AS id, (i % 100) + 1 AS account_id, 'Opp ' || i AS name,
        (random()*100000)::int AS amount,
        (ARRAY['Prospecting','Qualification','Proposal','Closed Won','Closed Lost'])[floor(random()*5+1)::int] AS stage_name,
        current_date + (random()*90)::int AS close_date,
        (random()*100)::int AS probability,
        false AS is_won, false AS is_closed,
        current_timestamp AS created_date, current_timestamp AS last_modified_date
    FROM range(1, 501) t(i)
""")
con.execute("""
    CREATE OR REPLACE TABLE pipelinekit_pipeline_raw.contacts AS
    SELECT i AS id, (i % 100) + 1 AS account_id,
        'First' || i AS first_name, 'Last' || i AS last_name,
        'contact' || i || '@example.com' AS email,
        'Manager' AS title, 'Sales' AS department,
        current_timestamp AS created_date
    FROM range(1, 201) t(i)
""")
con.close()
print("Seeded: 100 accounts, 500 opportunities, 200 contacts")
'@
    $seed | poetry run python -

    # Transform the synthetic data through dbt (staging + core).
    poetry run dbt build `
        --project-dir blueprints/salesforce-to-snowflake/transform `
        --profiles-dir blueprints/salesforce-to-snowflake/transform `
        --target local
} else {
    poetry run pipelinekit validate
    poetry run pipelinekit blueprint validate
    poetry run pipelinekit run --dry-run
    poetry run pipelinekit run
    poetry run pipelinekit validate --contracts
}

$end = Get-Date
$total = ($end - $start).TotalMinutes

Write-Host ""
Write-Host "=== Verification Complete ===" -ForegroundColor Cyan
Write-Host "Total time: $([math]::Round($total, 1)) minutes"
Write-Host ""
Write-Host "Record this result in:"
Write-Host "blueprints/salesforce-to-snowflake/docs/runbook.md"
Write-Host "Section: Verified Deployments"
