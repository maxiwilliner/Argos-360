{{
    config(
        materialized='external',
        location='../data/03_gold/fact_orders.parquet'
    )
}}

with orders as (
    select * from {{ ref('stg_orders') }}
),

products as (
    select * from {{ ref('dim_products') }}
)

select
    o.order_id,
    cast(strftime(o.order_date, '%Y%m%d') as integer) as order_date_key,
    o.order_date,
    o.order_timestamp,
    o.global_customer_id,
    o.product_id,
    p.category,
    p.subcategory,
    o.order_status,
    o.quantity,
    o.unit_price,
    o.unit_cost,
    o.discount_rate,
    o.gross_amount,
    o.net_amount,
    cast(o.gross_amount - o.net_amount as decimal(10, 2)) as discount_amount,
    o.shipping_cost,
    o.total_profit,
    cast(
        round(o.total_profit / nullif(o.net_amount, 0) * 100, 2) as decimal(5, 2)
    ) as net_margin_pct,
    o.delivered_timestamp,
    o.delivery_days,
    (o.order_status = 'DELIVERED') as is_completed_order
from orders as o
left join products as p on o.product_id = p.product_id
