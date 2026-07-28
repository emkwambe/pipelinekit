# PipelineKit Smoke Test Report
Date: 2026-07-27 19:19:50
Blueprint: stripe-to-snowflake
Result: 31/36 passed in 269.5s (4.5 minutes)

## Step Results
| Step | Status | Time |
|------|--------|------|
| EMS-LIST | PASS | 9.5s |
| EMS-DC | PASS | 7.7s |
| EMS-QM | PASS | 8.4s |
| BP-LIST | PASS | 8.8s |
| BP-BEST | PASS | 9.6s |
| BP-ALL | PASS | 8.1s |
| GOV-OWNER-SET | PASS | 7.6s |
| GOV-OWNER-LIST | PASS | 6.9s |
| GOV-CONV-ADD | PASS | 8.4s |
| GOV-CONV-CHECK | PASS | 7.1s |
| GOV-APPROVAL | PASS | 7.3s |
| GOV-APPROVAL-LIST | PASS | 7.9s |
| DC-SNAPSHOT | FAIL | 9.5s |
| DC-VERSION | PASS | 6.9s |
| DC-CONSUMER | PASS | 6.9s |
| DC-CONSUMER-LIST | PASS | 6.7s |
| DC-LIFECYCLE | FAIL | 7.5s |
| DC-NOTIFICATIONS | PASS | 7.5s |
| QM-COVERAGE | PASS | 6.3s |
| QM-RECORD | PASS | 4s |
| QM-ANOMALY | FAIL | 3.9s |
| QM-DRIFT | PASS | 3.5s |
| QM-FRESHNESS | PASS | 3.8s |
| QM-FRESHNESS-CHECK | FAIL | 3.9s |
| QM-SCORECARD | PASS | 3.2s |
| QM-REGRESSION | PASS | 3.1s |
| OM-SLO-SET | PASS | 3.1s |
| OM-SLO-LIST | PASS | 3.4s |
| OM-SLO-CHECK | FAIL | 4s |
| OM-DASHBOARD | PASS | 3.4s |
| AM-DEP-SCAN | PASS | 3.5s |
| AM-DEP-ADD | PASS | 3s |
| AM-DEP-LIST | PASS | 3.4s |
| AM-DEP-IMPACT | PASS | 4.1s |
| AM-DRIFT | PASS | 5.6s |
| HEALTH | PASS | 61.5s |


## Failed Steps
- **DC-SNAPSHOT**: Exit code: 2 (expected one of: 0)
- **DC-LIFECYCLE**: Exit code: 1 (expected one of: 0)
- **QM-ANOMALY**: Missing in output: 'stablishing'
- **QM-FRESHNESS-CHECK**: Exit code: 1 (expected one of: 0)
- **OM-SLO-CHECK**: Exit code: 1 (expected one of: 0)


## Notes
- HEALTH check time: 61.5s
- Target total time: < 30 minutes
- Actual total time: 4.5 minutes