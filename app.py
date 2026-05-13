import streamlit as st
import requests
import random
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# --- CONFIGURACIÓN INICIAL ---
geolocator = Nominatim(user_agent="agtech_brain_axel")
st.set_page_config(page_title="AgTech Brain - Sistema de Monitoreo", layout="wide")

# --- LÓGICA DE INTELIGENCIA (AgBrain) ---
class AgBrain:
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def get_weather(self):
        # Consulta datos específicos según la ubicación registrada
        url = f"https://api.open-meteo.com/v1/forecast?latitude={self.lat}&longitude={self.lon}&hourly=temperature_2m,precipitation_probability,et0_fao_evapotranspiration&timezone=America%2FSantiago&forecast_days=1"
        try:
            res = requests.get(url).json()
            return {
                'temp': res['hourly']['temperature_2m'][0],
                'rain_prob': res['hourly']['precipitation_probability'][0],
                'et0': res['hourly']['et0_fao_evapotranspiration'][0]
            }
        except:
            return None

    def detect_disease_sim(self):
        # Simulación de detección de patógenos por IA
        score = random.uniform(0, 1)
        if score > 0.85:
            return "⚠️ ALERTA: Posible hongo detectado (Roya).", "error"
        return "✅ SALUD: No se detectan anomalías en el follaje.", "success"

# --- CONTROL DE ESTADO DE SESIÓN ---
if 'registrado' not in st.session_state:
    st.session_state.registrado = False

# --- PÁGINA 1: REGISTRO E IDENTIDAD ---
if not st.session_state.registrado:
    st.title("🚜 Registro de Nuevo Terreno Agrícola")
    st.markdown("Ingrese los datos del predio para configurar el monitoreo satelital y climático.")
    
    with st.form("registro_agtech"):
        nombre = st.text_input("Nombre Completo del Administrador")
        calle_direccion = st.text_input("Dirección del Domicilio/Terreno (Calle, Número, Comuna)")
        hectareas = st.number_input("Cantidad de Hectáreas", min_value=0.1, step=0.5)
        
        btn_submit = st.form_submit_button("Configurar Dashboard")
        
        if btn_submit:
            if nombre and calle_direccion:
                try:
                    # Geocodificación: Convertir texto a coordenadas reales
                    location = geolocator.geocode(f"{calle_direccion}, Chile")
                    if location:
                        st.session_state.user_data = {
                            "nombre": nombre,
                            "hectareas": hectareas,
                            "lat": location.latitude,
                            "lon": location.longitude,
                            "addr": location.address # Aquí se guarda la llave 'addr'
                        }
                        st.session_state.registrado = True
                        st.rerun()
                    else:
                        st.error("No se pudo encontrar la ubicación. Intente ser más específico (ej: agregar la comuna).")
                except:
                    st.error("Error de conexión con el servicio de mapas. Intente nuevamente.")
            else:
                st.warning("Por favor, complete todos los campos.")

# --- PÁGINA 2: DASHBOARD PRINCIPAL ---
else:
    # CORRECCIÓN DE SEGURIDAD (KeyError)
    u = st.session_state.user_data
    nombre_user = u.get('nombre', 'Usuario')
    direccion_user = u.get('addr', 'Dirección no disponible')
    hectareas_user = u.get('hectareas', 0.0)
    lat_user = u.get('lat', -33.45)
    lon_user = u.get('lon', -70.66)

    # Instanciar el "Cerebro" con las coordenadas del usuario
    cerebro = AgBrain(lat_user, lon_user)
    clima = cerebro.get_weather()
    msg_ia, tipo_ia = cerebro.detect_disease_sim()

    st.title(f"🌱 Dashboard: Terreno de {nombre_user}")
    
    # Visualización Satelital (Folium)
    m = folium.Map(location=[lat_user, lon_user], zoom_start=17)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri', name='Satellite'
    ).add_to(m)
    folium.Marker([lat_user, lon_user], popup=direccion_user).add_to(m)
    
    st_folium(m, width=1200, height=450)

    # Información Base
    st.write(f"📍 **Dirección registrada:** {direccion_user}")
    st.write(f"📐 **Superficie:** {hectareas_user} Hectáreas")
    st.markdown("---")

    # Métricas Críticas (Lo que recuperamos de la versión anterior)
    st.subheader("📊 Valores Importantes de Monitoreo")
    c1, c2, c3, c4 = st.columns(4)
    
    humedad_simulada = random.randint(15, 50)
    
    if clima:
        c1.metric("Temperatura", f"{clima['temp']} °C")
        c2.metric("Prob. Lluvia", f"{clima['rain_prob']} %")
        c3.metric("Humedad Suelo", f"{humedad_simulada} %", delta="-3%" if humedad_simulada < 30 else "Estable")
        c4.metric("Evapotranspiración", f"{clima['et0']} mm")

    st.markdown("---")

    # Análisis de Decisiones
    col_ia, col_riego = st.columns(2)
    
    with col_ia:
        st.subheader("🔬 Análisis de IA")
        if tipo_ia == "error":
            st.error(msg_ia)
        else:
            st.success(msg_ia)

    with col_riego:
        st.subheader("🚜 Recomendación de Riego")
        # Lógica: Si la humedad es baja y no va a llover, regar.
        if humedad_simulada < 30 and (clima['rain_prob'] if clima else 0) < 40:
            st.warning("RECOMENDACIÓN: Activar sistema de riego (Humedad Crítica).")
        else:
            st.success("ESTADO: Nivel de agua óptimo para el cultivo.")

    # Botón para reiniciar
    if st.sidebar.button("Cerrar Sesión / Nuevo Registro"):
        st.session_state.registrado = False
        st.rerun()
