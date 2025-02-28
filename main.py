from flask import Flask, request, jsonify
import redis
import os
from celery import Celery
import json
import logging

app = Flask(__name__)

# Configura el logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables globales
Phone_number = "0000"
Message = "Nothing"

#Config Redis with Railway
REDIS_URL = os.getenv("REDIS_URL")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

#Config Celery
celery = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)

def log_json(message, level="info"):
    log_message = json.dumps(message)
    if level == "info":
        logger.info(log_message)
    elif level == "warning":
        logger.warning(log_message)
    elif level == "error":
        

def check_redis():
    try:
        redis_client.ping()
        log_json({"message": "Redis está conectado"})
        return True
    except redis.exceptions.ConnectionError:
        log_json({"message": "Redis no está disponible"}, level="error")
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
        log_json({"phone_number": Phone_number, "message": Message})
        redis_client.lpush("message_queue", f"{Phone_number}:{Message}")
        log_json({"message": "Message stored in Redis successfully."})

    except Exception as e:
        log_json({"error": f"Error while processing the message: {str(e)}"}, level="error")

@app.route('/messages')
def get_messages():
    if check_redis():
        messages = redis_client.lrange("message_queue", 0, 9)
        return jsonify({"last_messages": messages})
    return jsonify({"error": "Redis no disponible"}), 500


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

