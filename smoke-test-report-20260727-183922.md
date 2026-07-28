# PipelineKit Smoke Test Report
Date: 2026-07-27 18:39:22
Blueprint: stripe-to-snowflake
Result: 30/36 passed in 172.6s

## Step Results
| Step | Status | Time |
|------|--------|------|
| EMS-LIST | PASS | 3s |
| EMS-DC | PASS | 2.9s |
| EMS-QM | PASS | 2.9s |
| BP-LIST | PASS | 3.1s |
| BP-BEST | PASS | 3.1s |
| BP-ALL | PASS | 3.2s |
| GOV-OWNER-SET | PASS | 3.2s |
| GOV-OWNER-LIST | PASS | 3.9s |
| GOV-CONV-ADD | PASS | 3.5s |
| GOV-CONV-CHECK | PASS | 3.4s |
| GOV-APPROVAL | FAIL | 3.3s |
| GOV-APPROVAL-LIST | FAIL | 2.9s |
| DC-SNAPSHOT | FAIL | 2.9s |
| DC-VERSION | FAIL | 3.1s |
| DC-CONSUMER | PASS | 3.1s |
| DC-CONSUMER-LIST | PASS | 3s |
| DC-LIFECYCLE | PASS | 3.3s |
| DC-NOTIFICATIONS | PASS | 3s |
| QM-COVERAGE | PASS | 3.4s |
| QM-RECORD | PASS | 3.4s |
| QM-ANOMALY | FAIL | 3.5s |
| QM-DRIFT | PASS | 3s |
| QM-FRESHNESS | PASS | 3s |
| QM-FRESHNESS-CHECK | PASS | 3s |
| QM-SCORECARD | FAIL | 3.2s |
| QM-REGRESSION | PASS | 3.2s |
| OM-SLO-SET | PASS | 2.9s |
| OM-SLO-LIST | PASS | 2.9s |
| OM-SLO-CHECK | PASS | 3.2s |
| OM-DASHBOARD | PASS | 4.4s |
| AM-DEP-SCAN | PASS | 4s |
| AM-DEP-ADD | PASS | 4.4s |
| AM-DEP-LIST | PASS | 4.3s |
| AM-DEP-IMPACT | PASS | 4.3s |
| AM-DRIFT | PASS | 5.2s |
| HEALTH | PASS | 54.5s |


## Failed Steps
- **GOV-APPROVAL**: Missing: REQ-001
- **GOV-APPROVAL-LIST**: Missing: REQ-001
- **DC-SNAPSHOT**: Exit code: 2 (expected 0)
- **DC-VERSION**: Exit code: 2 (expected 0)
- **QM-ANOMALY**: Missing: ESTABLISHING
- **QM-SCORECARD**: Missing: Rating

