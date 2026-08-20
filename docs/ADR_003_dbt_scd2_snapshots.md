# ADR 003: Gestión de Historial (SCD Tipo 2) mediante dbt Snapshots

## Estado
**Aceptado**

## Contexto
Los atributos de los clientes cambian a lo largo del tiempo (cambios de domicilio, ciudad o teléfono). Si sobreescribimos la fila del cliente (SCD Tipo 1), las ventas históricas se atribuirían erróneamente a la nueva ciudad, distorsionando los reportes geográficos.

## Decisión
Utilizamos la funcionalidad nativa de **dbt Snapshots** (`snapshots/snp_customers.sql`) con estrategia `check` para versionar automáticamente la dimensión de clientes (`dim_customers`):
* dbt gestiona automáticamente las columnas de auditoría `dbt_valid_from`, `dbt_valid_to`, `dbt_scd_id` y el estado del registro activo.

## Consecuencias
### Positivas:
* Cumplimiento estricto del estándar de la industria en Analytics Engineering sin código SQL manual propenso a errores.
* Capacidad de realizar análisis precisos de ventas en el momento exacto en que ocurrieron (*Point-in-time analysis*).

### Negativas:
* Incremento en el volumen de filas de la dimensión de clientes al mantener todas las versiones históricas.
