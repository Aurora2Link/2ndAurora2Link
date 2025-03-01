from flask import Flask, request, jsonify
import redis
import os
from celery import Celery
from heyoo import WhatsApp

app = Flask(__name__)

#Config Redis with Railway
REDIS_URL = os.getenv("REDIS_URL")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

#Config WhatsApp
WP_TOKEN = os.getenv("WP_TOKEN")
ID_PHONE_NUM = os.getenv("ID_PHONE_NUM")

# Config Celery (sin backend, las tareas desaparecen después de ejecutarse)
celery = Celery("tasks", broker=REDIS_URL, backend=None)


def check_redis():
    try:
        redis_client.ping()
        print("Redis está conectado")
        return True
    except redis.exceptions.ConnectionError:
        print("Redis no está disponible")
        return False


def send_message(phone_number, message, url_image=None):
    try:
        message_wp = WhatsApp(WP_TOKEN, ID_PHONE_NUM)

        message_wp.send_message(message,phone_number)

        if url_image:
            message_wp.send_image(image=url_image, recipient_id=phone_number)

        print(f"Mensaje enviado correctamente a {phone_number}")
        return True
    except Exception as e:
        print(f"Error al enviar mensaje: {str(e)}")
        return False


def is_subscribed(phone_number):
    cache_key = f"sub:{phone_number}"
    status = redis_client.get(cache_key)
    
    if status is not None:
        return status == "1"
    
    #If not in cache, ask DB
    #fake DB API...
    response = {
        "status_code": 200,
        "id": "322123456789",
        "payed": "1",
        "sub_until": "2025-03-01"
        }

    """
    Not payed response
        response = {
        "status_code": 200,
        "id": "322123456789",
        "payed": "0",
        }
    """
    if response["status_code"] != 200:
        return False

    status = response.get("payed", "0")
    sub_until_date = datetime.strptime(response.get("sub_until", "1970-01-01"), "%Y-%m-%d")
    today = datetime.today()
    remaining_time = max((sub_until_date - today).days, 0)
    
    # Vida útil del token en segundos
    cache_lifespan = max(min(remaining_time * 86400, 604800), 60)

    redis_client.setex(cache_key, cache_lifespan, "1" if status == "1" else "0")
    
    return status == "1"


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
        
        '''
        if not is_subscribed(Phone_number):
            # Send message to user: need to pay
        Message = data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']    
        # Enviar a LLM

        '''
        
        Message = data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
        print(f"Message recived from {Phone_number}: {Message}")
        send_message(Phone_number,"Recibí tu mensaje!")
        # redis_client.lpush("message_queue", f"{Phone_number}:{Message}")
        # print("Message stored in Redis successfully.")

    except Exception as e:
        print(f"Error while processing the message: {str(e)}")


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

