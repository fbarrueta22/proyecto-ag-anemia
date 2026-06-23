import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuración
st.set_page_config(
    page_title="Visualización | Anemia Infantil",
    page_icon="📊",
    layout="wide"
)

# Carga de datos
@st.cache_data
def cargar_datos():
    df = pd.read_csv("ENDES_Anemia_Hogar_2019_2024_LIMPIO.csv")
    df["Grupo_Edad"] = pd.cut(
        df["Edad_Meses"],
        bins=[5, 11, 23, 35, 47, 59],
        labels=["6–11 m", "12–23 m", "24–35 m", "36–47 m", "48–59 m"]
    )
    df["Tiene_Anemia"] = df["Nivel_Anemia"] != "Sin anemia"
    return df

df = cargar_datos()

# Paleta 
COLOR_MAP = {
    "Sin anemia": "#4CAF50",
    "Leve":       "#FFC107",
    "Moderada":   "#FF5722",
    "Severa":     "#B71C1C",
}
AZUL_PRINCIPAL = "#1565C0"

# Encabezado 
st.title("📊 Visualización de Datos — Anemia Infantil")
st.markdown(
    "Exploración visual del dataset **ENDES 2019–2024** con "
    f"**{len(df):,}** registros de niños menores de 5 años en el Perú."
)
st.divider()

# Filtros laterales
with st.sidebar:
    st.header("🎛️ Filtros")

    anos_disp = sorted(df["ANO"].unique())
    anos_sel = st.multiselect(
        "Año(s)", anos_disp, default=anos_disp,
        help="Selecciona uno o varios años"
    )

    area_sel = st.multiselect(
        "Área de residencia",
        ["Urbana", "Rural"],
        default=["Urbana", "Rural"]
    )

    deptos_disp = sorted(df["Departamento"].unique())
    deptos_sel = st.multiselect(
        "Departamento(s)", deptos_disp, default=deptos_disp
    )

    st.divider()
    st.caption("Datos: ENDES 2019–2024 · INEI · Grupo 01 USIL")

# Aplicar filtros
mask = (
    df["ANO"].isin(anos_sel) &
    df["Area_Residencia"].isin(area_sel) &
    df["Departamento"].isin(deptos_sel)
)
dff = df[mask].copy()

if dff.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()

# KPIs 
total        = len(dff)
con_anemia   = dff["Tiene_Anemia"].sum()
sin_anemia   = total - con_anemia
pct_anemia   = con_anemia / total * 100
pct_severa   = (dff["Nivel_Anemia"] == "Severa").sum() / total * 100

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total niños", f"{total:,}")
k2.metric("Con anemia", f"{con_anemia:,}", f"{pct_anemia:.1f}%")
k3.metric("Sin anemia", f"{sin_anemia:,}")
k4.metric("Casos severos", f"{(dff['Nivel_Anemia']=='Severa').sum():,}", f"{pct_severa:.2f}%")

st.divider()

# FILA 1 — Distribución general + Tendencia temporal
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Distribución por nivel de anemia")
    dist = dff["Nivel_Anemia"].value_counts().reset_index()
    dist.columns = ["Nivel", "Casos"]
    orden = ["Sin anemia", "Leve", "Moderada", "Severa"]
    dist["Nivel"] = pd.Categorical(dist["Nivel"], categories=orden, ordered=True)
    dist = dist.sort_values("Nivel")
    fig_pie = px.pie(
        dist, names="Nivel", values="Casos",
        color="Nivel", color_discrete_map=COLOR_MAP,
        hole=0.45
    )
    fig_pie.update_traces(textposition="outside", textinfo="percent+label")
    fig_pie.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    st.subheader("Tendencia anual de casos de anemia (2019–2024)")
    tend = (
        dff.groupby(["ANO", "Nivel_Anemia"])
        .size().reset_index(name="Casos")
    )
    fig_tend = px.line(
        tend, x="ANO", y="Casos", color="Nivel_Anemia",
        color_discrete_map=COLOR_MAP,
        markers=True, labels={"ANO": "Año", "Nivel_Anemia": "Nivel"}
    )
    fig_tend.update_layout(margin=dict(t=20, b=20), legend_title="Nivel")
    fig_tend.update_xaxes(tickvals=anos_disp)
    st.plotly_chart(fig_tend, use_container_width=True)

st.divider()

# FILA 2 — Zonas con más niños con anemia
st.subheader("🗺️ Zonas con mayor número de niños con anemia")

col3, col4 = st.columns([3, 2])

