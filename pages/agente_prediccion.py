import streamlit as st
import pandas as pd
import joblib
import os
from dotenv import load_dotenv
from supabase import create_client
from zscore_calculator import calcular_zscores


def generar_recomendacion(prediccion, edad_meses, zscore_pe, zscore_te, area_cod, altitud):
    recomendaciones = []
    urgencia = "normal"

    if prediccion == 0:
        recomendaciones.append("El niño no presenta indicadores de riesgo de anemia.")
        recomendaciones.append("• Mantener dieta variada con alimentos ricos en hierro (sangrecita, hígado, lentejas).")
        recomendaciones.append("• Control de crecimiento en el establecimiento de salud cada 6 meses.")
    else:
        urgencia = "moderada"
        recomendaciones.append("El modelo detecta riesgo de anemia. Se recomienda evaluación clínica.")

        if edad_meses < 12:
            urgencia = "alta"
            recomendaciones.append("•Menor de 12 meses: derivación prioritaria al establecimiento de salud esta semana.")
        elif edad_meses < 24:
            recomendaciones.append("• Niño entre 12 y 24 meses: consulta médica en los próximos 7 días.")
        else:
            recomendaciones.append("• Consulta en el establecimiento de salud más cercano en los próximos 15 días.")

        if area_cod == 1:  # Rural
            recomendaciones.append("• Zona rural: acudir al puesto de salud más cercano. Solicitar suplemento de hierro según indicación del personal de salud.")
        else:
            recomendaciones.append("• Acudir al centro de salud o consultorio pediátrico para hemograma completo.")

        recomendaciones.append("• Incluir en la dieta: sangrecita, hígado, lentejas, espinaca con vitamina C (naranja, limón) para mejorar absorción.")
        recomendaciones.append("• Evitar té o café junto a las comidas principales.")

    if zscore_pe < -2:
        recomendaciones.append("⚠️ Bajo peso para la edad (Z-score P/E < -2): solicitar evaluación nutricional con especialista.")

    if zscore_te < -2:
        recomendaciones.append("⚠️ Talla baja para la edad (Z-score T/E < -2): posible desnutrición crónica. Incluir en programa de seguimiento nutricional.")

    if altitud > 3000:
        recomendaciones.append(f"• Altitud elevada ({altitud} msnm): considerar ajuste de valores de hemoglobina por altura según tablas OMS al momento del diagnóstico clínico.")

    return urgencia, recomendaciones



# Configuración
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Cargar modelo y encoders
modelo  = joblib.load('modelo_rf.pkl')
le_area = joblib.load('le_area.pkl')
le_depto= joblib.load('le_depto.pkl')

DEPARTAMENTOS = [
    'Amazonas', 'Áncash', 'Apurímac', 'Arequipa', 'Ayacucho',
    'Cajamarca', 'Callao', 'Cusco', 'Huancavelica', 'Huánuco',
    'Ica', 'Junín', 'La Libertad', 'Lambayeque', 'Lima',
    'Loreto', 'Madre de Dios', 'Moquegua', 'Pasco', 'Piura',
    'Puno', 'San Martín', 'Tacna', 'Tumbes', 'Ucayali'
]

# Interfaz
st.set_page_config(
    page_title="Agente de Detección de Anemia Infantil",
    page_icon="🩺",
    layout="centered"
)

st.title("Agente de Detección de Anemia Infantil")
st.markdown(
    "Sistema de predicción del riesgo de anemia en niños "
    "menores de 5 años basado en técnicas de aprendizaje automático."
)
st.divider()

# Formulario
st.subheader("Datos del niño")

col1, col2 = st.columns(2)

with col1:
    edad_meses = st.number_input(
        "Edad (meses)", min_value=6, max_value=59,
        value=24, step=1
    )
    peso_kg = st.number_input(
        "Peso (kg)", min_value=3.0, max_value=30.0,
        value=12.0, step=0.1, format="%.1f"
    )
    talla_cm = st.number_input(
        "Talla (cm)", min_value=50.0, max_value=130.0,
        value=85.0, step=0.1, format="%.1f"
    )
    altitud = st.number_input(
        "Altitud (msnm)", min_value=0, max_value=5000,
        value=150, step=10
    )

