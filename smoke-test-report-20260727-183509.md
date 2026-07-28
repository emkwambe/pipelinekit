# PipelineKit Smoke Test Report
Date: 2026-07-27 18:35:09
Blueprint: stripe-to-snowflake
Result: 31/36 passed in 178.3s

## Step Results
| Step | Status | Time |
|------|--------|------|
| EMS-LIST | PASS | 9.2s |
| EMS-DC | PASS | 7.7s |
| EMS-QM | PASS | 7.3s |
| BP-LIST | PASS | 7.5s |
| BP-BEST | PASS | 8.1s |
| BP-ALL | PASS | 7s |
| GOV-OWNER-SET | PASS | 3s |
| GOV-OWNER-LIST | PASS | 3.1s |
| GOV-CONV-ADD | PASS | 3.2s |
| GOV-CONV-CHECK | PASS | 3s |
| GOV-APPROVAL | FAIL | 3.3s |
| GOV-APPROVAL-LIST | FAIL | 3.4s |
| DC-SNAPSHOT | FAIL | 3.6s |
| DC-VERSION | FAIL | 3.2s |
| DC-CONSUMER | PASS | 3.2s |
| DC-CONSUMER-LIST | PASS | 2.9s |
| DC-LIFECYCLE | PASS | 3s |
| DC-NOTIFICATIONS | PASS | 2.9s |
| QM-COVERAGE | PASS | 3.5s |
| QM-RECORD | PASS | 3.3s |
| QM-ANOMALY | PASS | 3.6s |
| QM-DRIFT | PASS | 3s |
| QM-FRESHNESS | PASS | 3s |
| QM-FRESHNESS-CHECK | PASS | 2.9s |
| QM-SCORECARD | FAIL | 3.1s |
| QM-REGRESSION | PASS | 3.2s |
| OM-SLO-SET | PASS | 3.1s |
| OM-SLO-LIST | PASS | 2.9s |
| OM-SLO-CHECK | PASS | 2.9s |
| OM-DASHBOARD | PASS | 2.8s |
| AM-DEP-SCAN | PASS | 3s |
| AM-DEP-ADD | PASS | 3s |
| AM-DEP-LIST | PASS | 3s |
| AM-DEP-IMPACT | PASS | 2.8s |
| AM-DRIFT | PASS | 2.9s |
| HEALTH | PASS | 41.6s |


## Failed Steps
- **GOV-APPROVAL**: Missing: REQ-001
- **GOV-APPROVAL-LIST**: Missing: REQ-001
- **DC-SNAPSHOT**: Exit code: 2 (expected 0)
- **DC-VERSION**: Exit code: 2 (expected 0)
- **QM-SCORECARD**: Missing: Rating

