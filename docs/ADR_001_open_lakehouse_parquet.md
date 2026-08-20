# ADR 001: Adopción del Patrón Open Data Lakehouse con DuckDB y Parquet

## Estado
**Aceptado**

## Contexto
En arquitecturas de datos tradicionales, las empresas se veían obligadas a elegir entre:
1. Data Lakes basados en almacenamiento de objetos (baratos y flexibles, pero lentos para analítica relacional sin soporte ACID).
2. Data Warehouses propietarios (rápidos para SQL y BI, pero costosos y con formatos cerrados).

Para el proyecto **ARGOS-360**, requeríamos una arquitectura analítica de alto rendimiento, reproducible localmente sin costes de infraestructura en la nube y capaz de procesar millones de transacciones.

## Decisión
Implementamos un **Open Data Lakehouse** utilizando **DuckDB** como motor de procesamiento analítico en memoria y **Apache Parquet** como formato abierto de almacenamiento físico para todas las capas (Bronce, Plata y Oro):
* `materialized='external'` en dbt garantiza que cada modelo persista como un archivo `.parquet` independiente en disco.

## Consecuencias
### Positivas:
* **Cero bloqueo de proveedor (No Vendor Lock-in):** Los archivos Parquet pueden ser consumidos directamente por PySpark, Polars, Pandas o cargados a S3/BigQuery/Snowflake.
* **Rendimiento extremo:** Almacenamiento columnar con compresión Snappy/ZSTD y poda de metadatos (*filter pushdown*).
* **Coste $0:** Se ejecuta al 100% en local sin necesidad de aprovisionar infraestructura cloud.

### Negativas:
* Requiere gestión explícita de rutas de archivos en las configuraciones de dbt.
