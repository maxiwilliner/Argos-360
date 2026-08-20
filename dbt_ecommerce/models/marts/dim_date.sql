{{
    config(
        materialized='external',
        location='../data/03_gold/dim_date.parquet'
    )
}}

with date_spine as (
    select unnest(
        generate_series(
            cast('2024-01-01' as date),
            cast('2026-12-31' as date),
            interval '1 day'
        )
    ) as date_day
)

select
    cast(strftime(date_day, '%Y%m%d') as integer) as date_key,
    cast(date_day as date) as date_day,
    cast(extract('year' from date_day) as integer) as year_number,
    cast(extract('quarter' from date_day) as integer) as quarter_number,
    cast('Q' || extract('quarter' from date_day) as varchar) as quarter_name,
    cast(extract('month' from date_day) as integer) as month_number,
    cast(strftime(date_day, '%B') as varchar) as month_name,
    cast(extract('day' from date_day) as integer) as day_of_month,
    cast(extract('dayofweek' from date_day) as integer) as day_of_week,
    cast(strftime(date_day, '%A') as varchar) as day_name,
    (extract('dayofweek' from date_day) in (0, 6)) as is_weekend
from date_spine
