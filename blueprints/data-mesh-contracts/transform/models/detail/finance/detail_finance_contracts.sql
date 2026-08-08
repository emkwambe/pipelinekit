{{
  config(
    materialized='view',
    schema='detail_finance'
  )
}}

-- Finance Detail Table
-- Columns Finance can authoritatively provide about contracts.
-- Owned by: Finance domain
-- GM-4 column ownership declared in schema.yml

with frame as (
    select contract_id from {{ ref('frame_contracts') }}
),
finance_data as (
    select * from {{ source('pipelinekit_pipeline_raw', 'finance_contract_data') }}
),
joined as (
    select
        frame.contract_id,
        finance_data.renewal_date,
        finance_data.payment_status,
        finance_data.arr_value,
        finance_data.payment_terms
    from frame
    left join finance_data using (contract_id)
)
select * from joined
