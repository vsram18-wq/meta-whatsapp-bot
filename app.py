from flask import Flask, request
import requests
import os
import sqlite3

app = Flask(__name__)

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

VERIFY_TOKEN = "my_verify_token"

# =========================
# DATABASE
# =========================

conn = sqlite3.connect("banquetes.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telefono TEXT,
    fecha_evento TEXT,
    personas TEXT,
    tipo_evento TEXT,
    peticiones TEXT,
    nombre TEXT,
    contacto TEXT,
    correo TEXT
)
""")

conn.commit()

# Guarda el estado temporal de cada usuario
user_states = {}


# =========================
# HOME
# =========================
@app.route("/", methods=["GET"])
def home():
    return "Banquetes Wyndham Bot Running 🚀", 200


# =========================
# WEBHOOK VERIFY
# =========================
@app.route("/webhook", methods=["GET"])
def verify():

    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200

    return "Verification failed", 403


# =========================
# RECEIVE MESSAGES
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.get_json()

    print("INCOMING:")
    print(data)

    try:

        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        # Ignora status updates
        if "messages" not in value:
            return "OK", 200

        message = value["messages"][0]

        phone_number = message["from"]

        # Solo texto
        if message["type"] != "text":
            send_whatsapp_message(
                phone_number,
                "⚠️ Por favor envía mensajes de texto."
            )
            return "OK", 200

        text = message["text"]["body"].strip()

        # Crear usuario si no existe
        if phone_number not in user_states:

            user_states[phone_number] = {
                "step": "fecha"
            }

            send_whatsapp_message(
                phone_number,
                "👋 Bienvenido a Banquetes Wyndham.\n\n"
                "Con gusto podemos ayudarte a cotizar tu evento.\n\n"
                "📅 ¿Para qué fecha sería el evento?"
            )

            return "OK", 200

        user = user_states[phone_number]
        step = user["step"]

        # =========================
        # STEP 1 - FECHA
        # =========================
        if step == "fecha":

            user["fecha_evento"] = text
            user["step"] = "personas"

            send_whatsapp_message(
                phone_number,
                "Perfecto 😊\n\n"
                "👥 ¿Para cuántas personas sería el evento?"
            )

        # =========================
        # STEP 2 - PERSONAS
        # =========================
        elif step == "personas":

            user["personas"] = text
            user["step"] = "tipo"

            send_whatsapp_message(
                phone_number,
                "🍽️ ¿Qué tipo de servicio necesitan?\n\n"
                "☕ Coffee Break\n"
                "🍳 Desayuno\n"
                "🍽️ Comida\n"
                "🌙 Cena\n"
                "🎤 Presentación / Conferencia"
            )

        # =========================
        # STEP 3 - TIPO
        # =========================
        elif step == "tipo":

            user["tipo_evento"] = text
            user["step"] = "peticiones"

            send_whatsapp_message(
                phone_number,
                "✨ ¿Tienen alguna petición especial?"
            )

        # =========================
        # STEP 4 - PETICIONES
        # =========================
        elif step == "peticiones":

            user["peticiones"] = text
            user["step"] = "nombre"

            send_whatsapp_message(
                phone_number,
                "👤 ¿Cuál es tu nombre?"
            )

        # =========================
        # STEP 5 - NOMBRE
        # =========================
        elif step == "nombre":

            user["nombre"] = text
            user["step"] = "contacto"

            send_whatsapp_message(
                phone_number,
                "📞 ¿Cuál es tu mejor teléfono de contacto?"
            )

        # =========================
        # STEP 6 - CONTACTO
        # =========================
        elif step == "contacto":

            user["contacto"] = text
            user["step"] = "correo"

            send_whatsapp_message(
                phone_number,
                "📧 ¿Cuál es tu correo electrónico?"
            )

        # =========================
        # STEP 7 - CORREO
        # =========================
        elif step == "correo":

            user["correo"] = text

            # GUARDAR EN DATABASE
            cursor.execute("""
            INSERT INTO clientes (
                telefono,
                fecha_evento,
                personas,
                tipo_evento,
                peticiones,
                nombre,
                contacto,
                correo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                phone_number,
                user.get("fecha_evento"),
                user.get("personas"),
                user.get("tipo_evento"),
                user.get("peticiones"),
                user.get("nombre"),
                user.get("contacto"),
                user.get("correo")
            ))

            conn.commit()

            send_whatsapp_message(
                phone_number,
                "✅ Gracias.\n\n"
                "Hemos recibido tu información.\n\n"
                "Uno de nuestros ejecutivos de Banquetes Wyndham "
                "te enviará una cotización próximamente."
            )

            # Reiniciar conversación
            del user_states[phone_number]

    except Exception as e:
        print("ERROR:")
        print(str(e))

    return "OK", 200


# =========================
# SEND MESSAGE
# =========================
def send_whatsapp_message(to, text):

    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": text
        }
    }

    response = requests.post(url, headers=headers, json=data)

    print("MESSAGE SENT:")
    print(response.status_code)
    print(response.text)


if __name__ == "__main__":
    app.run(debug=True)