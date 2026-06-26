-- assert_no_duplicate_customers.sql
-- Quality check: customer_id must be unique in the dimension table.
-- Returns rows that FAIL the assertion (dbt convention: 0 rows = pass).

select
    customer_id,
    count(*) as row_count
from {{ ref('dim_customers') }}
group by customer_id
having count(*) > 1
