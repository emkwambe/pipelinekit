
  
  create view "practice-run"."pipelinekit_transformed"."stg_postgres__customers__dbt_tmp" as (
    with source as (
    select * from "practice-run"."pipelinekit_pipeline_raw"."customers"
),
staged as (
    select
        customer_id,
        email,
        created_at,
        _loaded_at
    from source
)
select * from staged
  );
