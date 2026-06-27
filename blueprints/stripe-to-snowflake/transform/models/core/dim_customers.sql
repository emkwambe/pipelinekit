-- dim_customers.sql
-- Dimension table for Stripe customers.
-- Grain: one row per customer.
-- Powers: New Customers, Customer Lifetime Value KPIs.

with customers as (

    select * from {{ ref('stg_stripe__customers') }}

),

charge_summary as (

    select
        customer_id,
        count(*)
            filter (where status = 'succeeded')         as total_successful_charges,
        sum(amount)
            filter (where status = 'succeeded')         as lifetime_value,
        min(created_at)                                 as first_charge_at,
        max(created_at)                                 as last_charge_at
    from {{ ref('stg_stripe__charges') }}
    group by customer_id

),

final as (

    select
        -- keys
        c.customer_id,

        -- contact details
        c.email,
        c.name,
        c.preferred_currency,
        c.default_payment_source_id,
        c.description,

        -- timestamps
        c.created_at                                    as customer_created_at,
        date_trunc('day',  c.created_at)                as customer_created_date,
        date_trunc('month', c.created_at)               as customer_created_month,

        -- lifetime value metrics (may be null for customers with no charges)
        coalesce(cs.total_successful_charges, 0)        as total_successful_charges,
        coalesce(cs.lifetime_value, 0.00)               as lifetime_value,
        cs.first_charge_at,
        cs.last_charge_at,

        -- metadata
        c._dlt_load_id,
        c._dlt_id

    from customers c
    left join charge_summary cs
        on c.customer_id = cs.customer_id

)

select * from final
