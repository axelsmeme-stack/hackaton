import streamlit as st
import requests
import random
import folium
import os
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from twilio.rest import Client # Esta es la línea 8 que daba el error

# --- CONFIGURACIÓN INICIAL ---
geolocator = Nominatim(user_agent="agtech_brain_axel_final")
st.set_page_config(page_title="AgTech Brain - Monitoreo Profesional", layout="wide")

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
        except:
            return None

    def detect_disease_sim(self):
        score = random.uniform(0, 1)
        if score > 0.85:
            return "⚠️ ALERTA: Posible hongo detectado (Roya).", "error"
        return "✅ SALUD: No se detectan anomalías en el follaje.", "success"

# --- FUNCIÓN PARA ENVIAR WHATSAPP (Twilio) ---
def enviar_whatsapp_reporte(datos_usuario, clima, humedad, msg_ia):
    try:
        account_sid = st.secrets["TWILIO_ACCOUNT_SID"]
        auth_token = st.secrets["TWILIO_AUTH_TOKEN"]
        client = Client(account_sid, auth_token)

        cuerpo = f"""
🌱 *REPORTE AGTECH BAJO DEMANDA* 🚜
---------------------------
👤 Administrador: {datos_usuario['nombre']}
📍 Ubicación: {datos_usuario['addr']}
📐 Superficie: {datos_usuario['hectareas']} Ha.
---------------------------
🌡️ Temp: {clima['temp']}°C
💧 Humedad Suelo: {humedad}%
🌦️ Prob. Lluvia: {clima['rain_prob']}%
🌾 IA: {msg_ia}
---------------------------
✅ Acción: Reporte generado desde Dashboard."""

        message = client.messages.create(
            from_='whatsapp:+14155238886', 
            body=cuerpo,
            to=f'whatsapp:{st.secrets["MY_PHONE_NUMBER"]}'
        )
        return True, message.sid
    except Exception as e:
        return False, str(e)

# --- CONTROL DE SESIÓN ---
if 'registrado' not in st.session_state:
    st.session_state.registrado = False

# --- PÁGINA 1: REGISTRO ---
if not st.session_state.registrado:
    st.title("🚜 Registro de Nuevo Terreno Agrícola")
    with st.form("registro_agtech"):
        nombre = st.text_input("Nombre Completo del Administrador")
        calle_direccion = st.text_input("Dirección (Calle, Número, Comuna)")
        hectareas = st.number_input("Cantidad de Hectáreas", min_value=0.1, step=0.5)
        
        if st.form_submit_button("Configurar Dashboard"):
            if nombre and calle_direccion:
                try:
                    location = geolocator.geocode(f"{calle_direccion}, Chile")
                    if location:
                        st.session_state.user_data = {
                            "nombre": nombre, "hectareas": hectareas,
                            "lat": location.latitude, "lon": location.longitude,
                            "addr": location.address
                        }
                        st.session_state.registrado = True
                        st.rerun()
                    else:
                        st.error("Dirección no encontrada. Intente ser más específico.")
                except:
                    st.error("Error de conexión. Intente nuevamente.")
            else:
                st.warning("Complete todos los campos.")

# --- PÁGINA 2: DASHBOARD ---
else:
    u = st.session_state.user_data
    cerebro = AgBrain(u.get('lat', -33.45), u.get('lon', -70.66))
    clima = cerebro.get_weather()
    msg_ia, tipo_ia = cerebro.detect_disease_sim()
    humedad_sim = random.randint(15, 50)

    st.title(f"🌱 Dashboard: Terreno de {u.get('nombre', 'Usuario')}")
    
    m = folium.Map(location=[u.get('lat', -33.45), u.get('lon', -70.66)], zoom_start=17)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri', name='Satellite'
    ).add_to(m)
    folium.Marker([u.get('lat', -33.45), u.get('lon', -70.66)], popup=u.get('addr')).add_to(m)
    st_folium(m, width=1200, height=450)

    st.write(f"📍 **Dirección registrada:** {u.get('addr', 'No disponible')}")
    st.write(f"📐 **Superficie:** {u.get('hectareas', 0.0)} Hectáreas")
    st.markdown("---")

    st.subheader("📊 Valores Importantes de Monitoreo")
    c1, c2, c3, c4 = st.columns(4)
    if clima:
        c1.metric("Temperatura", f"{clima['temp']} °C")
        c2.metric("Prob. Lluvia", f"{clima['rain_prob']} %")
        c3.metric("Humedad Suelo", f"{humedad_sim} %", delta="-3%" if humedad_sim < 30 else "Estable")
        c4.metric("Evapotranspiración", f"{clima['et0']} mm")

    st.markdown("---")
    col_ia, col_riego = st.columns(2)
    with col_ia:
        st.subheader("🔬 Análisis de IA")
        if tipo_ia == "error": st.error(msg_ia)
        else: st.success(msg_ia)

    with col_riego:
        st.subheader("🚜 Recomendación de Riego")
        if humedad_sim < 30 and (clima['rain_prob'] if clima else 0) < 40:
            st.warning("RECOMENDACIÓN: Activar sistema de riego.")
        else:
            st.success("ESTADO: Nivel de agua óptimo.")

    st.markdown("---")
    st.subheader("📲 Notificaciones en Tiempo Real")
    if st.button("📤 Enviar Reporte Actual a WhatsApp"):
        with st.spinner("Enviando reporte..."):
            exito, resultado = enviar_whatsapp_reporte(u, clima, humedad_sim, msg_ia)
            if exito:
                st.success(f"✅ Reporte enviado exitosamente.")
            else:
                st.error(f"❌ Error: {resultado}")

    if st.sidebar.button("Cerrar Sesión / Nuevo Registro"):
        st.session_state.registrado = False
        st.rerun()
