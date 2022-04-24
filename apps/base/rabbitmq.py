import pika
import os
from dotenv import load_dotenv

load_dotenv()
credentials = pika.PlainCredentials(os.getenv('RABBITMQ_USERNAME'), os.getenv('RABBITMQ_PASSWORD'))
parameters = pika.ConnectionParameters(
    host=os.getenv('RABBITMQ_HOST'),
    port=int(os.getenv('RABBITMQ_PORT')),
    credentials=credentials
)
QUEUEConnection = pika.BlockingConnection(parameters)
channel = QUEUEConnection.channel()
channel.queue_declare(queue=os.getenv("QUEUE_PROJECT"))
channel.queue_declare(queue=os.getenv("QUEUE_TOKEN"))
channel.queue_declare(queue=os.getenv("QUEUE_PRICE"))
channel.queue_declare(queue=os.getenv("QUEUE_EVENT"))
