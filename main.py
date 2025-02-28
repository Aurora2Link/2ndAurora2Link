from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, World!'

# Variables globales
Phone_number = "0000"
Message = "Nothing"

@app.route("/webhook/", methods=["POST", "GET"])
def webhook_whatsapp():
    global Phone_number, Message
    # SI HAY DATOS RECIBIDOS VIA GET
    if request.method == "GET":
        # SI EL TOKEN ES IGUAL AL QUE RECIBIMOS
        if request.args.get('hub.verify_token') == "JUAN":
            return request.args.get('hub.challenge')
        else:
            # SI NO SON IGUALES RETORNAMOS UN MENSAJE DE ERROR
            return "Error de autentificación."
    # RECIBIMOS TODOS LOS DATOS ENVIADO VIA JSON
    data = request.get_json()
    # EXTRAEMOS EL NÚMERO DE TELÉFONO Y EL MENSAJE
    Phone_number = data['entry'][0]['changes'][0]['value']['messages'][0]['from']
    Message = data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
    # RETORNAMOS EL STATUS EN UN JSON
    return jsonify({"status": "success"}, 200)

@app.route('/about')
def about():
    return "Phone Number: " + Phone_number + " Message: " + Message

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
