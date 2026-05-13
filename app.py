import streamlit as st
import requests
import random
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# Configuración inicial
geolocator = Nominatim(user_agent="agtech_brain_final")
st.set_page_config(page_title="AgTech Brain - Monitoreo", layout="wide")

# --- LÓGICA DE INTELIGENCIA (AgBrain) ---
class AgBrain:
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def get_weather(self):
        url = f"https://api.open-meteo.com/v1/forecast?latitude={self.lat}&longitude={self.lon}&hourly=temperature_2m,precipitation_probability,et0_fao_evapotranspiration&timezone=America%2FSantiago&forecast_days=1"
        try:
            res = requests.get(url).json()
            return {
                'temp': res['hourly']['temperature_2m'][0],
                'rain_prob': res['hourly']['precipitation_probability'][0],
                'et0': res['hourly']['et0_fao_evapotranspiration'][0]
            }
        except: return None

    def detect_disease_sim(self):
        score = random.uniform(0, 1)
        if score > 0.85:
            return "⚠️ ALERTA: Posible hongo detectado (Roya).", "error"
        return "✅ SALUD: No se detectan anomalías.", "success"

# --- CONTROL DE SESIÓN ---
if 'registrado' not in st.session_state:
    st.session_state.registrado = False

# --- PÁGINA 1: REGISTRO ---
if not st.session_state.registrado:
    st.title("🚜 Registro de Terreno Agrícola")
    with st.form("registro"):
        nombre = st.text_input("Nombre del Administrador")
        calle = st.text_input("Dirección (Calle, Número, Comuna)")
        hectareas = st.number_input("Hectáreas", min_value=0.1)
        if st.form_submit_button("Configurar Dashboard"):
            loc = geolocator.geocode(f"{calle}, Chile")
            if loc:
                st.session_state.user_data = {
                    "nombre": nombre, "hectareas": hectareas,
                    "lat": loc.latitude, "lon": loc.longitude, "addr": loc.address
                }
                st.session_state.registrado = True
                st.rerun()
            else:
                st.error("Dirección no encontrada.")

# --- PÁGINA 2: DASHBOARD (Lo que ves en image_dadb3c.jpg pero con datos) ---
else:
    data = st.session_state.user_data
    cerebro = AgBrain(data['lat'], data['lon'])
    clima = cerebro.get_weather()
    msg_ia, tipo_ia = cerebro.detect_disease_sim()

    st.title(f"🌱 Dashboard: Terreno de {data['nombre']}")
    
    # Fila 1: Mapa Satelital
    m = folium.Map(location=[data['lat'], data['lon']], zoom_start=17)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri', name='Satelital'
    ).add_to(m)
    folium.Marker([data['lat'], data['lon']], popup="Tu Terreno").add_to(m)
    st_folium(m, width=1200, height=400)

    # Fila 2: Información de Ubicación
    st.write(f"📍 **Dirección:** {data['addr']}")
    st.write(f"📐 **Superficie:** {data['hectareas']} Hectáreas")
    st.markdown("---")

    # Fila 3: VALORES IMPORTANTES (Lo que se había borrado)
    st.subheader("📊 Métricas de Monitoreo Crítico")
    col1, col2, col3, col4 = st.columns(4)
    
    # Simulamos sensor de humedad para la demo
    humedad_actual = random.randint(20, 45) 
    
    if clima:
        col1.metric("Temperatura", f"{clima['temp']} °C")
        col2.metric("Prob. Lluvia", f"{clima['rain_prob']} %")
        col3.metric("Humedad Suelo", f"{humedad_actual} %", "-5%" if humedad_actual < 30 else "")
        col4.metric("Evapotranspiración", f"{clima['et0']} mm")

    # Fila 4: IA y Decisiones
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔬 Análisis de IA")
        if tipo_ia == "error": st.error(msg_ia)
        else: st.success(msg_ia)
    
    with c2:
        st.subheader("🚜 Decisión de Riego")
        if humedad_actual < 30 and clima['rain_prob'] < 50:
            st.error("ACCIÓN: Iniciar Riego Inmediato")
        else:
            st.success("ESTADO: Óptimo (No requiere riego)")

    if st.sidebar.button("Cerrar Sesión / Nuevo Registro"):
        st.session_state.registrado = False
        st.rerun()
