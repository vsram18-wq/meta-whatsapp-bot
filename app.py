from flask import Flask, request
import requests
import os

app = Flask(__name__)

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

VERIFY_TOKEN = "my_verify_token"


@app.route("/webhook", methods=["GET"])
def verify():

    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200

    return "Verification failed", 403


@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.get_json()

    try:

        message = data["entry"][0]["changes"][0]["value"]["messages"][0]

        phone_number = message["from"]
        text = message["text"]["body"]

        send_whatsapp_message(phone_number, f"🔥 You said: {text}")

    except Exception as e:
        print("Error:", e)

    return "OK", 200


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

    requests.post(url, headers=headers, json=data)


if __name__ == "__main__":
    app.run(debug=True)