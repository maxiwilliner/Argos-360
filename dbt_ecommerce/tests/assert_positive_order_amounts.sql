-- Test singular personalizado: Verifica que ningún pedido entregado tenga un importe neto <= 0
select
    order_id,
    net_amount
from {{ ref('fact_orders') }}
where order_status = 'DELIVERED'
  and net_amount <= 0
