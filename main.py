#!/usr/bin/env python
import threading

import pika
import serial
import random
from retry import retry


def callback(ch, method, properties, body):
    threadLock.acquire()
    print(body, end="\n")
    try:
        ser = serial.Serial('/dev/ttyUSB0', 115200)
        ser.write(body)
        ser.close()
    except IOError as error:
        print("arduino serial not connected")
    finally:
        threadLock.release()
    send_to_global_log("arduino serial not connected")


def send_to_global_log(message):
    global channel
    channel.basic_publish(exchange='', routing_key='logs_queue', body=message)


@retry(pika.exceptions.AMQPConnectionError, delay=5, jitter=(1, 3))
def consume():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='wireguard.sokol.delfserver.ru',
                                  credentials=pika.PlainCredentials(username="hardware", password="Ohl@iu8ath#aeLai")))
    global channel
    channel = connection.channel()
    result = channel.queue_declare('translator', exclusive=True, durable=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange='backend.exchange', queue=queue_name, routing_key="hardware.device.control.request")
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
        connection.close()


threadLock = threading.Lock()
channel = None

if __name__ == '__main__':
    consume()
