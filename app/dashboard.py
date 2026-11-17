"""
ARGOS-360: Executive Lakehouse Dashboard & Customer 360 Explorer
Interactive BI application built with Streamlit, Plotly, and DuckDB.
Reads directly from Gold Layer Parquet files (Kimball Marts).
"""

from pathlib import Path
import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="ARGOS-360 | E-Commerce Customer 360 Lakehouse",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paths
REPO_ROOT = Path(__file__).resolve().parents[1]
GOLD_DIR = REPO_ROOT / "data" / "03_gold"
SILVER_DIR = REPO_ROOT / "data" / "02_silver"

@st.cache_data
def load_data():
    con = duckdb.connect()
    
    fact_orders_path = str(GOLD_DIR / "fact_orders.parquet")
    fact_rfm_path = str(GOLD_DIR / "fact_customer_rfm.parquet")
    dim_cust_path = str(GOLD_DIR / "dim_customers.parquet")
    dim_prod_path = str(GOLD_DIR / "dim_products.parquet")
    stg_cust_path = str(SILVER_DIR / "stg_customers_golden.parquet")
    
    orders_df = con.execute(f"SELECT * FROM read_parquet('{fact_orders_path}')").df()
    rfm_df = con.execute(f"SELECT * FROM read_parquet('{fact_rfm_path}')").df()
    cust_df = con.execute(f"SELECT * FROM read_parquet('{dim_cust_path}')").df()
    prod_df = con.execute(f"SELECT * FROM read_parquet('{dim_prod_path}')").df()
    silver_cust_df = con.execute(f"SELECT * FROM read_parquet('{stg_cust_path}')").df()
    
    return orders_df, rfm_df, cust_df, prod_df, silver_cust_df

try:
    orders, rfm, customers, products, silver_cust = load_data()
except Exception as e:
    st.error(f"⚠️ Could not load Gold Parquet tables. Make sure to run the pipeline first (`make pipeline` or `python run_pipeline.py`).\nError: {e}")
    st.stop()

# Sidebar Navigation
st.sidebar.title("🏛️ ARGOS-360")
st.sidebar.markdown("**Enterprise Lakehouse & Customer 360**")
st.sidebar.markdown("---")

view_mode = st.sidebar.radio(
    "Selecciona una vista:",
    ["📊 Executive Overview & Sales", "👥 Customer 360 & RFM Engine", "🔍 Individual Customer Profile", "🧬 MDM & Architecture Hub"]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Stack:** Python + DuckDB + dbt + Parquet + Splink + Streamlit")

# ==========================================
# 1. EXECUTIVE OVERVIEW & SALES
# ==========================================
if view_mode == "📊 Executive Overview & Sales":
    st.title("📊 Executive Dashboard & Sales Performance")
    st.markdown("Métricas consolidadas de la **Capa Oro (Kimball Marts)** sobre almacenamiento abierto Parquet.")

    # High-level KPI Cards
    total_rev = orders[orders["order_status"] == "DELIVERED"]["net_amount"].sum()
    total_profit = orders[orders["order_status"] == "DELIVERED"]["total_profit"].sum()
    total_orders = orders[orders["order_status"] == "DELIVERED"]["order_id"].nunique()
    total_customers = rfm["global_customer_id"].nunique()
    avg_order_val = total_rev / total_orders if total_orders else 0
    margin_pct = (total_profit / total_rev * 100) if total_rev else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("💰 Facturación Neta", f"${total_rev:,.2f}")
    c2.metric("📈 Beneficio Total", f"${total_profit:,.2f}", f"{margin_pct:.1f}% Margen")
    c3.metric("🛒 Pedidos Completados", f"{total_orders:,}")
    c4.metric("👥 Clientes Únicos (SSOT)", f"{total_customers:,}")
    c5.metric("🎯 Ticket Medio (AOV)", f"${avg_order_val:,.2f}")

    st.markdown("---")

    # Sales Trends & Category Breakdowns
    col_left, col_right = st.columns([6, 4])

    with col_left:
        st.subheader("📅 Evolución Mensual de Ventas y Beneficio")
        orders["year_month"] = pd.to_datetime(orders["order_date"]).dt.to_period("M").astype(str)
        monthly_sales = orders[orders["order_status"] == "DELIVERED"].groupby("year_month").agg(
            revenue=("net_amount", "sum"),
            profit=("total_profit", "sum")
        ).reset_index()

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(x=monthly_sales["year_month"], y=monthly_sales["revenue"], name="Facturación Neta", marker_color="#1E88E5"))
        fig_trend.add_trace(go.Scatter(x=monthly_sales["year_month"], y=monthly_sales["profit"], name="Beneficio Neto", mode="lines+markers", line=dict(color="#00E676", width=3)))
        fig_trend.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=30, b=20), hovermode="x unified")
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_right:
        st.subheader("🏷️ Facturación por Categoría")
        cat_sales = orders[orders["order_status"] == "DELIVERED"].groupby("category")["net_amount"].sum().reset_index()
        fig_cat = px.pie(cat_sales, values="net_amount", names="category", hole=0.45, color_discrete_sequence=px.colors.qualitative.Prism)
        fig_cat.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_cat, use_container_width=True)

