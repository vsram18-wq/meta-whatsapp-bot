from flask import Flask
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp():

    response = MessagingResponse()
    response.message("🔥 Bot working from Railway 🔥")

    return str(response)

if __name__ == "__main__":
    app.run()