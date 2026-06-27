# stripe-to-snowflake Runbook

## On-Call Reference — Stripe to Snowflake Pipeline

---

## Alert: `ingestion_failure`

**Severity**: Critical  
**Description**: The dlt ingestion pipeline failed or produced failed jobs.

**Triage Steps**:
1. Check ingestion logs: `python ingestion/pipeline.py` output or your orchestrator logs.
2. Verify Stripe API key is valid and not rate-limited:
bash
   curl https://api.stripe.com/v1/charges?limit=1 -u ${STRIPE_API_KEY}:

3. Verify Snowflake connectivity and credentials are valid.
4. Check for Stripe API incidents at https://status.stripe.com/
5. Review dlt pipeline state — a corrupt state file may require resetting:
bash
   # Remove dlt pipeline state to force full reload (use with caution)
   dlt pipeline stripe_to_snowflake drop

6. Re-run the pipeline manually after resolving the root cause.

---

## Alert: `freshness_breach_charges` / `freshness_breach_customers`

**Severity**: Critical (charges) / Warning (customers)  
**Description**: Table has not been updated within 6 hours.

**Triage Steps**:
1. Check if the scheduled pipeline run executed. Look for orchestrator job failures.
2. Check last load timestamp in Snowflake:
sql
   SELECT MAX(_dlt_load_id), MAX(created_at)
   FROM <DBT_SOURCE_DATABASE>.<DBT_SOURCE_SCHEMA>.charges;

3. If no recent runs: manually trigger the pipeline.
4. If runs are executing but data is stale: check Stripe API for data delays.
5. Escalate if freshness breach exceeds 12 hours.

---

## Alert: `quality_check_failure`

**Severity**: Critical  
**Description**: One or more dbt data quality tests failed.

**Triage Steps**:
1. Identify failing test:
bash
   cd dbt && dbt test --select tag:stripe 2>&1 | grep FAIL

2. For `assert_no_duplicate_charges`:
   - Check if dlt write_disposition is correctly set to `merge`.
   - Inspect duplicates: `SELECT charge_id, COUNT(*) FROM fct_charges GROUP BY 1 HAVING COUNT(*) > 1`
   - Root cause is typically a failed merge or a primary key misconfiguration in dlt.
3. For `assert_no_negative_charge_amounts`:
   - Inspect negative rows: `SELECT * FROM fct_charges WHERE amount < 0`
   - Determine if source data from Stripe actually contains negative values (escalate to data owner).
4. For `assert_successful_charges_have_positive_amount`:
   - Check for $0 trial authorizations — these may be expected. Consult the data owner.
   - If expected, update the test to exclude known zero-amount charge categories.
5. Do NOT suppress test failures without root cause analysis.

---

## Alert: `zero_charges_loaded`

**Severity**: Warning  
**Description**: No charges were loaded in the last pipeline run.

**Triage Steps**:
1. Check Stripe API connectivity (see `ingestion_failure` steps above).
2. Verify the Stripe account has charge activity. This may be expected during off-hours for low-volume accounts.
3. Check dlt incremental state — the cursor may be pointing beyond available data:
bash
   dlt pipeline stripe_to_snowflake info

4. If this occurs repeatedly during business hours, escalate.

---

## Manual Pipeline Execution

bash
# Run ingestion only
python stripe-to-snowflake/ingestion/pipeline.py

# Run dbt staging models only
cd stripe-to-snowflake/dbt && dbt run --select tag:staging

# Run all dbt models
cd stripe-to-snowflake/dbt && dbt run

# Run all dbt tests
cd stripe-to-snowflake/dbt && dbt test

# Full pipeline run
python stripe-to-snowflake/ingestion/pipeline.py && \
  cd stripe-to-snowflake/dbt && dbt run && dbt test


## Escalation

| Condition | Escalate To |
|---|---|
| Stripe API outage (confirmed at status.stripe.com) | Engineering Lead |
| Data quality failures persisting > 2 hours | Data Engineering On-Call |
| Freshness breach > 12 hours during business hours | Data Engineering On-Call + Stakeholders |
| Revenue data discrepancy reported by Finance | Data Engineering Lead + Finance |
