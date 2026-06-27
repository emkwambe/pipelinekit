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
        -- Stripe returns Unix epoch integers; the cross-db macro emits the
        -- correct per-target timestamp conversion (see macros/cross_db.sql).
        {{ to_timestamp('created') }}               as created_at

    from source

)

select * from renamed
