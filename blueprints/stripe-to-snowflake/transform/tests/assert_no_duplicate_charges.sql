-- assert_no_duplicate_charges.sql
-- Quality check: charge_id must be unique in the fact table.
-- Duplicates would double-count revenue metrics.
-- Returns rows that FAIL the assertion (dbt convention: 0 rows = pass).

select
    charge_id,
    count(*) as row_count
from {{ ref('fct_charges') }}
group by charge_id
having count(*) > 1
