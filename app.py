import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# Configuración del geocodificador
geolocator = Nominatim(user_agent="agtech_brain_chile")

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="AgTech Brain", layout="wide")

if 'registrado' not in st.session_state:
    st.session_state.registrado = False

# --- PÁGINA 1: REGISTRO POR DIRECCIÓN ---
if not st.session_state.registrado:
    st.title("🚜 Registro de Nuevo Terreno Agrícola")
    
    with st.form("registro_direccion"):
        nombre = st.text_input("Nombre Completo del Administrador")
        hectareas = st.number_input("Cantidad de Hectáreas", min_value=0.1)
        
        st.markdown("### Ubicación del Domicilio")
        calle_num = st.text_input("Calle y Número (ej: Av. Vicuña Mackenna 4860)")
        comuna = st.text_input("Población / Comuna", value="Santiago")
        ciudad = "Chile"
        
        btn_registro = st.form_submit_button("Configurar Monitoreo")
        
        if btn_registro:
            direccion_completa = f"{calle_num}, {comuna}, {ciudad}"
            try:
                # Convertimos dirección a coordenadas
                location = geolocator.geocode(direccion_completa)
                if location:
                    st.session_state.registrado = True
                    st.session_state.user_data = {
                        "nombre": nombre,
                        "hectareas": hectareas,
                        "direccion": direccion_completa,
                        "lat": location.latitude,
                        "lon": location.longitude
                    }
                    st.success(f"Ubicación encontrada: {location.address}")
                    st.rerun()
                else:
                    st.error("No pudimos encontrar esa dirección. Intenta ser más específico.")
            except Exception as e:
                st.error("Error al conectar con el servicio de mapas.")

# --- PÁGINA 2: DASHBOARD DINÁMICO ---
else:
    u = st.session_state.user_data
    st.title(f"🌱 Dashboard: Terreno de {u['nombre']}")
    
    # Aquí insertas tu lógica anterior de clima usando u['lat'] y u['lon']
    # El mapa satelital se centrará automáticamente:
    m = folium.Map(location=[u['lat'], u['lon']], zoom_start=17)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri', name='Satellite'
    ).add_to(m)
    folium.Marker([u['lat'], u['lon']], popup=u['direccion']).add_to(m)
    
    st_folium(m, width=1000, height=400)
    
    # Mostrar valores importantes
    st.write(f"**Dirección registrada:** {u['direccion']}")
    st.write(f"**Superficie:** {u['hectareas']} Hectáreas")
