-- stg_orders: standardize raw orders from Postgres
select
    order_id,
    customer_id,
    cast(amount as numeric(18,2)) as amount,
    status,
    cast(created_at as timestamp) as created_at,
    cast(updated_at as timestamp) as updated_at
from {{ source('pipelinekit_raw', 'orders') }}