# ==========================================
# 2. CUSTOMER 360 & RFM ENGINE
# ==========================================
elif view_mode == "👥 Customer 360 & RFM Engine":
    st.title("👥 Customer 360 & Segmentación RFM")
    st.markdown("Segmentación conductual automática basada en **Recencia (R), Frecuencia (F) y Valor Monetario (M)**.")

    col1, col2 = st.columns([5, 5])

    with col1:
        st.subheader("🎯 Distribución de Clientes por Segmento RFM")
        segment_counts = rfm["customer_rfm_segment"].value_counts().reset_index()
        segment_counts.columns = ["Segmento", "Total Clientes"]
        
        fig_seg = px.bar(
            segment_counts,
            x="Total Clientes",
            y="Segmento",
            orientation="h",
            color="Segmento",
            color_discrete_sequence=px.colors.qualitative.Bold,
            text="Total Clientes"
        )
        fig_seg.update_layout(template="plotly_dark", height=420, showlegend=False)
        st.plotly_chart(fig_seg, use_container_width=True)

    with col2:
        st.subheader("💎 Valor de Vida (LTV) vs Recencia")
        fig_scatter = px.scatter(
            rfm,
            x="recency_days",
            y="lifetime_net_spend",
            color="customer_rfm_segment",
            size="total_completed_orders",
            hover_data=["global_customer_id", "average_order_value"],
            labels={"recency_days": "Días desde última compra (Recency)", "lifetime_net_spend": "Gasto Total LTV ($)"},
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_scatter.update_layout(template="plotly_dark", height=420)
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.subheader("📋 Tabla de Segmentación de Clientes (Top LTV)")
    st.dataframe(
        rfm[[
            "global_customer_id", "customer_rfm_segment", "lifetime_net_spend", 
            "total_completed_orders", "average_order_value", "recency_days", "rfm_cell"
        ]].sort_values(by="lifetime_net_spend", ascending=False).head(20),
        use_container_width=True
    )

# ==========================================
# 3. INDIVIDUAL CUSTOMER PROFILE
# ==========================================
elif view_mode == "🔍 Individual Customer Profile":
    st.title("🔍 Vista 360° de Cliente Individual")
    
    # Customer Selector
    merged_cust = customers[customers["is_current_record"] == True].merge(rfm, on="global_customer_id", how="left")
    # fact_customer_rfm only contains customers with at least one DELIVERED order;
    # the rest come back from the left join with NaN metrics.
    merged_cust = merged_cust.fillna({
        "lifetime_net_spend": 0.0,
        "total_completed_orders": 0,
        "average_order_value": 0.0,
        "customer_rfm_segment": "Sin pedidos completados",
    })
    customer_list = merged_cust.apply(lambda row: f"{row['global_customer_id']} - {row['full_name']} ({row['city']})", axis=1).tolist()
    
    selected_option = st.selectbox("Busca y selecciona un cliente:", customer_list)
    selected_id = selected_option.split(" - ")[0]
    
    cust_data = merged_cust[merged_cust["global_customer_id"] == selected_id].iloc[0]
    
    col_info, col_kpis = st.columns([4, 6])
    
    with col_info:
        st.markdown(f"""
        ### 👤 Perfil del Cliente
        - **Global Customer ID:** `{cust_data['global_customer_id']}`
        - **Nombre:** **{cust_data['full_name']}**
        - **Email:** `{cust_data['email']}`
        - **Teléfono:** `{cust_data['phone']}`
        - **Ubicación:** {cust_data['street_address']}, {cust_data['city']} ({cust_data['country']})
        - **Segmento:** 🏷️ **{cust_data['customer_rfm_segment']}**
        """)
        
    with col_kpis:
        st.markdown("### 📊 Métricas Customer 360")
        k1, k2, k3 = st.columns(3)
        k1.metric("Gasto Total (LTV)", f"${cust_data['lifetime_net_spend']:,.2f}")
        k2.metric("Pedidos Totales", f"{int(cust_data['total_completed_orders'])}")
        k3.metric("Ticket Medio (AOV)", f"${cust_data['average_order_value']:,.2f}")
        
    st.markdown("---")
    
    st.subheader(f"🛒 Historial de Pedidos de {cust_data['full_name']}")
    cust_orders = orders[orders["global_customer_id"] == selected_id].sort_values(by="order_date", ascending=False)
    if not cust_orders.empty:
        st.dataframe(
            cust_orders[[
                "order_id", "order_date", "category", "subcategory", 
                "quantity", "unit_price", "discount_rate", "net_amount", "order_status"
            ]],
            use_container_width=True
        )
    else:
        st.info("Este cliente no tiene pedidos registrados.")
        
    # MDM Lineage for this customer
    st.subheader("🧬 Linaje MDM (Registros de Origen Unificados)")
    source_records = silver_cust[silver_cust["global_customer_id"] == selected_id]
    st.dataframe(source_records[["source_record_id", "source_system", "first_name", "last_name", "email", "phone", "city", "updated_at"]], use_container_width=True)

# ==========================================
# 4. MDM & ARCHITECTURE HUB
# ==========================================
elif view_mode == "🧬 MDM & Architecture Hub":
    st.title("🧬 Master Data Management & Arquitectura del Lakehouse")
    
    total_sources = len(silver_cust)
    total_gold_identities = silver_cust["global_customer_id"].nunique()
    duplicates_merged = total_sources - total_gold_identities
    dedup_ratio = (duplicates_merged / total_sources * 100) if total_sources else 0
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📥 Registros Crudos Procesados", f"{total_sources:,}")
    m2.metric("🏆 Golden Records Creados", f"{total_gold_identities:,}")
    m3.metric("🔗 Duplicados Unificados", f"{duplicates_merged:,}")
    m4.metric("📈 Tasa de Deduplicación", f"{dedup_ratio:.1f}%")
    
    st.markdown("---")
    
    st.subheader("🏛️ Diagrama de Flujo del Lakehouse (Medallion Architecture)")
    st.markdown("""
    ```
    [ Fuentes / APIs ] ──► [ Bronce: 01_raw/*.parquet ] ──► [ Plata: 02_silver (Splink MDM) ] ──► [ Oro: 03_gold (Kimball Marts) ]
    ```
    - **Capa Bronce:** Archivos Parquet crudos particionados.
    - **Capa Plata:** Deduplicación probabilística (Splink + RapidFuzz) y modelos staging de dbt.
    - **Capa Oro:** Hechos (`fact_orders`, `fact_customer_rfm`) y Dimensiones (`dim_customers` con SCD Tipo 2, `dim_products`, `dim_date`).
    """)
