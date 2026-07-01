import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ======================================================================================
# 1. CONFIGURACION DE LA PAGINA
# ======================================================================================
st.set_page_config(
    page_title="Panel de control de análisis del sector minorista",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----- Paleta de marca (consistente en todos los graficos) -----------------------------
BG_COLOR = "#0b111e"
CARD_COLOR = "#141b2d"
BORDER_COLOR = "#232f4b"
ACCENT = "#00e5ff"
ACCENT_2 = "#7c5cff"
TEXT_MUTED = "#8892b0"

SEGMENT_COLORS = {
    "Campeones (VIP)": "#00e5ff",
    "En Riesgo de Abandono": "#ff5c7a",
    "Nuevos Clientes": "#34d399",
    "Clientes Dormidos": "#8892b0",
    "Clientes Regulares": "#7c5cff",
}
SEQUENTIAL = ["#00e5ff", "#4facfe", "#7c5cff", "#c084fc", "#ff8fab", "#34d399"]

PLOTLY_TEMPLATE = "plotly_dark"

st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {BG_COLOR}; }}
    #MainMenu, footer {{ visibility: hidden; }}

    /* Tarjetas de metricas */
    div[data-testid="stMetric"] {{
        background-color: {CARD_COLOR};
        border: 1px solid {BORDER_COLOR};
        border-radius: 12px;
        padding: 16px 18px;
    }}
    div[data-testid="stMetricValue"] {{ color: {ACCENT}; font-size: 26px; font-weight: 700; }}
    div[data-testid="stMetricLabel"] {{ color: {TEXT_MUTED}; }}
    div[data-testid="stMetricDelta"] {{ color: #34d399; }}

    /* Contenedores con borde (tarjetas de graficos) */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: {CARD_COLOR};
        border-radius: 12px;
        border: 1px solid {BORDER_COLOR};
    }}

    h1, h2, h3 {{ color: #ffffff; }}
    .subtitle {{ color: {TEXT_MUTED}; font-size: 15px; margin-top: -10px; }}
    .section-title {{ color: #ffffff; font-weight: 600; margin-bottom: 4px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Mapa de ciudades sueltas a su estado (los datos de origen mezclan ciudades y estados)
CITY_TO_STATE = {
    "Chicago": "Illinois",
    "Houston": "Texas",
    "Los Angeles": "California",
    "Phoenix": "Arizona",
}

STATE_TO_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
    "Virginia": "VA", "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI",
    "Wyoming": "WY", "District of Columbia": "DC",
}


def style_fig(fig):
    """Aplica un estilo consistente (fondo transparente, fuente clara) a cualquier figura."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e5e9f0"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig


# ======================================================================================
# 2. CARGA Y PROCESAMIENTO DE DATOS
# ======================================================================================
@st.cache_data
def cargar_y_procesar_datos():
    customers = pd.read_csv("customer_data.csv")
    orders = pd.read_csv("order_data.csv")

    customers.columns = customers.columns.str.strip()
    orders.columns = orders.columns.str.strip()

    # Normalizar tipos de la llave de union para evitar perdidas silenciosas en el merge
    customers["Customer ID"] = pd.to_numeric(customers["Customer ID"], errors="coerce")
    orders["Customer ID"] = pd.to_numeric(orders["Customer ID"], errors="coerce")

    orders["Order Date"] = pd.to_datetime(orders["Order Date"], format="%d-%m-%Y", errors="coerce")
    orders = orders.dropna(subset=["Order Date", "Customer ID"])

    # Normalizar ciudades sueltas a su estado para el mapa geografico
    customers["Region"] = customers["Location"].replace(CITY_TO_STATE)
    customers["Region_Abbr"] = customers["Region"].map(STATE_TO_ABBR)

    # Calculos de negocio
    orders["Total_Sales"] = orders["Quantity"] * orders["List Price"] * (1 - orders["Discount Percent"] / 100)
    orders["Total_Cost"] = orders["Quantity"] * orders["cost price"]
    orders["Profit"] = orders["Total_Sales"] - orders["Total_Cost"]

    master = pd.merge(orders, customers, on="Customer ID", how="inner")
    return master


@st.cache_data
def calcular_rfm(df):
    fecha_referencia = df["Order Date"].max() + pd.Timedelta(days=1)

    rfm = df.groupby("Customer ID").agg(
        Recencia=("Order Date", lambda x: (fecha_referencia - x.max()).days),
        Frecuencia=("Order Id", "count"),
        Monetario=("Total_Sales", "sum"),
    )

    # Se usa rank() antes de qcut para evitar errores por bordes de bin duplicados
    # cuando existen muchos clientes con el mismo valor de recencia/frecuencia/monto.
    rfm["R_Score"] = pd.qcut(rfm["Recencia"].rank(method="first"), q=4, labels=[4, 3, 2, 1]).astype(int)
    rfm["F_Score"] = pd.qcut(rfm["Frecuencia"].rank(method="first"), q=4, labels=[1, 2, 3, 4]).astype(int)
    rfm["M_Score"] = pd.qcut(rfm["Monetario"].rank(method="first"), q=4, labels=[1, 2, 3, 4]).astype(int)

    def asignar_segmento(row):
        r, f, m = row["R_Score"], row["F_Score"], row["M_Score"]
        if r >= 3 and f >= 3 and m >= 3:
            return "Campeones (VIP)"
        elif r <= 2 and f >= 3 and m >= 3:
            return "En Riesgo de Abandono"
        elif r >= 3 and f <= 2:
            return "Nuevos Clientes"
        elif r <= 2 and f <= 2:
            return "Clientes Dormidos"
        else:
            return "Clientes Regulares"

    rfm["Segmento"] = rfm.apply(asignar_segmento, axis=1)
    return rfm


try:
    master_df = cargar_y_procesar_datos()
    rfm_df = calcular_rfm(master_df)
except FileNotFoundError as e:
    st.error(f"No se encontro un archivo de datos requerido: {e}")
    st.stop()
except Exception as e:
    st.error(f"Error al cargar los archivos CSV: {e}")
    st.stop()

# ======================================================================================
# 3. BARRA LATERAL (FILTROS GLOBALES)
# ======================================================================================
st.sidebar.title("🎛️ Panel de Control")
st.sidebar.markdown("Filtra las metricas globales de tu comercio.")

opciones_genero = ["Todos"] + sorted(master_df["Gender"].dropna().unique().tolist())
genero_seleccionado = st.sidebar.selectbox("Genero del Cliente", opciones_genero)

opciones_categoria = ["Todas"] + sorted(master_df["Category"].dropna().unique().tolist())
categoria_seleccionada = st.sidebar.selectbox("Categoria de Producto", opciones_categoria)

opciones_segmento_negocio = ["Todos"] + sorted(master_df["Segment"].dropna().unique().tolist())
segmento_negocio_seleccionado = st.sidebar.selectbox("Segmento de Negocio", opciones_segmento_negocio)

fecha_min = master_df["Order Date"].min().to_pydatetime()
fecha_max = master_df["Order Date"].max().to_pydatetime()

fechas_seleccionadas = st.sidebar.slider(
    "Rango de Fechas",
    min_value=fecha_min,
    max_value=fecha_max,
    value=(fecha_min, fecha_max),
    format="DD-MM-YYYY",
)

df_filtrado = master_df.copy()
if genero_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Gender"] == genero_seleccionado]
if categoria_seleccionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Category"] == categoria_seleccionada]
if segmento_negocio_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Segment"] == segmento_negocio_seleccionado]
df_filtrado = df_filtrado[
    (df_filtrado["Order Date"] >= fechas_seleccionadas[0]) & (df_filtrado["Order Date"] <= fechas_seleccionadas[1])
]

st.sidebar.markdown("---")
st.sidebar.caption(f"📄 {len(master_df):,} pedidos historicos | {master_df['Customer ID'].nunique():,} clientes")
st.sidebar.caption(f"🕒 Datos actualizados: {datetime.now().strftime('%d-%m-%Y')}")

with st.sidebar.expander("ℹ️ ¿Que es el analisis RFM?"):
    st.markdown(
        """
        **RFM** puntua a cada cliente segun tres dimensiones (1 a 4, siendo 4 el mejor):

        - **Recencia** — dias desde su ultima compra.
        - **Frecuencia** — numero total de pedidos.
        - **Monetario** — gasto total acumulado.

        Estos puntajes combinados generan segmentos accionables como
        *Campeones*, *En Riesgo* o *Clientes Dormidos*.
        """
    )

# ======================================================================================
# 4. ENCABEZADO
# ======================================================================================
col_titulo, col_kpi_rapido = st.columns([3, 1])
with col_titulo:
    st.title("📊 Panel de control de análisis del sector minorista")
    st.markdown(
        '<p class="subtitle">Analisis integral de clientes y ventas — segmentacion RFM, tendencias '
        "comerciales y desempeno geografico.</p>",
        unsafe_allow_html=True,
    )

st.markdown("---")

if df_filtrado.empty:
    st.warning("No hay datos para los filtros seleccionados. Ajusta los filtros en la barra lateral.")
    st.stop()

# ----- KPIs globales (siempre visibles, respetan los filtros) -------------------------
ingresos_totales = df_filtrado["Total_Sales"].sum()
ganancia_total = df_filtrado["Profit"].sum()
margen = (ganancia_total / ingresos_totales * 100) if ingresos_totales else 0
num_pedidos = df_filtrado["Order Id"].nunique()
ticket_medio = df_filtrado["Total_Sales"].mean()
clientes_activos = df_filtrado["Customer ID"].nunique()

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Ingresos", f"${ingresos_totales:,.0f}")
k2.metric("Ganancia", f"${ganancia_total:,.0f}")
k3.metric("Margen", f"{margen:.1f}%")
k4.metric("Pedidos", f"{num_pedidos:,}")
k5.metric("Ticket Medio", f"${ticket_medio:,.0f}")
k6.metric("Clientes Activos", f"{clientes_activos:,}")

st.markdown("")

# ======================================================================================
# 5. CUERPO PRINCIPAL
# ======================================================================================
tab1, tab2, tab3 = st.tabs(["👥 Segmentacion RFM", "📈 Ventas y Productos", "🗺️ Vista Geografica"])

# --- PESTAÑA 1: SEGMENTACION RFM -------------------------------------------------------
with tab1:
    st.subheader("Analisis de Segmentacion de Clientes")
    st.markdown("Identifica a tus mejores clientes y reacciona ante aquellos en riesgo de abandono.")

    vips = len(rfm_df[rfm_df["Segmento"] == "Campeones (VIP)"])
    riesgo = len(rfm_df[rfm_df["Segmento"] == "En Riesgo de Abandono"])
    nuevos = len(rfm_df[rfm_df["Segmento"] == "Nuevos Clientes"])
    dormidos = len(rfm_df[rfm_df["Segmento"] == "Clientes Dormidos"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Clientes VIP", f"{vips} 🏆")
    c2.metric("En Riesgo", f"{riesgo} ⚠️")
    c3.metric("Nuevos Clientes", f"{nuevos} 🌱")
    c4.metric("Dormidos", f"{dormidos} 💤")

    st.markdown("")
    col_graf1, col_graf2 = st.columns([1, 1])

    with col_graf1:
        with st.container(border=True):
            st.markdown('<p class="section-title">Distribucion del Valor de Clientes</p>', unsafe_allow_html=True)
            segmento_counts = rfm_df["Segmento"].value_counts().reset_index()
            segmento_counts.columns = ["Segmento", "Cantidad"]

            fig_bar = px.bar(
                segmento_counts,
                x="Cantidad",
                y="Segmento",
                orientation="h",
                color="Segmento",
                template=PLOTLY_TEMPLATE,
                color_discrete_map=SEGMENT_COLORS,
                text="Cantidad",
            )
            fig_bar.update_traces(textposition="outside")
            fig_bar.update_layout(showlegend=False, yaxis_title="", xaxis_title="Clientes")
            st.plotly_chart(style_fig(fig_bar), width="stretch")

    with col_graf2:
        with st.container(border=True):
            st.markdown('<p class="section-title">Relacion Recencia vs Monetario</p>', unsafe_allow_html=True)
            fig_scatter = px.scatter(
                rfm_df,
                x="Recencia",
                y="Monetario",
                color="Segmento",
                size="Frecuencia",
                template=PLOTLY_TEMPLATE,
                hover_name="Segmento",
                color_discrete_map=SEGMENT_COLORS,
                log_y=True,
                labels={"Recencia": "Dias desde la ultima compra", "Monetario": "Gasto total (USD, log)"},
            )
            st.plotly_chart(style_fig(fig_scatter), width="stretch")

    st.markdown("")
    with st.container(border=True):
        st.markdown('<p class="section-title">🔍 Explorador de Listas de Clientes</p>', unsafe_allow_html=True)
        segmento_filtro = st.selectbox(
            "Selecciona un segmento para auditar:", sorted(rfm_df["Segmento"].unique())
        )

        tabla_clientes = rfm_df[rfm_df["Segmento"] == segmento_filtro][
            ["Recencia", "Frecuencia", "Monetario"]
        ].sort_values("Monetario", ascending=False)
        st.dataframe(tabla_clientes, width="stretch")
        st.caption(f"Mostrando {len(tabla_clientes)} clientes para el segmento '{segmento_filtro}'.")

        st.download_button(
            "⬇️ Descargar lista (CSV)",
            data=tabla_clientes.to_csv(index=True).encode("utf-8"),
            file_name=f"clientes_{segmento_filtro.lower().replace(' ', '_')}.csv",
            mime="text/csv",
        )

# --- PESTAÑA 2: VENTAS Y PRODUCTOS -----------------------------------------------------
with tab2:
    st.subheader("Analisis de Ventas e Impacto Comercial")

    with st.container(border=True):
        st.markdown('<p class="section-title">Evolucion Historica de Ventas y Ganancia</p>', unsafe_allow_html=True)
        ventas_temporales = (
            df_filtrado.groupby(df_filtrado["Order Date"].dt.to_period("M"))
            .agg(Total_Sales=("Total_Sales", "sum"), Profit=("Profit", "sum"))
            .to_timestamp()
            .reset_index()
        )

        fig_line = px.line(
            ventas_temporales,
            x="Order Date",
            y=["Total_Sales", "Profit"],
            labels={"value": "USD", "variable": "Metrica", "Order Date": "Fecha"},
            template=PLOTLY_TEMPLATE,
            color_discrete_sequence=[ACCENT, "#34d399"],
        )
        fig_line.update_traces(mode="lines+markers")
        st.plotly_chart(style_fig(fig_line), width="stretch")

    col_cat, col_top = st.columns([1, 1])

    with col_cat:
        with st.container(border=True):
            st.markdown('<p class="section-title">Ganancia por Categoria y Subcategoria</p>', unsafe_allow_html=True)
            cat_perf = (
                df_filtrado.groupby(["Category", "Sub Category"])
                .agg(Profit=("Profit", "sum"), Total_Sales=("Total_Sales", "sum"))
                .reset_index()
            )
            fig_tree = px.treemap(
                cat_perf,
                path=["Category", "Sub Category"],
                values="Total_Sales",
                color="Profit",
                color_continuous_scale=["#ff5c7a", "#232f4b", "#00e5ff"],
                template=PLOTLY_TEMPLATE,
            )
            st.plotly_chart(style_fig(fig_tree), width="stretch")

    with col_top:
        with st.container(border=True):
            st.markdown('<p class="section-title">Top 10 Productos por Ingresos</p>', unsafe_allow_html=True)
            top_productos = (
                df_filtrado.groupby("Product Id")
                .agg(Total_Sales=("Total_Sales", "sum"))
                .sort_values("Total_Sales", ascending=False)
                .head(10)
                .reset_index()
            )
            fig_top = px.bar(
                top_productos,
                x="Total_Sales",
                y="Product Id",
                orientation="h",
                template=PLOTLY_TEMPLATE,
                color_discrete_sequence=[ACCENT_2],
                labels={"Total_Sales": "Ingresos (USD)", "Product Id": ""},
            )
            fig_top.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(style_fig(fig_top), width="stretch")

# --- PESTAÑA 3: VISTA GEOGRAFICA -------------------------------------------------------
with tab3:
    st.subheader("Distribucion Geografica de Ventas")

    geo_sales = (
        df_filtrado.groupby(["Region", "Region_Abbr"])
        .agg(Total_Sales=("Total_Sales", "sum"), Pedidos=("Order Id", "nunique"))
        .reset_index()
        .dropna(subset=["Region_Abbr"])
    )
    sin_mapear = df_filtrado["Region_Abbr"].isna().sum()

    with st.container(border=True):
        st.markdown('<p class="section-title">Ingresos por Estado (EE. UU.)</p>', unsafe_allow_html=True)
        fig_map = px.choropleth(
            geo_sales,
            locations="Region_Abbr",
            locationmode="USA-states",
            color="Total_Sales",
            scope="usa",
            color_continuous_scale=["#141b2d", "#4facfe", "#00e5ff"],
            hover_name="Region",
            labels={"Total_Sales": "Ingresos (USD)"},
        )
        fig_map.update_layout(geo=dict(bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(style_fig(fig_map), width="stretch")
        if sin_mapear:
            st.caption(f"⚠️ {sin_mapear} pedidos no pudieron ubicarse en un estado y fueron excluidos del mapa.")

    with st.container(border=True):
        st.markdown('<p class="section-title">Top 10 Estados por Ingresos</p>', unsafe_allow_html=True)
        top_estados = geo_sales.sort_values("Total_Sales", ascending=False).head(10)
        fig_estados = px.bar(
            top_estados,
            x="Total_Sales",
            y="Region",
            orientation="h",
            template=PLOTLY_TEMPLATE,
            color_discrete_sequence=[ACCENT],
            labels={"Total_Sales": "Ingresos (USD)", "Region": ""},
        )
        fig_estados.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(style_fig(fig_estados), width="stretch")
