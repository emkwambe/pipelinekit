-- stg_stripe__customers.sql
-- Staging model for Stripe customers.
-- Casts types and normalizes nulls.

with source as (

    select * from {{ source('stripe_raw', 'customers') }}

),

renamed as (

    select
        -- identifiers
        id                                          as customer_id,
        default_source                              as default_payment_source_id,

        -- contact details
        lower(trim(email))                          as email,
        trim(name)                                  as name,

        -- preferences
        upper(trim(currency))                       as preferred_currency,

        -- descriptive
        description,

        -- timestamps
        -- Stripe returns Unix epoch integers; convert to TIMESTAMP_NTZ
        to_timestamp_ntz(created)                   as created_at,

        -- dlt metadata
        _dlt_load_id,
        _dlt_id

    from source

)

select * from renamed
