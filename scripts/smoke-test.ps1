# PipelineKit Smoke Test Script
# scripts/smoke-test.ps1
#
# Simulates the first 30 minutes of a design partner onboarding session.
# Run this before every design partner session and after every major change.
#
# Usage:
#   cd C:\Users\HP\Documents\pipelinekit
#   .\scripts\smoke-test.ps1
#
# What it tests:
#   1.  Blueprint catalog
#   2.  Blueprint best practices
#   3.  EMS catalog
#   4.  Governance — owner assignment
#   5.  Contract snapshot
#   6.  Quality coverage
#   7.  Row count recording
#   8.  Anomaly detection
#   9.  Schema drift detection
#   10. Quality scorecard
#   11. Regression check
#   12. SLO definition and check
#   13. Observability dashboard
#   14. Dependency mapping
#   15. Architecture drift
#   16. Health check (full 11 checks)
#   17. EMS status summary
#
# Exit codes:
#   0 = all commands succeeded
#   1 = one or more commands failed

param(
    [string]$Blueprint = "stripe-to-snowflake",
    [switch]$Verbose,
    [switch]$TimingOnly
)

$ErrorActionPreference = "Stop"
$StartTime = Get-Date
$Passed = 0
$Failed = 0
$Results = @()

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
}

function Run-Step {
    param(
        [string]$Name,
        [string]$Description,
        [scriptblock]$Command,
        [string[]]$ExpectInOutput = @(),
        [int]$ExpectExitCode = 0
    )

    $StepStart = Get-Date
    Write-Host ""
    Write-Host "[$Name]" -ForegroundColor Yellow -NoNewline
    Write-Host " $Description"

    try {
        $output = & $Command 2>&1 | Out-String
        $exitCode = $LASTEXITCODE

        $elapsed = [math]::Round(((Get-Date) - $StepStart).TotalSeconds, 1)

        # Check expected exit code
        $exitOk = ($exitCode -eq $ExpectExitCode) -or
                  ($ExpectExitCode -eq 0 -and $exitCode -in @(0, 1))

        # Check expected output strings
        $outputOk = $true
        $missingStrings = @()
        foreach ($expected in $ExpectInOutput) {
            if ($output -notmatch [regex]::Escape($expected)) {
                $outputOk = $false
                $missingStrings += $expected
            }
        }

        if ($exitOk -and $outputOk) {
            Write-Host "  ✓ PASS ($($elapsed)s)" -ForegroundColor Green
            if ($Verbose) { Write-Host $output }
            $script:Passed++
            $script:Results += [PSCustomObject]@{
                Step = $Name
                Status = "PASS"
                Elapsed = $elapsed
                Detail = ""
            }
        } else {
            $detail = ""
            if (-not $exitOk) {
                $detail = "Exit code: $exitCode (expected $ExpectExitCode)"
            }
            if (-not $outputOk) {
                $detail += " Missing: $($missingStrings -join ', ')"
            }
            Write-Host "  ✗ FAIL ($($elapsed)s) — $detail" -ForegroundColor Red
            if ($Verbose -or -not $exitOk) { Write-Host $output }
            $script:Failed++
            $script:Results += [PSCustomObject]@{
                Step = $Name
                Status = "FAIL"
                Elapsed = $elapsed
                Detail = $detail.Trim()
            }
        }
    } catch {
        $elapsed = [math]::Round(((Get-Date) - $StepStart).TotalSeconds, 1)
        Write-Host "  ✗ ERROR ($($elapsed)s) — $($_.Exception.Message)" -ForegroundColor Red
        $script:Failed++
        $script:Results += [PSCustomObject]@{
            Step = $Name
            Status = "ERROR"
            Elapsed = $elapsed
            Detail = $_.Exception.Message
        }
    }
}

# ─────────────────────────────────────────────────────────────
Write-Header "PipelineKit Smoke Test"
Write-Host "Blueprint: $Blueprint"
Write-Host "Started:   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "Directory: $(Get-Location)"
# ─────────────────────────────────────────────────────────────

Write-Header "1. EMS Catalog"

Run-Step "EMS-LIST" "List all 12 Engineering Management Systems" {
    poetry run pipelinekit ems list
} -ExpectInOutput @("DC", "QM", "GM", "OM", "AM", "AI", "%")

Run-Step "EMS-DC" "Show Data Contract Management status" {
    poetry run pipelinekit ems status dc
} -ExpectInOutput @("DC-8", "DC-9", "DC-10", "DC-11")

Run-Step "EMS-QM" "Show Quality Management status" {
    poetry run pipelinekit ems status qm
} -ExpectInOutput @("QM-4", "QM-6", "QM-7", "QM-8", "QM-9")

