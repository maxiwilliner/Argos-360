{{
    config(
        materialized='external',
        location='../data/02_silver/stg_products.parquet'
    )
}}

with source as (
    select * from read_parquet('../data/01_raw/raw_products.parquet')
)

select
    cast(product_id as varchar) as product_id,
    cast(product_name as varchar) as product_name,
    cast(category as varchar) as category,
    cast(subcategory as varchar) as subcategory,
    cast(unit_cost as decimal(10, 2)) as unit_cost,
    cast(unit_price as decimal(10, 2)) as unit_price,
    cast(unit_price - unit_cost as decimal(10, 2)) as unit_margin,
    cast(
        round((unit_price - unit_cost) / nullif(unit_price, 0) * 100, 2) as decimal(5, 2)
    ) as profit_margin_pct,
    cast(created_at as timestamp) as created_at
from source
