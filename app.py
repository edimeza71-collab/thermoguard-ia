import streamlit as st
import requests
import google.generativeai as genai

# --- CONFIGURACIÓN DE CONEXIONES ---
FIREBASE_URL = "https://monitoreoia-b2097-default-rtdb.firebaseio.com/datos.json"
BOT_TOKEN = "8916674528:AAG0uHgWcg-5h4QB_BqidoNUQPyxBHZ3Ebc"
CHAT_ID = "1476571501"
APP_URL = "https://thermoguard-ia.streamlit.app"

# Configurar la API Key
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
        modelos_encontrados = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                modelos_encontrados.append(m.name.replace("models/", ""))
        
        modelo_final = next((m for m in modelos_encontrados if "flash" in m), None) or modelos_encontrados[0]
        
        model = genai.GenerativeModel(modelo_final)
        prompt = f"Eres un experto técnico de TECNI HOME. Analiza: Estado {estado}, Baja {baja}°C, Alta {alta}°C. Dame diagnóstico breve, qué revisar y por qué."
        
        response = model.generate_content(prompt)
        return f"*(Usando: {modelo_final})*\n\n{response.text}"
    except Exception as e:
        return f"Error: {str(e)}"

def obtener_datos():
    try:
        respuesta = requests.get(FIREBASE_URL)
        return respuesta.json() if respuesta.status_code == 200 else None
    except:
        return None

# --- EJECUCIÓN PRINCIPAL ---
if 'estado_anterior' not in st.session_state:
    st.session_state.estado_anterior = "INICIAL"

datos = obtener_datos()

if datos:
    tuberia_baja = datos.get("tuberia_baja", 0.0)
    tuberia_alta = datos.get("tuberia_alta", 0.0)
    estado_sistema = datos.get("estado_equipo", "Esperando datos...")

    col1, col2 = st.columns(2)
    col1.metric("Tubería Baja", f"{tuberia_baja} °C")
    col2.metric("Tubería Alta", f"{tuberia_alta} °C")
    
    st.write(f"### Estado: **{estado_sistema}**")
    
    if "CODIGO" in estado_sistema:
        st.error(f"⚠️ {estado_sistema}")
        
        # Lógica de aviso único
        if st.session_state.estado_anterior != estado_sistema:
            enviar_telegram(f"🚨 ALERTA TECNI HOME: {estado_sistema}. Diagnóstico: {APP_URL}")
            st.session_state.estado_anterior = estado_sistema
            
        if st.button("💡 Analizar Falla con IA"):
            with st.spinner("Consultando al experto..."):
                st.info(analizar_falla_con_ia(tuberia_baja, tuberia_alta, estado_sistema))
        
    elif "OPERATIVO" in estado_sistema:
        st.success("✅ Sistema operando correctamente.")
        st.session_state.estado_anterior = estado_sistema
    else:
        st.warning(f"ℹ️ {estado_sistema}")
        st.session_state.estado_anterior = estado_sistema
else:
    st.info("Esperando comunicación...")

if st.button("Actualizar"):
    st.rerun()
