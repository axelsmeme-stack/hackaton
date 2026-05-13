import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="AgTech Brain - Registro", layout="wide")

# Inicializar estado de sesión para el registro
if 'registrado' not in st.session_state:
    st.session_state.registrado = False

# --- PÁGINA 1: REGISTRO E IDENTIDAD ---
if not st.session_state.registrado:
    st.title("🚜 Registro de Nuevo Terreno Agrícola")
    st.markdown("Por favor, ingresa los datos para configurar el monitoreo satelital.")
    
    with st.form("registro_usuario"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre Completo del Administrador")
            hectareas = st.number_input("Cantidad de Hectáreas", min_value=0.1, step=0.1)
        
        with col2:
            st.markdown("**Ubicación del Terreno (Coordenadas)**")
            lat = st.number_input("Latitud", value=-33.45, format="%.6f")
            lon = st.number_input("Longitud", value=-70.66, format="%.6f")
        
        btn_registro = st.form_submit_button("Configurar Monitoreo")
        
        if btn_registro:
            if nombre:
                st.session_state.registrado = True
                st.session_state.user_data = {
                    "nombre": nombre,
                    "hectareas": hectareas,
                    "coords": [lat, lon]
                }
                st.rerun()
            else:
                st.error("Por favor, ingresa tu nombre para continuar.")

# --- PÁGINA 2: DASHBOARD PRINCIPAL (Solo si está registrado) ---
else:
    u = st.session_state.user_data
    st.title(f"🌱 Dashboard: Campo de {u['nombre']}")
    st.sidebar.success(f"Ubicación: {u['coords']}")
    st.sidebar.info(f"Superficie: {u['hectareas']} Hectáreas")

    # Botón para volver a registrar o cerrar sesión
    if st.sidebar.button("Cambiar Terreno"):
        st.session_state.registrado = False
        st.rerun()

    # --- AQUÍ CONTINÚA TU LÓGICA DE AGBRAIN ---
    # Nota: Usa u['coords'][0] para la latitud y u['coords'][1] para la longitud
    # en tus llamadas a Open-Meteo y Folium para que el mapa se centre solo.
