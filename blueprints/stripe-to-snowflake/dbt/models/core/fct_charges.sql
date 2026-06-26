-- fct_charges.sql
-- Fact table for Stripe charges.
-- Grain: one row per charge.
-- Powers: Daily Revenue, Charge Volume, Refund Rate, Average Charge Value KPIs.

with charges as (

    select * from {{ ref('stg_stripe__charges') }}

),

customers as (

    select * from {{ ref('stg_stripe__customers') }}

),

final as (

    select
        -- keys
        ch.charge_id,
        ch.customer_id,

        -- customer context
        c.email                                         as customer_email,
        c.name                                          as customer_name,
        c.created_at                                    as customer_created_at,

        -- charge details
        ch.amount_cents,
        ch.amount,
        ch.currency,
        ch.status,
        ch.is_refunded,
        ch.description,
        ch.created_at                                   as charge_created_at,

        -- derived date fields for analytics
        date_trunc('day',  ch.created_at)               as charge_date,
        date_trunc('month', ch.created_at)              as charge_month,

        -- KPI helper flags
        case when ch.status = 'succeeded' then 1 else 0 end  as is_successful,
        case when ch.is_refunded = true   then 1 else 0 end  as is_refund,

        -- KPI helper amounts (only count successful charges)
        case
            when ch.status = 'succeeded' then ch.amount
            else 0
        end                                             as successful_amount,

        -- metadata
        ch._dlt_load_id,
        ch._dlt_id

    from charges ch
    left join customers c
        on ch.customer_id = c.customer_id

)

select * from final
