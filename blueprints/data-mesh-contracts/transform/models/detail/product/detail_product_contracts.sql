{{
  config(
    materialized='view',
    schema='detail_product'
  )
}}

-- Product Detail Table
-- Columns Product can authoritatively provide about contracts.
-- Owned by: Product domain

with frame as (
    select contract_id from {{ ref('frame_contracts') }}
),
product_data as (
    select * from {{ source('pipelinekit_pipeline_raw', 'product_contract_data') }}
),
joined as (
    select
        frame.contract_id,
        product_data.active_users,
        product_data.licensed_users,
        product_data.licenses_purchased,
        product_data.last_active_at
    from frame
    left join product_data using (contract_id)
)
select * from joined
