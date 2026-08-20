{{
    config(
        materialized='external',
        location='../data/03_gold/dim_products.parquet'
    )
}}

with stg as (
    select * from {{ ref('stg_products') }}
)

select
    product_id,
    product_name,
    category,
    subcategory,
    unit_cost,
    unit_price,
    unit_margin,
    profit_margin_pct,
    case
        when unit_price >= 200 then 'Premium ($200+)'
        when unit_price >= 80 then 'Mid-Range ($80-$200)'
        else 'Budget (<$80)'
    end as price_tier,
    created_at
from stg
