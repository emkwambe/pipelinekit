-- stg_accounts: standardize raw Salesforce accounts
with source as (
    select * from {{ source('salesforce_raw', 'accounts') }}
),
renamed as (
    select
        id as account_id,
        name as account_name,
        industry,
        annual_revenue,
        number_of_employees,
        billing_city,
        billing_country,
        created_date,
        last_modified_date
    from source
)
select * from renamed
