-- fct_opportunities: trusted analytics-ready opportunities fact table
with opportunities as (
    select * from {{ ref('stg_opportunities') }}
),
accounts as (
    select * from {{ ref('stg_accounts') }}
),
final as (
    select
        o.opportunity_id,
        o.opportunity_name,
        o.account_id,
        a.account_name,
        a.industry,
        o.amount,
        o.stage_name,
        o.close_date,
        o.probability,
        o.is_won,
        o.is_closed,
        o.created_date
    from opportunities o
    left join accounts a on o.account_id = a.account_id
)
select * from final
