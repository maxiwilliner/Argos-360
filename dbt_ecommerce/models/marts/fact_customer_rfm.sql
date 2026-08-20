{{
    config(
        materialized='external',
        location='../data/03_gold/fact_customer_rfm.parquet'
    )
}}

with customer_orders as (
    select
        global_customer_id,
        count(order_id) as total_orders_placed,
        count(case when order_status = 'DELIVERED' then order_id end) as total_completed_orders,
        min(case when order_status = 'DELIVERED' then order_date end) as first_order_date,
        max(case when order_status = 'DELIVERED' then order_date end) as last_order_date,
        coalesce(
            sum(case when order_status = 'DELIVERED' then net_amount end), 0
        ) as lifetime_net_spend,
        coalesce(
            sum(case when order_status = 'DELIVERED' then gross_amount end), 0
        ) as lifetime_gross_spend,
        coalesce(
            sum(case when order_status = 'DELIVERED' then total_profit end), 0
        ) as lifetime_profit_generated,
        avg(case when order_status = 'DELIVERED' then net_amount end) as average_order_value
    from {{ ref('fact_orders') }}
    group by global_customer_id
),

rfm_metrics as (
    select
        c.global_customer_id,
        c.total_orders_placed,
        c.total_completed_orders,
        c.first_order_date,
        c.last_order_date,
        c.lifetime_net_spend,
        c.lifetime_gross_spend,
        c.lifetime_profit_generated,
        round(coalesce(c.average_order_value, 0), 2) as average_order_value,
        datediff('day', c.last_order_date, cast('2026-07-01' as date)) as recency_days
    from customer_orders as c
),

rfm_scores as (
    select
        *,
        ntile(5) over (order by recency_days desc) as r_score,
        ntile(5) over (order by total_completed_orders asc) as f_score,
        ntile(5) over (order by lifetime_net_spend asc) as m_score
    from rfm_metrics
    where total_completed_orders > 0
)

select
    global_customer_id,
    total_orders_placed,
    total_completed_orders,
    first_order_date,
    last_order_date,
    recency_days,
    lifetime_net_spend,
    lifetime_gross_spend,
    lifetime_profit_generated,
    average_order_value,
    r_score,
    f_score,
    m_score,
    r_score || f_score || m_score as rfm_cell,
    case
        when r_score >= 4 and f_score >= 4 and m_score >= 4 then 'Champions'
        when f_score >= 3 and m_score >= 3 then 'Loyal Customers'
        when r_score >= 4 and f_score between 2 and 3 then 'Potential Loyalists'
        when r_score >= 4 and f_score = 1 then 'Recent New Customers'
        when r_score <= 2 and f_score >= 3 then 'At Risk Customers'
        when r_score <= 2 and f_score <= 2 then 'Lost / Hibernating'
        else 'Standard Customers'
    end as customer_rfm_segment
from rfm_scores
