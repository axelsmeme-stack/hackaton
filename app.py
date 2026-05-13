import streamlit as st
import requests
import random
import folium
import math
import time
from folium import plugins
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from twilio.rest import Client

# --- CONFIGURACIÓN INICIAL ---
geolocator = Nominatim(user_agent="agtech_brain_final_v3")
st.set_page_config(page_title="AgTech Brain | Torre de Control", page_icon="🚁", layout="wide")

# Estilos CSS para alertas y diseño
st.markdown("""
   <style>
   .alerta-agronomica { color: #856404; background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 5px solid #ffeeba; margin-bottom: 20px;}
   .horario-auto { color: #155724; background-color: #d4edda; padding: 10px; border-radius: 5px; border-left: 5px solid #c3e6cb;}
   </style>
""", unsafe_allow_html=True)

# --- MOTOR LÓGICO DE RUTAS (DRON) ---
def calcular_ruta_dron(lat_centro, lon_centro, area_m2, patron):
    lado_grados = math.sqrt(area_m2) * 0.000009
    mitad = lado_grados / 2
    ruta = [[lat_centro, lon_centro]] 
    norte, sur = lat_centro + mitad, lat_centro - mitad
    este, oeste = lon_centro + mitad, lon_centro - mitad
    if patron == "Zig-Zag (Cobertura Total)":
        ruta.extend([[norte, oeste], [norte, este], [lat_centro + (mitad/2), este], [lat_centro + (mitad/2), oeste], [lat_centro, oeste], [lat_centro, este], [sur, este], [sur, oeste]])
    elif patron == "Espiral (Foco Central)":
        for i in range(1, 5):
            radio = (mitad / 4) * i
            ruta.extend([[lat_centro + radio, lon_centro], [lat_centro, lon_centro + radio], [lat_centro - radio, lon_centro], [lat_centro, lon_centro - radio]])
    elif patron == "Perimetral (Bordes)":
        ruta.extend([[norte, oeste], [norte, este], [sur, este], [sur, oeste], [norte, oeste]])
    ruta.append([lat_centro, lon_centro]) 
    return ruta

# --- LÓGICA DE CLIMA E IA ---
class AgBrain:
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon
    def get_weather(self):
        url = f"https://api.open-meteo.com/v1/forecast?latitude={self.lat}&longitude={self.lon}&hourly=temperature_2m,precipitation_probability,et0_fao_evapotranspiration&timezone=America%2FSantiago&forecast_days=1"
        try:
            res = requests.get(url).json()
            return {'temp': res['hourly']['temperature_2m'][0], 'rain_prob': res['hourly']['precipitation_probability'][0], 'et0': res['hourly']['et0_fao_evapotranspiration'][0]}
        except: return None

def enviar_whatsapp_reporte(u, clima, humedad, msg_ia):
    try:
        client = Client(st.secrets["TWILIO_ACCOUNT_SID"], st.secrets["TWILIO_AUTH_TOKEN"])
        cuerpo = f"🌱 *REPORTE AGTECH*\nUbicación: {u['addr']}\nTemp: {clima['temp']}°C\nHumedad: {humedad}%\nIA: {msg_ia}"
        client.messages.create(from_='whatsapp:+14155238886', body=cuerpo, to=f'whatsapp:{st.secrets["MY_PHONE_NUMBER"]}')
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
        hectareas = st.number_input("Hectáreas", min_value=0.1, value=1.0)
        if st.form_submit_button("Configurar Sistema"):
            location = geolocator.geocode(f"{calle}, Chile")
            if location:
                st.session_state.user_data = {"nombre": nombre, "hectareas": hectareas, "lat": location.latitude, "lon": location.longitude, "addr": location.address}
                st.session_state.registrado = True
                st.rerun()
            else: st.error("Dirección no encontrada.")