# ─────────────────────────────────────────────────────────────
Write-Header "2. Blueprint Catalog"

Run-Step "BP-LIST" "List installed blueprints" {
    poetry run pipelinekit blueprint list
} -ExpectInOutput @($Blueprint)

Run-Step "BP-BEST" "Check best practices for $Blueprint" {
    poetry run pipelinekit quality check-best-practices --blueprint $Blueprint
} -ExpectInOutput @("Grade:", "BP-001", "BP-002", "BP-003")

Run-Step "BP-ALL" "Check best practices for all blueprints" {
    poetry run pipelinekit quality check-best-practices
} -ExpectInOutput @("Grade:")

# ─────────────────────────────────────────────────────────────
Write-Header "3. Governance"

Run-Step "GOV-OWNER-SET" "Assign owner to $Blueprint" {
    poetry run pipelinekit governance owner set $Blueprint `
        --name "Smoke Test Engineer" `
        --email "smoke@test.com"
} -ExpectInOutput @($Blueprint)

Run-Step "GOV-OWNER-LIST" "List all blueprint owners" {
    poetry run pipelinekit governance owner list
} -ExpectInOutput @("smoke@test.com")

Run-Step "GOV-CONV-ADD" "Add naming convention" {
    poetry run pipelinekit governance convention add `
        --scope table `
        --pattern "^(stg|fct|dim|raw)_[a-z_]+" `
        --description "Table prefix convention"
}

Run-Step "GOV-CONV-CHECK" "Check $Blueprint against conventions" {
    poetry run pipelinekit governance convention check $Blueprint
}

Run-Step "GOV-APPROVAL" "Request approval for a change" {
    poetry run pipelinekit governance approval request `
        --blueprint $Blueprint `
        --change "Upgrade to v1.1.0" `
        --requested-by "engineer@company.com"
} -ExpectInOutput @("REQ-001")

Run-Step "GOV-APPROVAL-LIST" "List pending approvals" {
    poetry run pipelinekit governance approval list
} -ExpectInOutput @("REQ-001")

# ─────────────────────────────────────────────────────────────
Write-Header "4. Data Contract Management"

Run-Step "DC-SNAPSHOT" "Snapshot contracts for $Blueprint" {
    poetry run pipelinekit contract snapshot $Blueprint
}

Run-Step "DC-VERSION" "Show contract version history" {
    poetry run pipelinekit contract version $Blueprint
}

Run-Step "DC-CONSUMER" "Register a contract consumer" {
    poetry run pipelinekit contract consumer add $Blueprint `
        --email "analyst@company.com" `
        --table "charges"
}

Run-Step "DC-CONSUMER-LIST" "List contract consumers" {
    poetry run pipelinekit contract consumer list
} -ExpectInOutput @("analyst@company.com")

Run-Step "DC-LIFECYCLE" "Set contract lifecycle state" {
    poetry run pipelinekit contract lifecycle set $Blueprint `
        --contract "charges.yaml" `
        --state "active"
}

Run-Step "DC-NOTIFICATIONS" "Check contract notifications" {
    poetry run pipelinekit contract notifications
}

# ─────────────────────────────────────────────────────────────
Write-Header "5. Quality Management"

Run-Step "QM-COVERAGE" "Run quality coverage check" {
    poetry run pipelinekit quality coverage --blueprint $Blueprint
} -ExpectInOutput @("Coverage")

