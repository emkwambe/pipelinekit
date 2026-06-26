-- stg_contacts: standardize raw Salesforce contacts
with source as (
    select * from {{ source('salesforce_raw', 'contacts') }}
),
renamed as (
    select
        id as contact_id,
        account_id,
        first_name,
        last_name,
        email,
        title,
        department,
        created_date
    from source
)
select * from renamed
