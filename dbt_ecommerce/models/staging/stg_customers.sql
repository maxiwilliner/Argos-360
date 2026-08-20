{{
    config(
        materialized='external',
        location='../data/02_silver/stg_customers.parquet'
    )
}}

with source as (
    select * from read_parquet('../data/02_silver/stg_customers_golden.parquet')
)

select
    cast(source_record_id as varchar) as source_record_id,
    cast(source_system as varchar) as source_system,
    cast(global_customer_id as varchar) as global_customer_id,
    cast(first_name as varchar) as first_name,
    cast(last_name as varchar) as last_name,
    cast(first_name || ' ' || last_name as varchar) as full_name,
    cast(email as varchar) as email,
    cast(phone as varchar) as phone,
    cast(street_address as varchar) as street_address,
    cast(city as varchar) as city,
    cast(state as varchar) as state,
    cast(country as varchar) as country,
    cast(updated_at as timestamp) as updated_at,
    cast(mdm_cluster_size as integer) as mdm_cluster_size,
    cast(is_golden_record_source as boolean) as is_golden_record_source
from source
