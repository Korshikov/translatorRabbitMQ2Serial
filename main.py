#!/usr/bin/env python
import threading

import pika
import serial
import random
import json
from retry import retry

abstractDevicesDict = {
    # Желтая настольная лампа
    "table_lamp": {
        "deviceIdentifier": "sw7",
        "power": False
    },
    # лампа торшер
    "lamp": {
        "deviceIdentifier": "sw8",
        "power": False
    },
    # Звезда
    "start": {
        "deviceIdentifier": "sw11",
        "power": False
    },
    # гирлянда на стелаже
    "garland": {
        "deviceIdentifier": "sw13",
        "power": False
    },
    "letter1": {
        "deviceIdentifier": "ws2813",
        "start": 456,
        "end": 587,
        "level": 20,
        "power": True,
        "color": "000000"
    },
    "letter2": {
        "deviceIdentifier": "ws2813",
        "start": 337,
        "end": 456,
        "level": 35,
        "power": True,
        "color": "000000"
    },
    "letter3": {
        "deviceIdentifier": "ws2813",
        "start": 211,
        "end": 337,
        "level": 50,
        "power": True,
        "color": "000000"
    },
    "letter4": {
        "deviceIdentifier": "ws2813",
        "start": 111,
        "end": 211,
        "level": 50,
        "power": True,
        "color": "000000"
    },
    "letter5": {
        "deviceIdentifier": "ws2813",
        "start": 0,
        "end": 111,
        "level": 50,
        "power": True,
        "color": "000000"
    }
}


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


@retry(pika.exceptions.AMQPConnectionError, delay=5, jitter=(1, 3))
def consume():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='wireguard.sokol.delfserver.ru',
                                  credentials=pika.PlainCredentials(username="hardware", password="Ohl@iu8ath#aeLai")))
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

if __name__ == '__main__':
    consume()
