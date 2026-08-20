{{
    config(
        materialized='external',
        location='../data/03_gold/dim_customers.parquet'
    )
}}

with snapshot_source as (
    select * from {{ ref('snp_customers') }}
)

select
    dbt_scd_id as customer_sk,
    global_customer_id,
    first_name,
    last_name,
    full_name,
    email,
    phone,
    street_address,
    city,
    state,
    country,
    updated_at as source_last_updated_at,
    dbt_valid_from,
    coalesce(dbt_valid_to, cast('9999-12-31' as timestamp)) as dbt_valid_to,
    (dbt_valid_to is null) as is_current_record
from snapshot_source
