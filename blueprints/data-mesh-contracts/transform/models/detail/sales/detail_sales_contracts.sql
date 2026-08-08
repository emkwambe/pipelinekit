{{
  config(
    materialized='view',
    schema='detail_sales'
  )
}}

-- Sales Detail Table
-- Columns Sales can authoritatively provide about contracts.
-- Owned by: Sales domain

with frame as (
    select contract_id from {{ ref('frame_contracts') }}
),
sales_data as (
    select * from {{ source('pipelinekit_pipeline_raw', 'sales_contract_data') }}
),
joined as (
    select
        frame.contract_id,
        sales_data.employee_owners,
        sales_data.opportunity_value,
        sales_data.account_tier
    from frame
    left join sales_data using (contract_id)
)
select * from joined
