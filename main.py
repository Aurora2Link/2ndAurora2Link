from flask import Flask, request, jsonify
import redis
import os

app = Flask(__name__)

# Configurar Redis
REDIS_URL = os.getenv("REDIS_URL")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def check_redis():
    try:
        redis_client.ping()
        print("Redis está conectado")
        return True
    except redis.exceptions.ConnectionError:
        print("Redis no está disponible")
        return False

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
    # Enviar el mensaje a Redis
    redis_client.lpush("message_queue", data)
    return jsonify({"status": "success"}, 200)

@app.route('/messages')
def get_messages():
    if check_redis():
        messages = redis_client.lrange("message_queue", 0, 9)
        return jsonify({"last_messages": messages})
    return jsonify({"error": "Redis no disponible"}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
