from flask import Flask, request, jsonify
import redis
import os
import json

app = Flask(__name__)

# Configurar Redis
REDIS_URL = os.getenv("REDIS_URL")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

@app.route('/')
def home():
    return 'Hello, World!'

@app.route("/webhook/", methods=["POST", "GET"])
def webhook_whatsapp():
    if request.method == "GET":
        if request.args.get('hub.verify_token') == "JUAN":
            return request.args.get('hub.challenge')
        else:
            return "Error de autentificación."
    # Recibe data del mensaje 
    data = request.get_json()
    # Convertir el objeto JSON a una cadena
    data_str = json.dumps(data)
    # Enviar el mensaje a Redis
    redis_client.lpush("message_queue", data_str)
    return jsonify({"status": "success"}, 200)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
    
