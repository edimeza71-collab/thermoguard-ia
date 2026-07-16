import streamlit as st
import requests
import time
import pandas as pd
import google.generativeai as genai

# --- CONFIGURACIÓN DE CONEXIONES ---
FIREBASE_URL = "https://monitoreoia-b2097-default-rtdb.firebaseio.com/datos.json"
BOT_TOKEN = "8916674528:AAG0uHgWcg-5h4QB_BqidoNUQPyxBHZ3Ebc"
CHAT_ID = "1476571501"
APP_URL = "https://thermoguard-ia-8tnwql6ndqvxzbebelhdvy.streamlit.app"

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
st.set_page_config(page_title="Panel TermoGuardIA", page_icon="❄️", layout="centered")

st.title("❄️ Control de Refrigeración - TermoGuardIA")

# --- FUNCIONES ---
def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try: 
        requests.post(url, json={"chat_id": CHAT_ID, "text": mensaje})
    except: 
        pass

def analizar_falla_con_ia(baja, alta, estado):
    try:
        modelos = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        modelo_final = next((m for m in modelos if "flash" in m), modelos[0])
        model = genai.GenerativeModel(modelo_final)
        prompt = f"Experto TERMOGUARDIA. Estado: {estado}. Baja: {baja}°C, Alta: {alta}°C. ¿Qué revisar de forma directa?"
        return model.generate_content(prompt).text
    except Exception as e: 
        return f"Error IA: {str(e)}"

def obtener_datos():
    try:
        resp = requests.get(FIREBASE_URL)
        return resp.json() if resp.status_code == 200 else None
    except: 
        return None

# --- EJECUCIÓN PRINCIPAL ---
if 'estado_anterior' not in st.session_state: 
    st.session_state.estado_anterior = ""

datos = obtener_datos()

if datos:
    # 1. Leer los datos de Firebase
    tuberia_baja = datos.get("tuberia_baja", 0.0)
    tuberia_alta = datos.get("tuberia_alta", 0.0)
    estado_sistema = datos.get("estado_equipo", "Esperando datos...")
    ultimo_latido = datos.get("last_seen", 0)

    # 2. Mostrar los números principales
    col1, col2 = st.columns(2)
    col1.metric("Tubería Baja", f"{tuberia_baja} °C")
    col2.metric("Tubería Alta", f"{tuberia_alta} °C")
    st.write(f"### Estado: **{estado_sistema}**")
    
    # --- 3. GRÁFICAS Y COMPORTAMIENTO VISUAL ---
    st.divider()
    st.subheader("📊 Comportamiento de los Sensores")

    if 'historial_baja' not in st.session_state:
        st.session_state.historial_baja = []
    if 'historial_alta' not in st.session_state:
        st.session_state.historial_alta = []

    st.session_state.historial_baja.append(tuberia_baja)
    st.session_state.historial_alta.append(tuberia_alta)

    if len(st.session_state.historial_baja) > 50:
        st.session_state.historial_baja.pop(0)
        st.session_state.historial_alta.pop(0)

    df_grafica = pd.DataFrame({
        'Tubería Baja': st.session_state.historial_baja,
        'Tubería Alta': st.session_state.historial_alta
    })
    st.line_chart(df_grafica, color=["#00BFFF", "#FF4500"])
    st.divider()
    # -------------------------------------------
    
    # 4. Manejo inteligente de estados para el Dashboard
    if estado_sistema != st.session_state.estado_anterior:
        if "REINICIADO" in estado_sistema:
            enviar_telegram(f"⚡ Aviso TermoGuardIA: El sistema se ha reiniciado (posible corte eléctrico).")
        st.session_state.estado_anterior = estado_sistema

    if "CODIGO" in estado_sistema:
        st.error(f"⚠️ {estado_sistema}")
        if st.button("💡 Analizar Falla con IA"):
            with st.spinner("Consultando..."): 
                st.info(analizar_falla_con_ia(tuberia_baja, tuberia_alta, estado_sistema))
    elif "REINICIADO" in estado_sistema:
        st.info("ℹ️ Sistema recién encendido. Esperando estabilización de lecturas...")
    elif "OPERATIVO" in estado_sistema:
        st.success("✅ Sistema operando correctamente.")
    else:
        st.warning(f"ℹ️ {estado_sistema}")

    # --- 5. MOTOR CENTINELA (VIGILANCIA WI-FI/LUZ) ---
    if 'latido_anterior' not in st.session_state:
        st.session_state.latido_anterior = ultimo_latido
        st.session_state.tiempo_ultima_lectura = time.time()
        st.session_state.alerta_enviada = False

    if ultimo_latido != st.session_state.latido_anterior:
        # El Arduino sigue enviando datos frescos
        st.session_state.latido_anterior = ultimo_latido
        st.session_state.tiempo_ultima_lectura = time.time()
        st.session_state.alerta_enviada = False
    else:
        # El latido se congeló
        tiempo_desconectado = time.time() - st.session_state.tiempo_ultima_lectura
        if tiempo_desconectado > 120:  # 120 segundos = 2 minutos
            st.error("⚠️ PÉRDIDA DE COMUNICACIÓN CON EL EQUIPO (Wi-Fi o Energía)")
            if not st.session_state.alerta_enviada:
                enviar_telegram("🚨 ALERTA ThermoGuard IA 🚨\n\n⚠️ EQUIPO DESCONECTADO ⚠️\nSe ha perdido la comunicación por Wi-Fi o falta de energía eléctrica en el sitio.")
                st.session_state.alerta_enviada = True
    # ------------------------------------------------

else:
    st.info("Esperando comunicación...")

# --- ACTUALIZACIÓN AUTOMÁTICA ---
time.sleep(15) # Espera 15 segundos (el mismo tiempo de tu Arduino)
st.rerun()     # Vuelve a cargar la página sola
