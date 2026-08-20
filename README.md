# ARGOS-360: E-Commerce Customer 360 & Operations Lakehouse

[![CI/CD DataOps](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?style=flat&logo=githubactions&logoColor=white)](.github/workflows/ci.yml)
[![DuckDB](https://img.shields.io/badge/Engine-DuckDB-FFF000?style=flat&logo=duckdb&logoColor=black)](https://duckdb.org/)
[![dbt](https://img.shields.io/badge/Transform-dbt--core-FF694B?style=flat&logo=dbt&logoColor=white)](https://www.getdbt.com/)
[![Storage](https://img.shields.io/badge/Storage-Apache%20Parquet-00D2B8?style=flat)](https://parquet.apache.org/)
[![BI App](https://img.shields.io/badge/BI%20App-Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)](app/dashboard.py)
[![SQLFluff](https://img.shields.io/badge/Linter-SQLFluff-25c2a0?style=flat)](https://sqlfluff.com/)

> **ARGOS-360** es una plataforma analítica **End-to-End** de estándar empresarial que implementa un **Open Data Lakehouse** sobre almacenamiento abierto Parquet y DuckDB. Resuelve el problema crítico de la fragmentación de identidades de clientes mediante **Master Data Management (MDM) y Entity Resolution probabilístico**, modela los datos bajo la metodología **Kimball (Esquema de Estrella + SCD Tipo 2)** y ofrece un cuadro de mando ejecutivo interactivo para la toma de decisiones estratégicas.

---

## Arquitectura End-to-End

```mermaid
flowchart TD
    subgraph S1 [1. Ingesta & Generación]
        A1[Simulador Python / Faker] -->|Datos Crudos Desordenados| B1[(data/01_raw/*.parquet)]
    end

    subgraph S2 [2. MDM & Entity Resolution]
        B1 -->|Deduplicación Difusa & Blocking| C1[RapidFuzz / Splink Engine]
        C1 -->|Golden Record Asignado| C2[(data/02_silver/stg_customers_golden.parquet)]
    end

    subgraph S3 [3. Transformación dbt & Lakehouse Parquet]
        B1 & C2 -->|dbt Staging Models| D1[(data/02_silver/*.parquet)]
        D1 -->|dbt Snapshots / SCD Tipo 2| D2[(snapshots/snp_customers)]
        D1 & D2 -->|dbt Marts / Kimball Models| E1[(data/03_gold/fact_orders.parquet)]
        D1 & D2 -->|dbt Marts / Kimball Models| E2[(data/03_gold/fact_customer_rfm.parquet)]
        D1 & D2 -->|dbt Marts / Kimball Models| E3[(data/03_gold/dim_customers.parquet)]
        D1 & D2 -->|dbt Marts / Kimball Models| E4[(data/03_gold/dim_products.parquet)]
    end

    subgraph S4 [4. DataOps & Calidad]
        F1[SQLFluff Linter] --> G1[GitHub Actions CI/CD]
        F2[dbt tests & assertions] --> G1
    end

    subgraph S5 [5. Consumo & Reporting]
        E1 & E2 & E3 & E4 -->|Motor SQL DuckDB| H1[App Streamlit / Customer 360 Dashboard]
    end
```

---

## Características Técnicas Destacadas

### 1. Master Data Management (MDM) & Customer 360
* **Problema:** Múltiples fuentes (Shopify, Salesforce, HubSpot) generan identidades duplicadas por erratas tipográficas y variaciones de email.
* **Solución:** Motor de resolución de entidades con **reglas de bloqueo determinístico y matching probabilístico difuso** ($\ge 88\%$ similitud Levenshtein/Jaro-Winkler) agrupado mediante componentes conexos (*Disjoint-Set Union-Find*).
* **Resultado:** Creación de un **Golden Record** con `global_customer_id` único y trazabilidad completa hacia los registros de origen.

### 2. Open Data Lakehouse con Parquet Físico
* Todos los modelos de dbt utilizan la directiva `materialized='external'`, garantizando que las capas **Bronce (`01_raw`)**, **Plata (`02_silver`)** y **Oro (`03_gold`)** persistan físicamente como archivos `.parquet` abiertos en disco, eliminando cualquier dependencia propietaria.

### 3. Versionado Histórico (SCD Tipo 2) con dbt Snapshots
* Implementación nativa de **Slowly Changing Dimensions (SCD Tipo 2)** en `snapshots/snp_customers.sql` para rastrear cambios en domicilios y atributos de clientes sin alterar el histórico de ventas.

### 4. Modelado Dimensional Kimball & Segmentación RFM
* **`fact_orders`:** Hechos transaccionales con cálculo de márgenes netos, descuentos y tiempos de entrega.
* **`fact_customer_rfm`:** Motor de segmentación conductual **RFM (Recency, Frequency, Monetary)** clasificando a los clientes en *Champions, Loyal, Potential Loyalists, At Risk y Lost*.
* **`dim_customers`**, **`dim_products`**, **`dim_date`:** Dimensiones enriquecidas con jerarquías y categorías.

### 5. DataOps, Calidad y CI/CD
* Pipeline automatizado en **GitHub Actions (`.github/workflows/ci.yml`)** que ejecuta el linter de SQL (**SQLFluff**) y valida el 100% de los tests de calidad (**`dbt test`**) en cada *Pull Request*.

---

## Guía de Inicio Rápido (1 Comando)

### Prerrequisitos
* Python 3.10 o superior.

### 1. Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/argos-360.git
cd argos-360
```

### 2. Instalar Dependencias
```bash
make install
# O manualmente: pip install -r requirements.txt
```

### 3. Ejecutar la Pipeline Completa End-to-End
```bash
make pipeline
# O multiplataforma: python run_pipeline.py
```
> Este comando ejecuta la generación sintética, el motor de MDM, los snapshots de dbt, la compilación de la Capa Oro en Parquet y la batería de tests de calidad.

### 4. Lanzar el Dashboard Interactivo
```bash
make dashboard
# O directamente: streamlit run app/dashboard.py
```

---

## Estructura del Repositorio

```text
argos-360/
├── .github/workflows/ci.yml            # CI/CD: SQLFluff + dbt test
├── app/dashboard.py                    # Dashboard interactivo Streamlit
├── data/                               # Almacenamiento físico del Lakehouse
│   ├── 01_raw/*.parquet                # Capa Bronce
│   ├── 02_silver/*.parquet             # Capa Plata (Splink MDM & Staging)
│   └── 03_gold/*.parquet               # Capa Oro (Kimball Star Schema)
├── dbt_ecommerce/                      # Proyecto dbt
│   ├── dbt_project.yml                 # Configuración de dbt
│   ├── profiles.yml                    # Conexión DuckDB
│   ├── snapshots/snp_customers.sql     # SCD Tipo 2 dbt Snapshot
│   ├── models/
│   │   ├── staging/*.sql               # Modelos de limpieza Plata
│   │   └── marts/*.sql                 # Modelos Dimensionales Oro
│   └── tests/*.sql                     # Pruebas de aserción de calidad
├── docs/                               # Architecture Decision Records (ADRs)
│   ├── ADR_001_open_lakehouse_parquet.md
│   ├── ADR_002_splink_entity_resolution.md
│   └── ADR_003_dbt_scd2_snapshots.md
├── src/
│   ├── generator/generate_raw_data.py  # Generador de datos sintéticos
│   └── mdm/entity_resolution.py        # Motor de deduplicación y Golden Record
├── .sqlfluff                           # Configuración del linter SQL
├── Makefile                            # Orquestación con make
├── run_pipeline.py                     # Orquestación multiplataforma en Python
└── requirements.txt                    # Dependencias del proyecto
```
