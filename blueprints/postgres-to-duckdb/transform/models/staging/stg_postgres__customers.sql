-- Staged customers from PostgreSQL. One row per customer.
with source as (
    select * from {{ source('postgres_raw', 'customers') }}
)

select
    customer_id,
    email,
    created_at
from source
