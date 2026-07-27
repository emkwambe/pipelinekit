-- Staged orders from PostgreSQL. One row per order.
with source as (
    select * from {{ source('postgres_raw', 'orders') }}
)

select
    order_id,
    customer_id,
    status,
    amount,
    created_at
from source
