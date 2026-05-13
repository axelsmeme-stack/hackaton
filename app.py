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
geolocator = Nominatim(user_agent="agtech_brain_final")
st.set_page_config(page_title="AgTech Brain | Torre de Control", page_icon="🚁", layout="wide")

# Estilos CSS para alertas profesionales
st.markdown("""
   <style>
   .alerta-agronomica { color: #856404; background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 5px solid #ffeeba; margin-bottom: 20px;}
   .horario-auto { color: #155724; background-color: #d4edda; padding: 10px; border-radius: 5px; border-left: 5px solid #c3e6cb;}
   </style>
""", unsafe_allow_html=True)

# --- MOTOR LÓGICO DE RUTAS ---
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

# --- CONTROL DE SESIÓN ---
if 'registrado' not in st.session_state:
    st.session_state.registrado = False

# --- PÁGINA DE REGISTRO ---
if not st.session_state.registrado:
    st.title("🚜 Bienvenido a AgTech Brain")
    with st.form("registro"):
        nombre = st.text_input("Nombre del Administrador")
        calle = st.text_input("Dirección (Calle, Número, Comuna)")
        hectareas = st.number_input("Hectáreas", min_value=0.1, value=1.0)
        if st.form_submit_button("Configurar Sistema"):
            location = geolocator.geocode(f"{calle}, Chile")
            if location:
                st.session_state.user_data = {
                    "nombre": nombre, "hectareas": hectareas,
                    "lat": location.latitude, "lon": location.longitude, "addr": location.address
                }
                st.session_state.registrado = True
                st.rerun()
            else: st.error("Dirección no encontrada.")

# --- APP PRINCIPAL (CON MENÚ) ---
else:
    u = st.session_state.user_data
    
    # Barra Lateral
    st.sidebar.title("AgTech Menu")
    opcion = st.sidebar.radio("Navegación:", ["📊 Dashboard General", "🛸 Despliegue Dron"])
    
    if opcion == "📊 Dashboard General":
        st.title(f"🌱 Dashboard: {u['nombre']}")
        # (Aquí iría tu código de métricas y mapa satelital que ya tenemos listo)
        st.info("Pestaña de monitoreo satelital y reporte de WhatsApp.")
        if st.sidebar.button("Cerrar Sesión"):
            st.session_state.registrado = False
            st.rerun()

    # --- CATEGORÍA: DESPLIEGUE DRON (Integración solicitada) ---
    elif opcion == "🛸 Despliegue Dron":
        st.title("🚁 Enjambre VRA - Torre de Control Automática")
        
        # Panel de Configuración en Sidebar
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
                # Lógica de Riesgo Agronómico
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
            
            st_folium(mapa, width=800, height=500)