with col2:
    sexo = st.selectbox(
        "Sexo", options=['M', 'F'],
        format_func=lambda x: 'Masculino' if x == 'M' else 'Femenino'
    )
    area = st.selectbox(
        "Área de residencia", options=['Urbana', 'Rural']
    )
    departamento = st.selectbox(
        "Departamento", options=DEPARTAMENTOS,
        index=DEPARTAMENTOS.index('Lima')
    )

st.divider()

# Predicción
if st.button("Evaluar riesgo de anemia", use_container_width=True):

    with st.spinner("Analizando datos..."):

        # Calcular Z-scores con tablas OMS
        z_talla, z_peso, z_peso_talla, z_imc = calcular_zscores(
            edad_meses, peso_kg, talla_cm, sexo
        )

        # Encodear variables categóricas
        try:
            area_cod  = le_area.transform([area])[0]
            depto_cod = le_depto.transform([departamento])[0]
        except ValueError:
            st.error("Error: departamento o área no reconocida.")
            st.stop()

        # Construir input para el modelo
        features = [
            'Edad_Meses', 'Peso_kg', 'Talla_cm',
            'Zscore_Talla_Edad', 'Zscore_Peso_Edad',
            'Zscore_Peso_Talla', 'Zscore_IMC',
            'Altitud', 'Area_cod', 'Depto_cod'
        ]
        datos = pd.DataFrame([[
            edad_meses, peso_kg, talla_cm,
            z_talla, z_peso, z_peso_talla, z_imc,
            altitud, area_cod, depto_cod
        ]], columns=features)

        # Predecir
        proba = modelo.predict_proba(datos)[0][1]
        pred  = 1 if proba >= 0.35 else 0
        resultado = "Con anemia" if pred == 1 else "Sin anemia"

    # Mostrar resultado
    st.subheader("Resultado")

    urgencia, recomendaciones = generar_recomendacion(
        prediccion=pred,
        edad_meses=edad_meses,
        zscore_pe=z_peso,
        zscore_te=z_talla,
        area_cod=area_cod,
        altitud=altitud
    )

    if pred == 1:
        st.error(f"⚠️ **{resultado}**")
    else:
        st.success(f"✅ **{resultado}**")

    st.metric(label="Probabilidad de anemia", value=f"{proba:.1%}")

    if urgencia == "alta":
        st.error("🔴 Requiere atención urgente")
    elif urgencia == "moderada":
        st.warning("⚠️ Se recomienda consulta médica")

    st.subheader("Recomendaciones")
    for r in recomendaciones:
        st.write(r)

    # Z-scores calculados
    with st.expander("Ver Z-scores calculados (OMS)"):
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Talla/Edad",  z_talla)
        col_b.metric("Peso/Edad",   z_peso)
        col_c.metric("Peso/Talla",  z_peso_talla)
        col_d.metric("IMC",         z_imc)

    # Guardar en Supabase
    try:
        supabase.table("predicciones").insert({
            "edad_meses"  : int(edad_meses),
            "peso_kg"     : float(peso_kg),
            "talla_cm"    : float(talla_cm),
            "altitud"     : int(altitud),
            "sexo"        : sexo,
            "area"        : area,
            "departamento": departamento,
            "z_talla_edad": float(z_talla),
            "z_peso_edad" : float(z_peso),
            "z_peso_talla": float(z_peso_talla),
            "z_imc"       : float(z_imc),
            "resultado"   : resultado,
            "probabilidad": float(round(proba, 4))
        }).execute()
        st.caption("✓ Consulta guardada en base de datos")
    except Exception as e:
        st.caption(f"⚠️ No se pudo guardar en base de datos: {e}")

st.divider()
st.caption(
    "Desarrollado por Grupo 01 — USIL | "
    "Agentes Inteligentes 2026-1 | "
    "Datos: ENDES 2019–2024"
)