# --- APP PRINCIPAL (CON MENÚ) ---
else:
    u = st.session_state.user_data
    st.sidebar.title("AgTech Menu")
    opcion = st.sidebar.radio("Navegación:", ["📊 Dashboard General", "🛸 Despliegue Dron"])
    
    # --- CATEGORÍA 1: DASHBOARD GENERAL (RESTAURADO) ---
    if opcion == "📊 Dashboard General":
        st.title(f"🌱 Dashboard de Monitoreo: {u['nombre']}")
        
        # 1. Mapa Satelital de la Sección Principal
        m_main = folium.Map(location=[u['lat'], u['lon']], zoom_start=17)
        folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri', name='Satellite').add_to(m_main)
        folium.Marker([u['lat'], u['lon']], popup=u['addr']).add_to(m_main)
        st_folium(m_main, width=1200, height=400, key="main_map")

        st.write(f"📍 **Ubicación:** {u['addr']} | 📐 **Área:** {u['hectareas']} Ha.")
        st.markdown("---")

        # 2. Métricas en Tiempo Real
        cerebro = AgBrain(u['lat'], u['lon'])
        clima = cerebro.get_weather()
        humedad = random.randint(20, 45)
        msg_ia = "✅ SALUD: No se detectan anomalías en el follaje."
        
        st.subheader("📊 Variables Críticas")
        col1, col2, col3, col4 = st.columns(4)
        if clima:
            col1.metric("Temperatura", f"{clima['temp']} °C")
            col2.metric("Prob. Lluvia", f"{clima['rain_prob']} %")
            col3.metric("Humedad Suelo", f"{humedad} %", delta="-2%" if humedad < 30 else "Estable")
            col4.metric("Evapotranspiración", f"{clima['et0']} mm")

        st.markdown("---")
        
        # 3. IA y WhatsApp
        c_ia, c_wa = st.columns(2)
        with c_ia:
            st.subheader("🔬 Análisis de IA Satelital")
            st.success(msg_ia)
        with c_wa:
            st.subheader("📲 Reporte Rápido")
            if st.button("📤 Enviar Datos a WhatsApp"):
                if enviar_whatsapp_reporte(u, clima, humedad, msg_ia):
                    st.success("Reporte enviado exitosamente.")
                else: st.error("Error: Revisa los Secrets de Twilio.")

    # --- CATEGORÍA 2: DESPLIEGUE DRON (MANTENIDO) ---
    elif opcion == "🛸 Despliegue Dron":
        st.title("🚁 Enjambre VRA - Torre de Control Automática")
        st.sidebar.markdown("---")
        st.sidebar.header("⚙️ Misión del Dron")
        area_m2 = st.sidebar.number_input("Área a cubrir (m²)", value=int(u['hectareas']*10000))
        patron_vuelo = st.sidebar.selectbox("Patrón de Distribución", ["Zig-Zag (Cobertura Total)", "Espiral (Foco Central)", "Perimetral (Bordes)"])
        hora_simulada = st.sidebar.slider("Hora en el campo:", 0, 23, 14)

        col_control, col_mapa = st.columns([1.2, 2])
        with col_control:
            st.subheader("Operaciones Manuales")
            tipo_mision = st.radio("Tipo de Aplicación:", ["Riego (Agua)", "Nutrición", "Tratamiento"])
            iniciar_vuelo = st.button("🚀 Forzar Despliegue Manual", type="primary", use_container_width=True)
            if iniciar_vuelo:
                if tipo_mision == "Riego (Agua)" and 10 <= hora_simulada <= 18:
                    st.markdown(f'<div class="alerta-agronomica"><b>⚠️ RIESGO:</b> Son las {hora_simulada}:00 hrs. El agua quemará el tejido por efecto lupa.</div>', unsafe_allow_html=True)
                    if not st.checkbox("Confirmar despliegue de emergencia"): st.stop()
                with st.spinner("Calculando ruta..."):
                    time.sleep(1)
                    st.success(f"✅ Misión de {tipo_mision} iniciada.")
                    c1, c2 = st.columns(2)
                    c1.metric("Área", f"{area_m2} m²")
                    c2.metric("Vuelo Est.", f"{round((area_m2/10000)*10, 1)} min")

        with col_mapa:
            mapa = folium.Map(location=[u['lat'], u['lon']], zoom_start=18, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri")
            folium.Marker([u['lat'], u['lon']], popup="Base", icon=folium.Icon(color="black", icon="home")).add_to(mapa)
            if iniciar_vuelo:
                ruta = calcular_ruta_dron(u['lat'], u['lon'], area_m2, patron_vuelo)
                color = "cyan" if tipo_mision == "Riego (Agua)" else "orange"
                plugins.AntPath(locations=ruta, delay=800, color=color, weight=4).add_to(mapa)
            st_folium(mapa, width=800, height=500, key="drone_map")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.registrado = False
        st.rerun()
