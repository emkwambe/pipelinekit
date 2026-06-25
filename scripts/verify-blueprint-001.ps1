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
