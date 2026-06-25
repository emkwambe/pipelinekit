-- fct_orders: trusted analytics-ready orders fact table
select
    order_id,
    customer_id,
    amount,
    status,
    created_at,
    updated_at,
    date_trunc('day', created_at) as order_date
from {{ ref('stg_orders') }}
where status != 'cancelled'
