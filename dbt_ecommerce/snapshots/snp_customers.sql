{% snapshot snp_customers %}

{{
    config(
        target_schema='main',
        unique_key='global_customer_id',
        strategy='check',
        check_cols=['street_address', 'city', 'state', 'country', 'email', 'phone']
    )
}}

with source_customers as (
    select * from read_parquet('../data/02_silver/stg_customers_golden.parquet')
),

ranked_customers as (
    select
        global_customer_id,
        first_name,
        last_name,
        first_name || ' ' || last_name as full_name,
        email,
        phone,
        street_address,
        city,
        state,
        country,
        updated_at,
        row_number() over (
            partition by global_customer_id 
            order by updated_at desc
        ) as rn
    from source_customers
)

select
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
    updated_at
from ranked_customers
where rn = 1

{% endsnapshot %}
