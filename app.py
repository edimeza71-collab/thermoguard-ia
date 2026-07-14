import streamlit as st
import requests
import google.generativeai as genai

# --- CONFIGURACIÓN DE CONEXIONES ---
FIREBASE_URL = "https://monitoreoia-b2097-default-rtdb.firebaseio.com/datos.json"
BOT_TOKEN = "8916674528:AAG0uHgWcg-5h4QB_BqidoNUQPyxBHZ3Ebc"
CHAT_ID = "1476571501"
APP_URL = "https://thermoguard-ia.streamlit.app"

# Configuración de la página
st.set_page_config(page_title="Panel TECNI HOME", page_icon="❄️", layout="centered")

st.title("❄️ Control de Refrigeración - TECNI HOME")
st.write("Monitoreo en tiempo real del ciclo de refrigeración.")

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
        # Extraemos la llave de los secretos de Streamlit
        clave_secreta = st.secrets["GOOGLE_API_KEY"]
        
        # Inicialización moderna recomendada por la librería de Google
        client = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            api_key=clave_secreta
        )
        
        prompt = f"""
        Eres un experto técnico de TECNI HOME. Analiza esta falla de refrigeración:
        - Estado: {estado}
        - Temp. Tubería Baja: {baja}°C
        - Temp. Tubería Alta: {alta}°C
        
        Dame un diagnóstico técnico breve y directo. ¿Qué pieza revisar primero y por qué?
        """
        
        response = client.generate_content(prompt)
        return response.text
    except Exception as error_ia:
        return f"Error al conectar con el motor de IA: {str(error_ia)}"

def obtener_datos():
    try:
        respuesta = requests.get(FIREBASE_URL)
        if respuesta.status_code == 200:
            return respuesta.json()
    except:
        st.error("Error conectando a Firebase.")
    return None

# --- EJECUCIÓN PRINCIPAL ---
datos = obtener_datos()

if datos:
    tuberia_baja = datos.get("tuberia_baja", 0.0)
    tuberia_alta = datos.get("tuberia_alta", 0.0)
    estado_sistema = datos.get("estado_equipo", "Esperando datos...")

    col1, col2 = st.columns(2)
    col1.metric(label="Tubería Baja (Succión)", value=f"{tuberia_baja} °C")
    col2.metric(label="Tubería Alta (Líquido)", value=f"{tuberia_alta} °C")
    
    st.write(f"### Estado del sistema: **{estado_sistema}**")
    
    if "CODIGO" in estado_sistema:
        st.error(f"⚠️ {estado_sistema}")
        
        # Botón para activar la IA en la web
        if st.button("💡 Analizar Falla con IA"):
            with st.spinner("Consultando al experto virtual..."):
                reporte = analizar_falla_con_ia(tuberia_baja, tuberia_alta, estado_sistema)
                st.markdown("### 🤖 Diagnóstico del Experto:")
                st.info(reporte)
        
        # Mensaje corto para Telegram
        alerta_corta = (
            f"🚨 ALERTA TECNI HOME 🚨\n"
            f"Falla: {estado_sistema}\n"
            f"T: {tuberia_baja}°C / {tuberia_alta}°C\n"
            f"🔗 Diagnóstico: {APP_URL}"
        )
        enviar_telegram(alerta_corta)
        
    elif "OPERATIVO" in estado_sistema:
        st.success("✅ El ciclo de refrigeración está operando correctamente.")
    else:
        st.warning(f"ℹ️ {estado_sistema}")
else:
    st.info("Esperando comunicación con el ESP32...")
    
st.write("---")
if st.button("Actualizar Lecturas Ahora"):
    st.rerun()
