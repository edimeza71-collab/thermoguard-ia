import streamlit as st
import requests
import google.generativeai as genai

# --- CONFIGURACIÓN DE CONEXIONES ---
FIREBASE_URL = "https://monitoreoia-b2097-default-rtdb.firebaseio.com/datos.json"
BOT_TOKEN = "8916674528:AAG0uHgWcg-5h4QB_BqidoNUQPyxBHZ3Ebc"
CHAT_ID = "1476571501"
APP_URL = "https://thermoguard-ia-8tnwql6ndqvxzbebelhdvy.streamlit.app"

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
st.set_page_config(page_title="Panel TECNI HOME", page_icon="❄️", layout="centered")

st.title("❄️ Control de Refrigeración - TECNI HOME")

# --- FUNCIONES ---
def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": CHAT_ID, "text": mensaje})
    except: pass

def analizar_falla_con_ia(baja, alta, estado):
    try:
        modelos = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        modelo_final = next((m for m in modelos if "flash" in m), modelos[0])
        model = genai.GenerativeModel(modelo_final)
        prompt = f"Experto TECNI HOME. Estado: {estado}. Baja: {baja}°C, Alta: {alta}°C. ¿Qué revisar de forma directa?"
        return model.generate_content(prompt).text
    except Exception as e: return f"Error IA: {str(e)}"

def obtener_datos():
    try:
        resp = requests.get(FIREBASE_URL)
        return resp.json() if resp.status_code == 200 else None
    except: return None

# --- EJECUCIÓN PRINCIPAL ---
if 'estado_anterior' not in st.session_state: st.session_state.estado_anterior = ""

datos = obtener_datos()

if datos:
    tuberia_baja = datos.get("tuberia_baja", 0.0)
    tuberia_alta = datos.get("tuberia_alta", 0.0)
    estado_sistema = datos.get("estado_equipo", "Esperando datos...")

    col1, col2 = st.columns(2)
    col1.metric("Tubería Baja", f"{tuberia_baja} °C")
    col2.metric("Tubería Alta", f"{tuberia_alta} °C")
    st.write(f"### Estado: **{estado_sistema}**")
    
    # Manejo inteligente de estados para el Dashboard
    if estado_sistema != st.session_state.estado_anterior:
        if "REINICIADO" in estado_sistema:
            enviar_telegram(f"⚡ Aviso TECNI HOME: El sistema se ha reiniciado (posible corte eléctrico).")
        st.session_state.estado_anterior = estado_sistema

    if "CODIGO" in estado_sistema:
        st.error(f"⚠️ {estado_sistema}")
        if st.button("💡 Analizar Falla con IA"):
            with st.spinner("Consultando..."): st.info(analizar_falla_con_ia(tuberia_baja, tuberia_alta, estado_sistema))
    elif "REINICIADO" in estado_sistema:
        st.info("ℹ️ Sistema recién encendido. Esperando estabilización de lecturas...")
    elif "OPERATIVO" in estado_sistema:
        st.success("✅ Sistema operando correctamente.")
    else:
        st.warning(f"ℹ️ {estado_sistema}")
else:
    st.info("Esperando comunicación...")

if st.button("Actualizar"): st.rerun()