Run-Step "QM-RECORD" "Record row counts" {
    poetry run pipelinekit quality record-counts `
        --blueprint $Blueprint `
        --table "charges:45231" `
        --table "customers:12840"
}

Run-Step "QM-ANOMALY" "Check for volume anomalies" {
    poetry run pipelinekit quality check-anomalies --blueprint $Blueprint
} -ExpectInOutput @("ESTABLISHING")

Run-Step "QM-DRIFT" "Check for schema drift" {
    poetry run pipelinekit quality check-drift --blueprint $Blueprint
}

Run-Step "QM-FRESHNESS" "Set freshness requirement" {
    poetry run pipelinekit quality freshness set $Blueprint `
        --table "charges" `
        --hours 6
}

Run-Step "QM-FRESHNESS-CHECK" "Check freshness compliance" {
    poetry run pipelinekit quality freshness check $Blueprint
}

Run-Step "QM-SCORECARD" "Run quality scorecard" {
    poetry run pipelinekit quality scorecard --blueprint $Blueprint
} -ExpectInOutput @("Score", "Rating")

Run-Step "QM-REGRESSION" "Check for quality regression" {
    poetry run pipelinekit quality check-regression --blueprint $Blueprint
}

# ─────────────────────────────────────────────────────────────
Write-Header "6. Observability Management"

Run-Step "OM-SLO-SET" "Define freshness SLO" {
    poetry run pipelinekit observability slo set $Blueprint `
        --table "charges" `
        --type "freshness" `
        --threshold 6 `
        --unit "hours"
}

Run-Step "OM-SLO-LIST" "List defined SLOs" {
    poetry run pipelinekit observability slo list
} -ExpectInOutput @("charges")

Run-Step "OM-SLO-CHECK" "Evaluate SLO compliance" {
    poetry run pipelinekit observability slo check $Blueprint
}

Run-Step "OM-DASHBOARD" "Show SLO compliance dashboard" {
    poetry run pipelinekit observability dashboard
}

# ─────────────────────────────────────────────────────────────
Write-Header "7. Architecture Management"

Run-Step "AM-DEP-SCAN" "Scan for blueprint dependencies" {
    poetry run pipelinekit architect dependency scan
}

Run-Step "AM-DEP-ADD" "Add manual dependency" {
    poetry run pipelinekit architect dependency add `
        "postgres-to-snowflake" `
        $Blueprint `
        --type "manual" `
        --reason "orders feed stripe reconciliation"
}

Run-Step "AM-DEP-LIST" "List all dependencies" {
    poetry run pipelinekit architect dependency list
}

Run-Step "AM-DEP-IMPACT" "Show impact of postgres-to-snowflake changes" {
    poetry run pipelinekit architect dependency impact "postgres-to-snowflake"
}

Run-Step "AM-DRIFT" "Check architecture drift" {
    poetry run pipelinekit architect drift
}

# ─────────────────────────────────────────────────────────────
Write-Header "8. Health Check (Full 11 Checks)"

Run-Step "HEALTH" "Run full health check" {
    poetry run pipelinekit health --strict
} -ExpectInOutput @(
    "deps", "security", "blueprints", "specs", "tests", "ownership",
    "quality_score", "slo_violations", "volume_anomalies",
    "schema_drift", "architecture_drift"
)

# ─────────────────────────────────────────────────────────────
Write-Header "Results"

$TotalTime = [math]::Round(((Get-Date) - $StartTime).TotalSeconds, 1)
$Total = $Passed + $Failed

Write-Host ""
Write-Host "─" * 60
Write-Host "  Smoke Test Complete"
Write-Host "─" * 60
Write-Host ""
Write-Host "  Passed:  $Passed / $Total" -ForegroundColor $(if ($Failed -eq 0) { "Green" } else { "Yellow" })
Write-Host "  Failed:  $Failed / $Total" -ForegroundColor $(if ($Failed -eq 0) { "Green" } else { "Red" })
Write-Host "  Time:    $($TotalTime)s"
Write-Host ""

if ($Failed -gt 0) {
    Write-Host "  Failed steps:" -ForegroundColor Red
    $Results | Where-Object { $_.Status -ne "PASS" } | ForEach-Object {
        Write-Host "    ✗ $($_.Step): $($_.Detail)" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "  Step timing:" -ForegroundColor Cyan
$Results | ForEach-Object {
    $color = if ($_.Status -eq "PASS") { "Green" } else { "Red" }
    $symbol = if ($_.Status -eq "PASS") { "✓" } else { "✗" }
    Write-Host "    $symbol $($_.Step.PadRight(25)) $($_.Elapsed)s" -ForegroundColor $color
}

Write-Host ""
Write-Host "  Target: all steps in under 30 minutes total"
Write-Host "  Actual: $($TotalTime)s ($([math]::Round($TotalTime/60, 1)) minutes)"
Write-Host ""

if ($TotalTime -gt 1800) {
    Write-Host "  ⚠ Total time exceeds 30-minute target" -ForegroundColor Yellow
    Write-Host "    Investigate slow steps before design partner session"
}

# Export results to markdown for design partner prep
$reportPath = "smoke-test-report-$(Get-Date -Format 'yyyyMMdd-HHmmss').md"
$report = @"
# PipelineKit Smoke Test Report
Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Blueprint: $Blueprint
Result: $Passed/$Total passed in $($TotalTime)s

## Step Results
| Step | Status | Time |
|------|--------|------|
$($Results | ForEach-Object { "| $($_.Step) | $($_.Status) | $($_.Elapsed)s |" } | Out-String)

## Failed Steps
$($Results | Where-Object { $_.Status -ne "PASS" } | ForEach-Object { "- **$($_.Step)**: $($_.Detail)" } | Out-String)
"@
$report | Out-File $reportPath -Encoding UTF8
Write-Host "  Report saved: $reportPath"
Write-Host ""

# Exit with failure if any steps failed
if ($Failed -gt 0) { exit 1 }
exit 0
