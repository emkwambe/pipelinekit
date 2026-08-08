{{
  config(
    materialized='table',
    schema='core'
  )
}}

-- Core Contracts: joined wide table from all Detail tables
-- Simple LEFT JOINs — all tables share the same Frame key (contract_id)
-- This is the table analytics consumers query
-- No domain owns columns here exclusively — each Detail table is authoritative

with frame as (
    select * from {{ ref('frame_contracts') }}
),
finance as (
    select * from {{ ref('detail_finance_contracts') }}
),
sales as (
    select * from {{ ref('detail_sales_contracts') }}
),
product as (
    select * from {{ ref('detail_product_contracts') }}
)
select
    -- Frame columns (Engineering domain)
    frame.contract_id,
    frame.status,
    frame.type,
    frame.created_at,

    -- Finance domain columns
    finance.renewal_date,
    finance.payment_status,
    finance.arr_value,
    finance.payment_terms,

    -- Sales domain columns
    sales.employee_owners,
    sales.opportunity_value,
    sales.account_tier,

    -- Product domain columns
    product.active_users,
    product.licensed_users,
    product.licenses_purchased,
    product.last_active_at

from frame
left join finance using (contract_id)
left join sales using (contract_id)
left join product using (contract_id)
