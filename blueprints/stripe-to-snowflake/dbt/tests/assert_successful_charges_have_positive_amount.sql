-- assert_successful_charges_have_positive_amount.sql
-- Quality check: succeeded charges must have amount > 0.
-- A zero-amount succeeded charge is anomalous and likely a pipeline issue.
-- Returns rows that FAIL the assertion (dbt convention: 0 rows = pass).

select
    charge_id,
    amount,
    currency,
    status
from {{ ref('fct_charges') }}
where status = 'succeeded'
  and amount <= 0
