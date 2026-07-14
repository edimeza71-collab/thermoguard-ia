import streamlit as st
import requests
import google.generativeai as genai

# --- CONFIGURACIÓN SEGURA DE IA ---
# El sistema buscará la llave en los secretos de Streamlit
clave_secreta = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=clave_secreta)

# --- CONFIGURACIÓN DE CONEXIONES ---
FIREBASE_URL = "https://monitoreoia-b2097-default-rtdb.firebaseio.com/datos.json"
BOT_TOKEN = "8916674528:AAG0uHgWcg-5h4QB_BqidoNUQPyxBHZ3Ebc"
CHAT_ID = "1476571501"
APP_URL = "https://thermoguard-ia.streamlit.app"

# Configuración de la pestaña de la página web
st.set_page_config(page_title="Panel TECNI HOME", page_icon="❄️", layout="centered")

st.title("❄️ Control de Refrigeración - TECNI HOME")
st.write("Monitoreo en tiempo real del ciclo de refrigeración.")

# --- FUNCIÓN PARA ENVIAR TELEGRAM ---
def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        st.error("Error al intentar enviar el mensaje de Telegram.")

# --- FUNCIÓN PARA LEER FIREBASE ---
def obtener_datos():
    try:
        respuesta = requests.get(FIREBASE_URL)
        if respuesta.status_code == 200:
            return respuesta.json()
    except Exception as e:
        st.error("Error conectando a la base de datos de Firebase.")
    return None

# --- EJECUCIÓN PRINCIPAL ---
datos = obtener_datos()

if datos:
    # Extraer los datos de Firebase
    tuberia_baja = datos.get("tuberia_baja", 0.0)
    tuberia_alta = datos.get("tuberia_alta", 0.0)
    estado_sistema = datos.get("estado_equipo", "Esperando datos...")

    # Mostrar los indicadores
    col1, col2 = st.columns(2)
    col1.metric(label="Tubería Baja (Succión)", value=f"{tuberia_baja} °C")
    col2.metric(label="Tubería Alta (Líquido)", value=f"{tuberia_alta} °C")
    
    # --- VISUALIZACIÓN INTELIGENTE DEL ESTADO ---
    st.write(f"### Estado del sistema: **{estado_sistema}**")
    
    if "CODIGO" in estado_sistema:
        st.error(f"⚠️ {estado_sistema}") # Se pone ROJO automáticamente ante fallas
    elif "OPERATIVO" in estado_sistema:
        st.success("✅ El ciclo de refrigeración está operando correctamente.")
    else:
        st.warning(f"ℹ️ {estado_sistema}") # AMARILLO para estados de transición
    
    # --- LÓGICA DE ALERTAS A TELEGRAM ---
    # Solo disparamos alerta si es un código de error real
    if "CODIGO" in estado_sistema:
        alerta_msg = (
            f"🚨 ALERTA TECNI HOME 🚨\n"
            f"Falla detectada: {estado_sistema}\n"
            f"Tubería Baja: {tuberia_baja}°C\n"
            f"Tubería Alta: {tuberia_alta}°C\n\n"
            f"Revisa el panel interactivo aquí:\n{APP_URL}"
        )
        enviar_telegram(alerta_msg)
else:
    st.info("Esperando comunicación con el ESP32...")
    
# Botón para forzar la actualización de la página
st.write("---")
if st.button("Actualizar Lecturas Ahora"):
    st.rerun()
