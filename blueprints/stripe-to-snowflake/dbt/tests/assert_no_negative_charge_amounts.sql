-- assert_no_negative_charge_amounts.sql
-- Quality check: all charge amounts must be non-negative.
-- Stripe refunds are separate objects; negative amounts indicate a data issue.
-- This test returns rows that FAIL the assertion (dbt convention: 0 rows = pass).

select
    charge_id,
    amount,
    currency,
    status
from {{ ref('fct_charges') }}
where amount < 0
