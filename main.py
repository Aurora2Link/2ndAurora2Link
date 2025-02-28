from flask import Flask, request, jsonify
import redis
import os
from celery import Celery

app = Flask(__name__)

# Variables globales
Phone_number = "0000"
Message = "Nothing"

#Config Redis with Railway
REDIS_URL = os.getenv("REDIS_URL")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

#Config Celery
celery = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)

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
    global Phone_number, Message
    if request.method == "GET":
        if request.args.get('hub.verify_token') == "JUAN":
            return request.args.get('hub.challenge')
        else:
            return "Error de autentificación."
    #Recive data from message            
    data = request.get_json()
    process_message.delay(data) #Send to celery

    # Phone_number = data['entry'][0]['changes'][0]['value']['messages'][0]['from']
    # Message = data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
    return jsonify({"status": "success"}, 200)

@celery.task
def process_message(data):
    try:
        Phone_number = data['entry'][0]['changes'][0]['value']['messages'][0]['from']
        Message = data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
        print(f"Message recived from {Phone_number}: {Message}")
        redis_client.lpush("message_queue", f"{Phone_number}:{message}")
        print("Message stored in Redis successfully.")

    except Exception as e:
        print(f"Error while processing the message: {str(e)}")

@app.route('/messages')
def get_messages():
    if check_redis():
        messages = redis_client.lrange("message_queue", 0, 9)
        return jsonify({"last_messages": messages})
    return jsonify({"error": "Redis no disponible"}), 500


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

