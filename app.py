import streamlit as st
import requests
import random
import folium
import os
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from twilio.rest import Client

# --- CONFIGURACIÓN INICIAL ---
geolocator = Nominatim(user_agent="agtech_brain_final_v2")
st.set_page_config(page_title="AgTech Brain - Sistema de Gestión", layout="wide")

# --- LÓGICA DE INTELIGENCIA Y FUNCIONES ---
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

def enviar_whatsapp_reporte(u, clima, humedad, msg_ia):
    try:
        account_sid = st.secrets["TWILIO_ACCOUNT_SID"]
        auth_token = st.secrets["TWILIO_AUTH_TOKEN"]
        client = Client(account_sid, auth_token)
        cuerpo = f"🌱 *REPORTE AGTECH*\nUbicación: {u['addr']}\nTemp: {clima['temp']}°C\nHumedad: {humedad}%\nIA: {msg_ia}"
        client.messages.create(
            from_='whatsapp:+14155238886',
            body=cuerpo,
            to=f'whatsapp:{st.secrets["MY_PHONE_NUMBER"]}'
        )
        return True
    except: return False

# --- CONTROL DE SESIÓN ---
if 'registrado' not in st.session_state:
    st.session_state.registrado = False

# --- PÁGINA DE REGISTRO ---
if not st.session_state.registrado:
    st.title("🚜 Bienvenido a AgTech Brain")
    with st.form("registro"):
        nombre = st.text_input("Nombre del Administrador")
        calle = st.text_input("Dirección del Predio (Calle, Número, Comuna)")
        hectareas = st.number_input("Hectáreas", min_value=0.1)
        if st.form_submit_button("Configurar Sistema"):
            location = geolocator.geocode(f"{calle}, Chile")
            if location:
                st.session_state.user_data = {
                    "nombre": nombre, "hectareas": hectareas,
                    "lat": location.latitude, "lon": location.longitude, "addr": location.address
                }
                st.session_state.registrado = True
                st.rerun()
            else: st.error("No se encontró la dirección.")

# --- APP PRINCIPAL (CON MENÚ) ---
else:
    u = st.session_state.user_data
    
    # --- MENÚ LATERAL (SIDEBAR) ---
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2942/2942940.png", width=100)
    st.sidebar.title("AgTech Menu")
    opcion = st.sidebar.radio("Seleccione una categoría:", 
                              ["📊 Dashboard General", "🛸 Despliegue del Dron", "⚙️ Configuración"])

    # --- CATEGORÍA 1: DASHBOARD ---
    if opcion == "📊 Dashboard General":
        st.title(f"🌱 Dashboard: {u['nombre']}")
        
        # Mapa Satelital
        m = folium.Map(location=[u['lat'], u['lon']], zoom_start=17)
        folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                         attr='Esri', name='Satellite').add_to(m)
        st_folium(m, width=1100, height=400)

        # Clima y Métricas
        cerebro = AgBrain(u['lat'], u['lon'])
        clima = cerebro.get_weather()
        humedad = random.randint(20, 45)
        
        col1, col2, col3 = st.columns(3)
        if clima:
            col1.metric("Temperatura", f"{clima['temp']} °C")
            col2.metric("Humedad Suelo", f"{humedad} %")
            col3.metric("ET0 (Evaporación)", f"{clima['et0']} mm")

        st.markdown("---")
        if st.button("📲 Enviar Reporte a WhatsApp"):
            if enviar_whatsapp_reporte(u, clima, humedad, "Salud Óptima"):
                st.success("Reporte enviado.")
            else: st.error("Error al enviar. Revisa los Secrets.")

    # --- CATEGORÍA 2: DESPLIEGUE DEL DRON ---
    elif opcion == "🛸 Despliegue del Dron":
        st.title("🛸 Centro de Control de Drones")
        st.subheader("Simulación de Despliegue en Tiempo Real")
        
        col_dron1, col_dron2 = st.columns(2)
        
        with col_dron1:
            st.info("Parámetros de Vuelo")
            bateria = st.progress(85, text="Batería del Dron: 85%")
            st.write(f"📍 Punto de Inicio: {u['addr']}")
            st.write("📡 Estado de Señal: Fuerte (GPS Fix)")
            
            if st.button("🚀 Iniciar Despegue"):
                with st.spinner("Sincronizando motores y GPS..."):
                    import time
                    time.sleep(2)
                    st.success("¡Dron en el aire! Iniciando patrullaje de hectáreas.")
        
        with col_dron2:
            st.warning("Cámara Térmica / NDVI")
            # Simulación de una imagen NDVI (salud de plantas)
            st.image("https://www.scielo.org.mx/img/revistas/remexca/v10n5//2007-0934-remexca-10-05-1153-gf2.jpg", 
                     caption="Mapa de salud (NDVI) generado por el dron")

    # --- CATEGORÍA 3: CONFIGURACIÓN ---
    elif opcion == "⚙️ Configuración":
        st.title("⚙️ Configuración del Sistema")
        st.write(f"Administrador: {u['nombre']}")
        if st.button("🔴 Cerrar Sesión / Cambiar Terreno"):
            st.session_state.registrado = False
            st.rerun()
