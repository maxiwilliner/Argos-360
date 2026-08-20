# ADR 002: Master Data Management mediante Entity Resolution Probabilístico

## Estado
**Aceptado**

## Contexto
En ecosistemas omnicanal, los clientes interactúan a través de múltiples puntos de contacto (tienda Shopify, CRM Salesforce, listas de marketing). Esto genera identidades fragmentadas, errores tipográficos en nombres, variaciones en correos y números de teléfono sin estandarizar. Un `JOIN` relacional exacto sobre el email falla en más del 25% de los casos.

## Decisión
Implementamos un motor de **Entity Resolution / MDM** que combina:
1. **Reglas de Bloqueo Determinístico:** Matching exacto sobre correos y teléfonos normalizados.
2. **Matching Probabilístico Difuso (Fuzzy Matching):** Algoritmos de similitud de texto (Levenshtein y Jaro-Winkler via RapidFuzz / metodología Splink) para nombres y ubicaciones con similitud $\ge 88\%$.
3. **Clusterización con Disjoint-Set (Union-Find):** Agrupación en componentes conexos para asignar un `global_customer_id` único (Golden Record).
4. **Reglas de Supervivencia (Survivorship):** Selección de los atributos más recientes y completos para el perfil 360.

## Consecuencias
### Positivas:
* Generación de una **Fuente Única de Verdad (SSOT)** que elimina clientes duplicados y métricas de LTV distorsionadas.
* Permite trazabilidad y linaje bidireccional desde los registros de origen hasta el Golden Record.

### Negativas:
* Complejidad algorítmica adicional que requiere una fase de procesamiento previa a los modelos de dbt.
