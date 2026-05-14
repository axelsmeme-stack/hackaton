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
geolocator = Nominatim(user_agent="agtech_brain_axel_final")
st.set_page_config(page_title="AgTech Brain | Gestión Agrícola", page_icon="🌿", layout="wide")

# --- LÓGICA DE RUTAS Y CLIMA (Se mantienen igual) ---
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

class AgBrain:
    def __init__(self, lat, lon):
        self.lat, self.lon = lat, lon
    def get_weather(self):
        url = f"https://api.open-meteo.com/v1/forecast?latitude={self.lat}&longitude={self.lon}&hourly=temperature_2m,precipitation_probability,et0_fao_evapotranspiration&timezone=America%2FSantiago&forecast_days=1"
        try:
            res = requests.get(url).json()
            return {'temp': res['hourly']['temperature_2m'][0], 'rain_prob': res['hourly']['precipitation_probability'][0], 'et0': res['hourly']['et0_fao_evapotranspiration'][0]}
        except: return None

# --- FUNCIÓN DE ENVÍO WHATSAPP (Usa st.secrets de Streamlit Cloud) ---
def enviar_whatsapp_profesional(u, clima, humedad):
    try:
        # Esto busca los datos en el panel de Secrets que configuraste en el paso anterior
        account_sid = st.secrets["TWILIO_ACCOUNT_SID"]
        auth_token = st.secrets["TWILIO_AUTH_TOKEN"]
        client = Client(account_sid, auth_token)
        
        cuerpo_mensaje = f"""
🌱 *AGTECH BRAIN - INFORME*
--------------------------
👤 *Admin:* {u['nombre']}
🚜 *Cultivo:* {u['cultivo']}
📍 *Ubicación:* {u['addr']}
🌡️ *Temp:* {clima['temp']}°C
💧 *Humedad:* {humedad}%
🌦️ *Prob. Lluvia:* {clima['rain_prob']}%
--------------------------
✅ Estado del predio verificado.
"""
        message = client.messages.create(
            from_='whatsapp:+14155238886', 
            body=cuerpo_mensaje,
            to=f'whatsapp:{st.secrets["MY_PHONE_NUMBER"]}'
        )
        return True, message.sid
    except Exception as e:
        return False, str(e)

# --- CONTROL DE SESIÓN ---
if 'registrado' not in st.session_state:
    st.session_state.registrado = False

if not st.session_state.registrado:
    st.title("🚜 Bienvenido a AgTech Brain")
    with st.form("registro_maestro"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre del Administrador")
            calle = st.text_input("Dirección del Predio (Calle, Número, Ciudad)")
        with col2:
            tipo_cultivo = st.selectbox("Tipo de Cultivo", ["Uva de Mesa", "Maíz", "Nogales", "Cerezas", "Trigo", "Otro"])
            hectareas = st.number_input("Hectáreas", min_value=0.1, value=1.0)
        if st.form_submit_button("Configurar Sistema"):
            location = geolocator.geocode(f"{calle}, Chile")
            if location:
                st.session_state.user_data = {"nombre": nombre, "hectareas": hectareas, "cultivo": tipo_cultivo, "lat": location.latitude, "lon": location.longitude, "addr": location.address}
                st.session_state.registrado = True
                st.rerun()
            else: st.error("Dirección no encontrada.")
else:
    u = st.session_state.user_data
    st.sidebar.title("AgTech Menu")
    opcion = st.sidebar.radio("Navegación:", ["📊 Dashboard General", "🛸 Despliegue Dron"])
    
    if opcion == "📊 Dashboard General":
        st.title(f"🌱 Dashboard: {u['nombre']}")
        m_main = folium.Map(location=[u['lat'], u['lon']], zoom_start=17)
        folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri', name='Satellite').add_to(m_main)
        folium.Marker([u['lat'], u['lon']], popup=f"Terreno de {u['cultivo']}").add_to(m_main)
        st_folium(m_main, width=1200, height=400, key="main_map")
        
        cerebro = AgBrain(u['lat'], u['lon'])
        clima = cerebro.get_weather()
        humedad_suelo = random.randint(18, 42)
        
        if clima:
            st.subheader("📊 Variables Críticas")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Temperatura", f"{clima['temp']} °C")
            c2.metric("Prob. Lluvia", f"{clima['rain_prob']} %")
            c3.metric("Humedad Suelo", f"{humedad_suelo} %")
            c4.metric("ET0", f"{clima['et0']} mm")

            st.markdown("---")
            st.subheader("📲 Acciones de Comunicación")
            if st.button("📤 Enviar Informe Completo a WhatsApp", type="primary"):
                with st.spinner("Enviando..."):
                    exito, detalle = enviar_whatsapp_profesional(u, clima, humedad_suelo)
                    if exito: st.success("✅ Informe enviado correctamente.")
                    else: st.error(f"❌ Error al enviar: {detalle}")

    elif opcion == "🛸 Despliegue Dron":
        st.title("🚁 Torre de Control: Operación de Drones")
        area_m2 = st.sidebar.number_input("Área (m²)", value=int(u['hectareas']*10000))
        patron_vuelo = st.sidebar.selectbox("Patrón de Movimiento", ["Zig-Zag (Cobertura Total)", "Espiral (Foco Central)", "Perimetral (Bordes)"])
        ruta_previa = calcular_ruta_dron(u['lat'], u['lon'], area_m2, patron_vuelo)
        
        col_c, col_m = st.columns([1.2, 2])
        with col_c:
            iniciar = st.button("🚀 Forzar Despliegue Manual", type="primary", use_container_width=True)
            if iniciar: st.success(f"✅ Misión iniciada sobre {u['cultivo']}.")
        with col_m:
            mapa = folium.Map(location=[u['lat'], u['lon']], zoom_start=18, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri")
            if iniciar: plugins.AntPath(locations=ruta_previa, delay=800, color="cyan", weight=4).add_to(mapa)
            else: folium.PolyLine(locations=ruta_previa, color="yellow", weight=2, dash_array='5, 10').add_to(mapa)
            st_folium(mapa, width=800, height=500, key="drone_map")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.registrado = False
        st.rerun()
