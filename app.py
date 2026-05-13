import streamlit as st
import requests
import random
import pandas as pd
import folium
from streamlit_folium import st_folium

# --- CLASE AGBRAIN (Tu lógica original integrada) ---
class AgBrain:
    def __init__(self, crop_type, moisture_threshold):
        self.crop_type = crop_type
        self.moisture_threshold = moisture_threshold 

    def get_weather(self):
        url = "https://api.open-meteo.com/v1/forecast?latitude=-33.45&longitude=-70.66&hourly=temperature_2m,precipitation_probability,et0_fao_evapotranspiration&timezone=America%2FSantiago&forecast_days=1"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'temp': data['hourly']['temperature_2m'][0],
                    'rain_prob': data['hourly']['precipitation_probability'][0],
                    'et0': data['hourly']['et0_fao_evapotranspiration'][0]
                }
            return None
        except:
            return None

    def detect_disease_sim(self):
        health_score = random.uniform(0, 1)
        if health_score > 0.85:
            return "⚠️ ALERTA: Posible hongo detectado (Roya).", "error"
        return "✅ SALUD: No se detectan anomalías.", "success"

# --- CONFIGURACIÓN DE PÁGINA STREAMLIT ---
st.set_page_config(page_title="AgTech Brain - Chile", layout="wide")

st.title("🌱 AgTech Brain: Monitoreo Inteligente")
st.markdown("---")

# --- BARRA LATERAL (ENTRADAS) ---
st.sidebar.header("Configuración del Cultivo")
crop = st.sidebar.selectbox("Tipo de Cultivo", ["Tomate", "Maíz", "Trigo", "Uva"])
threshold = st.sidebar.slider("Umbral de Humedad Crítica (%)", 0, 100, 30)
moisture_sensor = st.sidebar.number_input("Humedad Actual del Sensor (%)", 0, 100, 25)

cerebro = AgBrain(crop, threshold)
weather = cerebro.get_weather()
disease_msg, disease_type = cerebro.detect_disease_sim()

# --- CUERPO PRINCIPAL ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📊 Estado en Tiempo Real")
    
    # Métricas Clave (Open-Meteo)
    if weather:
        m1, m2, m3 = st.columns(3)
        m1.metric("Temperatura", f"{weather['temp']} °C")
        m2.metric("Prob. Lluvia", f"{weather['rain_prob']} %")
        m3.metric("Evapotranspiración", f"{weather['et0']} mm")
    
    # Análisis de IA y Decisión
    st.info(f"**Cultivo:** {crop} | **Humedad:** {moisture_sensor}%")
    
    if disease_type == "error":
        st.error(disease_msg)
    else:
        st.success(disease_msg)

    # Lógica de decisión
    if moisture_sensor < threshold:
        if weather and weather['rain_prob'] > 60:
            st.warning("🚜 DECISIÓN: ESPERAR (Lluvia inminente según Open-Meteo).")
            decision_text = "Esperar por lluvia"
        else:
            st.error(f"💧 DECISIÓN: REGAR (Humedad baja + ET0 de {weather['et0']}mm).")
            decision_text = "Iniciar riego"
    else:
        st.success("✅ DECISIÓN: ESTADO ÓPTIMO (No requiere riego).")
        decision_text = "Todo en orden"

with col2:
    st.subheader("🗺️ Vista Satelital del Terreno")
    # Mapa de Santiago (puedes cambiar lat/lon por las del campo real)
    m = folium.Map(location=[-33.45, -70.66], zoom_start=15, tiles="CartoDB positron")
    # Capa satelital opcional (usando Esri)
    folium.TileLayer(
        tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr = 'Esri',
        name = 'Satellite',
        overlay = False,
        control = True
    ).add_to(m)
    st_folium(m, width=700, height=300)

st.markdown("---")

# --- SECCIÓN WHATSAPP ---
st.subheader("📱 Reporte Diario WhatsApp")
reporte = f"""*Reporte AgTech {crop}* 
---------------------------
📍 Estado: {decision_text}
🌡️ Temp: {weather['temp']}°C
💧 Humedad: {moisture_sensor}%
🔬 IA: {disease_msg}
---------------------------"""

st.code(reporte, language="text")
if st.button("Enviar Reporte a WhatsApp"):
    # Link directo a WhatsApp (Sustituir por integración API Twilio en producción)
    st.markdown(f"[Haz clic aquí para enviar el informe](https://wa.me/?text={requests.utils.quote(reporte)})")
