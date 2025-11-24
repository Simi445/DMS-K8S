from flask import Flask
import pika
import json
import os
import threading
import sys
sys.path.append('/app/shared')
from rabbitmq_client import RabbitMQ

app = Flask(__name__)

def handle_message(message, replica_count, current_replica):
    try:
        host = os.environ.get('RABBIT_HOST', 'collection-rabbitmq-service.default.svc.cluster.local')
        port = int(os.environ.get('RABBIT_PORT', 5672))
        username = os.environ.get('RABBIT_USER', 'admin')
        password = os.environ.get('RABBIT_PASS', 'admin123')
        
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=host, port=port, credentials=pika.PlainCredentials(username, password)))
        pub_channel = connection.channel()
        pub_channel.exchange_declare(exchange='monitoring_ingest', exchange_type='direct')
        
        replica_id = (current_replica[0] % replica_count) + 1
        routing_key = f'replica{replica_id}'
        current_replica[0] += 1
        
        body = json.dumps(message)
        
        pub_channel.basic_publish(
            exchange='monitoring_ingest',
            routing_key=routing_key,
            body=body
        )
        print(f"Forwarded message to {routing_key}", flush=True)
        
        connection.close()
        
    except Exception as e:
        print(f"Error forwarding message: {str(e)}", flush=True)

def main():
    replica_count = 3 
    current_replica = [0]  
    
    rabbitmq_consumer = RabbitMQ('load-balancer', 'consumption_data', os.environ.get('RABBIT_HOST', 'collection-rabbitmq-service.default.svc.cluster.local'))
    
    def message_handler(message):
        handle_message(message, replica_count, current_replica)
    
    rabbitmq_consumer.consumeMessage(message_handler)

if __name__ == '__main__':
    consumer_thread = threading.Thread(target=main, daemon=True)
    consumer_thread.start()
    
    print("Load Balancer starting...", flush=True)
    app.run(debug=False, host='0.0.0.0', port=5001)