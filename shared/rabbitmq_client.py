from flask import Flask
import pika
import threading
import time
import os
import sys
import json

class RabbitMQ():

    def __init__(self, consumerName, exchangeName, host=None):
        self.host = host or os.environ.get('RABBIT_HOST', 'rabbitmq')
        self.port = int(os.environ.get('RABBIT_PORT', 5672))
        self.username = os.environ.get('RABBIT_USER', 'admin')
        self.password = os.environ.get('RABBIT_PASS', 'admin123')
        self.consumer = consumerName
        self.exchange = exchangeName

    def consumeMessage(self, message_handler=None):
        def callback(ch, method, properties, body):
            try:
                message = json.loads(body)
                print(f"{self.consumer} received: {message}", flush=True)
                if message_handler:
                    message_handler(message)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except json.JSONDecodeError:
                print(f"{self.consumer} received invalid JSON: {body}", flush=True)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f"{self.consumer} error processing message: {str(e)}", flush=True)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        def consume():
            connection = self.connect_with_retry(self.host, self.port)
            print(f"Connected to RabbitMQ at {self.host}:{self.port}", flush=True)

            channel = connection.channel()
            channel.exchange_declare(exchange=self.exchange, exchange_type='fanout')
            result = channel.queue_declare(queue='', exclusive=True)
            queue_name = result.method.queue
            channel.queue_bind(exchange=self.exchange, queue=queue_name)

            print(f"Bound to queue {queue_name}, waiting for messages...", flush=True)

            channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)
            channel.start_consuming()
        threading.Thread(target=consume, daemon=True).start()

    def sendMessage(self, messageType, body):
        print("Send function called", flush=True)
        connection = self.connect_with_retry(self.host, self.port)
        channel = connection.channel()
        channel.exchange_declare(exchange=self.exchange, exchange_type='fanout')
        
        message = {
            "type": messageType,
            "data": body,
            "sender": self.consumer
        }
        
        serialized_body = json.dumps(message)
        channel.basic_publish(exchange=self.exchange, routing_key='', body=serialized_body)
        print(f"Published message {message} to exchange {self.exchange}", flush=True)
        connection.close()
        return f'Message sent: {messageType}'

    def connect_with_retry(self, host, port, interval=5):
        while True:
            try:
                credentials = pika.PlainCredentials(self.username, self.password)
                return pika.BlockingConnection(pika.ConnectionParameters(host, port=port, credentials=credentials))
            except pika.exceptions.AMQPConnectionError as e:
                print(f"RabbitMQ not ready at {host}:{port} - retrying in {interval}s: {e}")
                time.sleep(interval)