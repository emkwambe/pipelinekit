-- stg_opportunities: standardize raw Salesforce opportunities
with source as (
    select * from {{ source('salesforce_raw', 'opportunities') }}
),
renamed as (
    select
        id as opportunity_id,
        account_id,
        name as opportunity_name,
        amount,
        stage_name,
        close_date,
        probability,
        is_won,
        is_closed,
        created_date,
        last_modified_date
    from source
)
select * from renamed
