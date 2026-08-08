{{
  config(
    materialized='view',
    schema='frame'
  )
}}

-- Frame Table: one row per contract_id
-- This is the shared backbone for all downstream Detail tables.
-- Owned by: Engineering domain
-- Every Detail table LEFT JOINs to this using contract_id.

with source as (
    select * from {{ source('pipelinekit_pipeline_raw', 'contracts') }}
),
frame as (
    select
        contract_id,
        status,
        type,
        created_at,
        _loaded_at
    from source
    where contract_id is not null
)
select * from frame
