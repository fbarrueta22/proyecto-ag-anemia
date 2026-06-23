import streamlit as st

st.set_page_config(
    page_title="Anemia Infantil — Grupo 01 USIL",
    page_icon="🩺",
    layout="centered"
)

st.title("🩺 Sistema de Detección de Anemia Infantil")
st.markdown(
    "Plataforma integral para la **predicción y análisis** del riesgo de anemia "
    "en niños menores de 5 años en el Perú, basada en datos **ENDES 2019–2024**."
)
st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🤖 Agente de Detección")
    st.markdown(
        "Ingresa los datos de un niño y el modelo de Machine Learning "
        "predice el riesgo de anemia con recomendaciones personalizadas."
    )
    if st.button("Ir al Agente →", use_container_width=True):
        st.switch_page("pages/agente_prediccion.py")

with col2:
    st.markdown("### 📊 Visualización de Datos")
    st.markdown(
        "Explora gráficos interactivos sobre las zonas con más casos, "
        "grupos de edad más afectados, tendencias anuales y más."
    )
    if st.button("Ir a Visualización →", use_container_width=True):
        st.switch_page("pages/visualizacion.py")

st.divider()
st.markdown(
    """
    **Fuente de datos:** Instituto Nacional de Estadística e Informática (INEI)  
    **Encuesta:** ENDES (Encuesta Demográfica y de Salud Familiar) 2019–2024  
    **Modelo:** Random Forest con ajuste por umbral (≥ 35% de probabilidad)
    """
)
st.caption("Desarrollado por Grupo 01 — USIL | Agentes Inteligentes 2026-1")
