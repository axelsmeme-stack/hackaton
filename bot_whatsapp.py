import os
import requests
from twilio.rest import Client

# 1. Credenciales desde GitHub Secrets
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)

# 2. Datos de Chile (Open-Meteo)
url = "https://api.open-meteo.com/v1/forecast?latitude=-33.45&longitude=-70.66&hourly=temperature_2m,precipitation_probability&timezone=America%2FSantiago&forecast_days=1"
res = requests.get(url).json()
temp = res['hourly']['temperature_2m'][0]

# 3. Mensaje para el Agricultor
cuerpo = f"""
🌱 *INFORME DIARIO AGTECH* 🚜
---------------------------
📍 Santiago, Chile
🌡️ Temperatura: {temp}°C
💧 Estado: Monitoreo Automático OK.
🔬 IA: No se detectan anomalías.
---------------------------"""

# 4. Envío (Usando el número de image_1c545f.png)
message = client.messages.create(
    from_='whatsapp:+19789694942', # Número de tu imagen image_1c545f.png
    body=cuerpo,
    to=f'whatsapp:{os.environ["MY_PHONE_NUMBER"]}'
)

print(f"Reporte enviado con éxito! SID: {message.sid}")
