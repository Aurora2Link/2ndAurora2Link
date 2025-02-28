from flask import Flask, request, jsonify
import redis
import os
from celery import Celery

app = Flask(__name__)

#Config Redis with Railway
REDIS_URL = os.getenv("REDIS_URL")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

#Config Celery
celery = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)

@app.route('/')
def home():
    return 'Hello, World!'

# Variables globales
Phone_number = "0000"
Message = "Nothing"

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
        redis_client.lpush("message_queue", f"{Phone_number}:{message}")
        print(f"Message recived from {Phone_number}: {Message}")

    except Exception as e:
        print(f"Error while processing the message: {str(e)}")

@app.route('/messages')
def get_messages():
    messages = redis_client.lrange("message_queue", 0,9)
    return jsonify({"last_messages": messages})

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
