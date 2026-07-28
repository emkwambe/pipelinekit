with source as (
    select * from "practice-run"."pipelinekit_pipeline_raw"."orders"
),
staged as (
    select
        order_id,
        customer_id,
        status,
        amount,
        created_at,
        _loaded_at
    from source
)
select * from staged