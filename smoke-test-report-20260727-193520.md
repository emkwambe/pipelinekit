# PipelineKit Smoke Test Report
Date: 2026-07-27 19:35:20
Blueprint: stripe-to-snowflake
Result: 36/36 passed in 3.5 minutes

## Step Results
| Step | Status | Time |
|------|--------|------|
| EMS-LIST | PASS | 4.4s |
| EMS-DC | PASS | 3.1s |
| EMS-QM | PASS | 2.9s |
| BP-LIST | PASS | 2.9s |
| BP-BEST | PASS | 3.3s |
| BP-ALL | PASS | 3s |
| GOV-OWNER-SET | PASS | 2.9s |
| GOV-OWNER-LIST | PASS | 3s |
| GOV-CONV-ADD | PASS | 2.9s |
| GOV-CONV-CHECK | PASS | 2.9s |
| GOV-APPROVAL | PASS | 2.9s |
| GOV-APPROVAL-LIST | PASS | 3.1s |
| DC-SNAPSHOT | PASS | 4s |
| DC-VERSION | PASS | 3.8s |
| DC-CONSUMER | PASS | 3.9s |
| DC-CONSUMER-LIST | PASS | 4.1s |
| DC-LIFECYCLE | PASS | 4.1s |
| DC-NOTIFICATIONS | PASS | 4.3s |
| QM-COVERAGE | PASS | 4.6s |
| QM-RECORD | PASS | 3.8s |
| QM-ANOMALY | PASS | 3.3s |
| QM-DRIFT | PASS | 3.6s |
| QM-FRESHNESS | PASS | 3.5s |
| QM-FRESHNESS-CHECK | PASS | 4.2s |
| QM-SCORECARD | PASS | 4.3s |
| QM-REGRESSION | PASS | 3.9s |
| OM-SLO-SET | PASS | 6.2s |
| OM-SLO-LIST | PASS | 4.4s |
| OM-SLO-CHECK | PASS | 4.1s |
| OM-DASHBOARD | PASS | 3.7s |
| AM-DEP-SCAN | PASS | 4s |
| AM-DEP-ADD | PASS | 3.8s |
| AM-DEP-LIST | PASS | 4s |
| AM-DEP-IMPACT | PASS | 3.7s |
| AM-DRIFT | PASS | 4.5s |
| HEALTH | PASS | 77.8s |


## Notes
- Steps that exit 1 are often correct behavior (STALE, VIOLATED, etc.)
- HEALTH check time: 77.8s
- Run pipelinekit run to populate EMS with real pipeline data