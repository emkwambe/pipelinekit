-- stg_stripe__charges.sql
-- Staging model for Stripe charges.
-- Casts types, normalizes nulls, and converts amount from cents to decimal.

with source as (

    select * from {{ source('stripe_raw', 'charges') }}

),

renamed as (

    select
        -- identifiers
        id                                          as charge_id,
        customer                                    as customer_id,

        -- amounts
        amount                                      as amount_cents,
        round(amount / 100.0, 2)                    as amount,
        upper(trim(currency))                       as currency,

        -- status
        lower(trim(status))                         as status,
        {{ safe_boolean('refunded') }}              as is_refunded,

        -- descriptive
        description,

        -- timestamps
        -- Stripe returns Unix epoch integers; convert via the cross-db macro
        -- (Snowflake to_timestamp_ntz / DuckDB to_timestamp / BigQuery TIMESTAMP_SECONDS).
        {{ to_timestamp('created') }}               as created_at

    from source

)

select * from renamed