with col3:
    anemia_depto = (
        dff[dff["Tiene_Anemia"]]
        .groupby("Departamento")
        .size().reset_index(name="Casos_Anemia")
        .sort_values("Casos_Anemia", ascending=True)
    )
    fig_bar = px.bar(
        anemia_depto, x="Casos_Anemia", y="Departamento",
        orientation="h",
        color="Casos_Anemia",
        color_continuous_scale=["#FFE082", "#FF5722", "#B71C1C"],
        labels={"Casos_Anemia": "Casos con anemia", "Departamento": ""},
        text="Casos_Anemia"
    )
    fig_bar.update_traces(textposition="outside")
    fig_bar.update_layout(
        coloraxis_showscale=False,
        margin=dict(t=10, b=10),
        height=550
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col4:
    st.markdown("**Tasa de anemia por departamento (%)**")
    tasa_depto = (
        dff.groupby("Departamento")
        .agg(Total=("Tiene_Anemia", "count"), Anemia=("Tiene_Anemia", "sum"))
        .assign(Tasa=lambda x: (x["Anemia"] / x["Total"] * 100).round(1))
        .reset_index()
        .sort_values("Tasa", ascending=False)
    )
    fig_tasa = px.bar(
        tasa_depto.head(15), x="Tasa", y="Departamento",
        orientation="h",
        color="Tasa",
        color_continuous_scale=["#FFF9C4", "#F57F17", "#B71C1C"],
        labels={"Tasa": "% con anemia", "Departamento": ""},
        text=tasa_depto.head(15)["Tasa"].apply(lambda v: f"{v}%")
    )
    fig_tasa.update_traces(textposition="outside")
    fig_tasa.update_layout(
        coloraxis_showscale=False,
        margin=dict(t=10, b=10),
        height=550,
        yaxis=dict(autorange="reversed")
    )
    st.plotly_chart(fig_tasa, use_container_width=True)

st.divider()

# FILA 3 — Edad con mayor número de niños con anemia
st.subheader("👶 Edad con mayor número de niños con anemia")

col5, col6 = st.columns(2)

with col5:
    edad_anemia = (
        dff[dff["Tiene_Anemia"]]
        .groupby(["Grupo_Edad", "Nivel_Anemia"])
        .size().reset_index(name="Casos")
    )
    orden_edad = ["6–11 m", "12–23 m", "24–35 m", "36–47 m", "48–59 m"]
    orden_nivel = ["Leve", "Moderada", "Severa"]
    edad_anemia["Grupo_Edad"] = pd.Categorical(edad_anemia["Grupo_Edad"], categories=orden_edad, ordered=True)
    edad_anemia["Nivel_Anemia"] = pd.Categorical(edad_anemia["Nivel_Anemia"], categories=orden_nivel, ordered=True)
    edad_anemia = edad_anemia.sort_values(["Grupo_Edad", "Nivel_Anemia"])

    fig_edad = px.bar(
        edad_anemia, x="Grupo_Edad", y="Casos",
        color="Nivel_Anemia", barmode="stack",
        color_discrete_map=COLOR_MAP,
        labels={"Grupo_Edad": "Grupo de edad", "Casos": "Casos con anemia", "Nivel_Anemia": "Nivel"},
        text_auto=True
    )
    fig_edad.update_layout(margin=dict(t=10, b=10))
    st.plotly_chart(fig_edad, use_container_width=True)

with col6:
    # Tasa de anemia por grupo de edad
    tasa_edad = (
        dff.groupby("Grupo_Edad")
        .agg(Total=("Tiene_Anemia", "count"), Anemia=("Tiene_Anemia", "sum"))
        .assign(Tasa=lambda x: x["Anemia"] / x["Total"] * 100)
        .reset_index()
    )
    fig_tasa_edad = px.area(
        tasa_edad, x="Grupo_Edad", y="Tasa",
        color_discrete_sequence=[AZUL_PRINCIPAL],
        labels={"Grupo_Edad": "Grupo de edad", "Tasa": "% con anemia"},
        markers=True, text=tasa_edad["Tasa"].apply(lambda v: f"{v:.1f}%")
    )
    fig_tasa_edad.update_traces(textposition="top center")
    fig_tasa_edad.update_layout(margin=dict(t=10, b=10))
    st.plotly_chart(fig_tasa_edad, use_container_width=True)

st.divider()

# FILA 4 — Urbano vs Rural + Hemoglobina
st.subheader("🏘️ Área de residencia y niveles de hemoglobina")

col7, col8 = st.columns(2)

with col7:
    area_nivel = (
        dff.groupby(["Area_Residencia", "Nivel_Anemia"])
        .size().reset_index(name="Casos")
    )
    fig_area = px.bar(
        area_nivel, x="Area_Residencia", y="Casos",
        color="Nivel_Anemia", barmode="group",
        color_discrete_map=COLOR_MAP,
        labels={"Area_Residencia": "Área", "Casos": "Casos", "Nivel_Anemia": "Nivel"},
        text_auto=True
    )
    fig_area.update_layout(margin=dict(t=10, b=10))
    st.plotly_chart(fig_area, use_container_width=True)

with col8:
    # Distribución de hemoglobina por nivel
    fig_hb = px.box(
        dff, x="Nivel_Anemia", y="Hemoglobina",
        color="Nivel_Anemia", color_discrete_map=COLOR_MAP,
        category_orders={"Nivel_Anemia": ["Sin anemia", "Leve", "Moderada", "Severa"]},
        labels={"Nivel_Anemia": "Nivel de anemia", "Hemoglobina": "Hemoglobina (g/dL × 10)"},
        points=False
    )
    fig_hb.update_layout(showlegend=False, margin=dict(t=10, b=10))
    st.plotly_chart(fig_hb, use_container_width=True)

st.divider()

# FILA 5 — Mapa de calor: Departamento × Año
st.subheader("🔥 Mapa de calor: casos de anemia por departamento y año")

heatmap_data = (
    dff[dff["Tiene_Anemia"]]
    .groupby(["Departamento", "ANO"])
    .size().reset_index(name="Casos")
    .pivot(index="Departamento", columns="ANO", values="Casos")
    .fillna(0)
)

fig_heat = px.imshow(
    heatmap_data,
    color_continuous_scale=["#FFF9C4", "#FF5722", "#B71C1C"],
    labels=dict(x="Año", y="Departamento", color="Casos"),
    aspect="auto",
    text_auto=True
)
fig_heat.update_layout(margin=dict(t=10, b=10), height=650)
st.plotly_chart(fig_heat, use_container_width=True)

st.divider()

# FILA 6 — Altitud vs anemia + Z-scores
st.subheader("⛰️ Relación entre altitud, estado nutricional y anemia")

col9, col10 = st.columns(2)

with col9:
    # Altitud promedio por nivel de anemia
    alt_nivel = (
        dff.groupby("Nivel_Anemia")["Altitud"]
        .mean().reset_index()
        .rename(columns={"Altitud": "Altitud_Promedio"})
    )
    orden_niv = ["Sin anemia", "Leve", "Moderada", "Severa"]
    alt_nivel["Nivel_Anemia"] = pd.Categorical(alt_nivel["Nivel_Anemia"], categories=orden_niv, ordered=True)
    alt_nivel = alt_nivel.sort_values("Nivel_Anemia")
    fig_alt = px.bar(
        alt_nivel, x="Nivel_Anemia", y="Altitud_Promedio",
        color="Nivel_Anemia", color_discrete_map=COLOR_MAP,
        labels={"Nivel_Anemia": "Nivel", "Altitud_Promedio": "Altitud promedio (msnm)"},
        text=alt_nivel["Altitud_Promedio"].apply(lambda v: f"{v:.0f} m")
    )
    fig_alt.update_traces(textposition="outside")
    fig_alt.update_layout(showlegend=False, margin=dict(t=10, b=10))
    st.plotly_chart(fig_alt, use_container_width=True)

with col10:
    # Z-score Talla/Edad promedio por nivel (desnutrición crónica)
    zsc_nivel = (
        dff.groupby("Nivel_Anemia")[["Zscore_Talla_Edad", "Zscore_Peso_Edad"]]
        .mean().reset_index()
        .melt(id_vars="Nivel_Anemia", var_name="Indicador", value_name="Z_score_promedio")
    )
    nombre_map = {"Zscore_Talla_Edad": "T/E (Talla-Edad)", "Zscore_Peso_Edad": "P/E (Peso-Edad)"}
    zsc_nivel["Indicador"] = zsc_nivel["Indicador"].map(nombre_map)
    zsc_nivel["Nivel_Anemia"] = pd.Categorical(zsc_nivel["Nivel_Anemia"], categories=orden_niv, ordered=True)
    zsc_nivel = zsc_nivel.sort_values("Nivel_Anemia")
    fig_zsc = px.bar(
        zsc_nivel, x="Nivel_Anemia", y="Z_score_promedio",
        color="Indicador", barmode="group",
        labels={"Nivel_Anemia": "Nivel", "Z_score_promedio": "Z-score promedio", "Indicador": ""},
        color_discrete_sequence=["#1565C0", "#00897B"]
    )
    fig_zsc.update_layout(margin=dict(t=10, b=10))
    st.plotly_chart(fig_zsc, use_container_width=True)

# ── Pie de página ─────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Desarrollado por Grupo 01 — USIL | "
    "Agentes Inteligentes 2026-1 | "
    "Datos: ENDES 2019–2024"
)
