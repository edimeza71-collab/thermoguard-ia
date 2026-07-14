import streamlit as st
import requests
import google.generativeai as genai

# --- CONFIGURACIÓN DE CONEXIONES ---
FIREBASE_URL = "https://monitoreoia-b2097-default-rtdb.firebaseio.com/datos.json"
BOT_TOKEN = "8916674528:AAG0uHgWcg-5h4QB_BqidoNUQPyxBHZ3Ebc"
CHAT_ID = "1476571501"
APP_URL = "https://thermoguard-ia.streamlit.app"

# Configurar la API Key globalmente (esto corrige el error anterior)
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Configuración de la página
st.set_page_config(page_title="Panel TECNI HOME", page_icon="❄️", layout="centered")

st.title("❄️ Control de Refrigeración - TECNI HOME")

# --- FUNCIONES DE SOPORTE ---
def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje}
    try:
        requests.post(url, json=payload)
    except:
        pass

def analizar_falla_con_ia(baja, alta, estado):
    try:
        # Usamos el modelo configurado globalmente
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Eres un experto técnico de TECNI HOME. Analiza esta falla de refrigeración:
        - Estado: {estado}
        - Temp. Tubería Baja: {baja}°C
        - Temp. Tubería Alta: {alta}°C
        
        Dame un diagnóstico técnico breve y directo. ¿Qué pieza revisar primero y por qué?
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error técnico de IA: {str(e)}"

def obtener_datos():
    try:
        respuesta = requests.get(FIREBASE_URL)
        if respuesta.status_code == 200:
            return respuesta.json()
    except:
        return None
    return None

# --- EJECUCIÓN PRINCIPAL ---
datos = obtener_datos()

if datos:
    tuberia_baja = datos.get("tuberia_baja", 0.0)
    tuberia_alta = datos.get("tuberia_alta", 0.0)
    estado_sistema = datos.get("estado_equipo", "Esperando datos...")

    col1, col2 = st.columns(2)
    col1.metric(label="Tubería Baja", value=f"{tuberia_baja} °C")
    col2.metric(label="Tubería Alta", value=f"{tuberia_alta} °C")
    
    st.write(f"### Estado: **{estado_sistema}**")
    
    if "CODIGO" in estado_sistema:
        st.error(f"⚠️ {estado_sistema}")
        if st.button("💡 Analizar Falla con IA"):
            with st.spinner("Consultando al experto virtual..."):
                reporte = analizar_falla_con_ia(tuberia_baja, tuberia_alta, estado_sistema)
                st.markdown("### 🤖 Diagnóstico:")
                st.info(reporte)
        
        # Enviar alerta corta
        alerta_corta = f"🚨 ALERTA TECNI HOME: {estado_sistema}. Diagnóstico: {APP_URL}"
        enviar_telegram(alerta_corta)
        
    elif "OPERATIVO" in estado_sistema:
        st.success("✅ Sistema operando correctamente.")
    else:
        st.warning(f"ℹ️ {estado_sistema}")
else:
    st.info("Esperando comunicación con el ESP32...")
    
if st.button("Actualizar"):
    st.rerun()
