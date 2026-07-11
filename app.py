
import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# === CONFIGURACIÓN DE LA PÁGINA ===
st.set_page_config(page_title="Dashboard Industrial IoT", layout="wide")
st.title("❄️ Panel de Monitoreo: Cavas de Congelación")

# === CONEXIÓN A LA BASE DE DATOS ===
# Sustituye esta URL por la tuya de Firebase
URL_FIREBASE = "https://monitoreoia-b2097-default-rtdb.firebaseio.com/historial_ia.json"

def cargar_datos():
    respuesta = requests.get(URL_FIREBASE)
    if respuesta.status_code == 200 and respuesta.json() is not None:
        # Convertimos el JSON de Google a una tabla ordenada
        df = pd.DataFrame.from_dict(respuesta.json(), orient='index')
        return df
    else:
        return pd.DataFrame()

df = cargar_datos()

if df.empty:
    st.warning("No hay datos en la base de datos todavía. Corre el simulador primero.")
else:
    # Ordenamos por fecha para tener lo más reciente al final
    df = df.sort_values(by="fecha_hora")
    ultima_lectura = df.iloc[-1]

    # === 1. INDICADORES EN TIEMPO REAL ===
    st.subheader("📡 Monitoreo en Tiempo Real")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("🌡️ Temperatura Actual", f"{ultima_lectura['temperatura']} °C")
    with col2:
        st.metric("⏱️ Presión Actual", f"{ultima_lectura['presion']} PSI")
    with col3:
        estado = ultima_lectura['diagnostico_ia']
        color = "red" if "CRÍTICO" in estado.upper() else "green"
        st.markdown(f"**Estado del Sistema:** <br><span style='color:{color}; font-size:24px'>{estado}</span>", unsafe_allow_html=True)

    st.divider()

    # === 2. GRÁFICA HISTÓRICA ===
    st.subheader("📈 Comportamiento Térmico")
    fig = px.line(df, x="fecha_hora", y="temperatura", markers=True, title="Variación de Temperatura en el Tiempo")
    fig.add_hline(y=-10, line_dash="dash", line_color="red", annotation_text="Límite de Riesgo")
    st.plotly_chart(fig, use_container_width=True)

    # === 3. TABLA DE BITÁCORA ===
    st.subheader("📋 Historial de Base de Datos")
    st.dataframe(df, use_container_width=True, hide_index=True)
