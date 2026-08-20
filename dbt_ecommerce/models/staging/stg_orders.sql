{{
    config(
        materialized='external',
        location='../data/02_silver/stg_orders.parquet'
    )
}}

with source as (
    select * from read_parquet('../data/01_raw/raw_orders.parquet')
),

customers_map as (
    select distinct
        source_record_id,
        global_customer_id
    from read_parquet('../data/02_silver/stg_customers_golden.parquet')
)

select
    cast(s.order_id as varchar) as order_id,
    cast(s.source_customer_id as varchar) as source_customer_id,
    cast(c.global_customer_id as varchar) as global_customer_id,
    cast(s.product_id as varchar) as product_id,
    cast(s.order_timestamp as timestamp) as order_timestamp,
    cast(s.order_timestamp as date) as order_date,
    cast(s.order_status as varchar) as order_status,
    cast(s.quantity as integer) as quantity,
    cast(s.unit_price as decimal(10, 2)) as unit_price,
    cast(s.unit_cost as decimal(10, 2)) as unit_cost,
    cast(s.discount_rate as decimal(4, 2)) as discount_rate,
    cast(s.gross_amount as decimal(10, 2)) as gross_amount,
    cast(s.net_amount as decimal(10, 2)) as net_amount,
    cast(s.shipping_cost as decimal(10, 2)) as shipping_cost,
    cast((s.net_amount - (s.unit_cost * s.quantity)) as decimal(10, 2)) as total_profit,
    cast(s.delivered_timestamp as timestamp) as delivered_timestamp,
    case
        when s.delivered_timestamp is not null
            then datediff(
                'day', cast(s.order_timestamp as date), cast(s.delivered_timestamp as date)
            )
    end as delivery_days
from source as s
left join customers_map as c on s.source_customer_id = c.source_record_id
