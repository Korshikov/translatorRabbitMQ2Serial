#!/usr/bin/env python
import threading

import subprocess
import sched, time
import datetime

import pika
import serial
import random
from retry import retry

import json


def callback(ch, method, properties, body):
    request = json.loads(body.decode("utf-8"))
    print(request, end="\n")
    if 'process' in request and request['process']:
        processing_request(request)
    else:
        send_to_serial(body)


def send_to_global_log(message):
    global channel
    channel.basic_publish(exchange='', routing_key='logs_queue', body=message)


def send_to_serial(message):
    threadLock.acquire()
    print(message, end="\n")

    try:
        ser = serial.Serial('/dev/ttyUSB0', 115200)
        ser.write(message)
        ser.close()
    except IOError as error:
        print("arduino serial not connected")
    finally:
        threadLock.release()
    send_to_global_log("arduino serial not connected")


def send_to_log(message):
    pass


def processing_request(request):
    global state
    if request['deviceIdentifier'] == 'pwm1':
        if request['level'] == 10:
            send_to_serial(json.dumps({'deviceIdentifier': 'sw9', 'power': True, 'period': 2000}).encode())
            time.sleep(1)
            send_to_serial(
                json.dumps({'deviceIdentifier': 'pwm1', 'power': True, 'level': 10, 'period': 5000}).encode())
            state = 4
            scene_update(state)
            return
        elif request['level'] == 255:
            state = 5
            scene_update(state)
            return
    elif request['deviceIdentifier'] == 'ssr3':
        state = request['state']
        scene_update(state)
        if request['level'] > 30:
            send_to_serial(json.dumps({'deviceIdentifier': 'sw4', 'power': True}).encode())
            send_to_serial(json.dumps({'deviceIdentifier': 'ssr3', 'power': True, 'level': request['level']}).encode())
            if request['level'] > 180:
                send_to_serial(
                    json.dumps({'deviceIdentifier': 'ssr2', 'power': True, 'level': request['level']}).encode())
            else:
                send_to_serial(json.dumps({'deviceIdentifier': 'ssr2', 'power': False}).encode())
        else:
            send_to_serial(json.dumps({'deviceIdentifier': 'sw4', 'power': False}).encode())
            send_to_serial(json.dumps({'deviceIdentifier': 'ssr3', 'power': False}).encode())
            send_to_serial(json.dumps({'deviceIdentifier': 'ssr2', 'power': False}).encode())
        return


def scene_update(scene):
    if scene == 0:
        # 0 - на старте
        send_to_serial(json.dumps({'deviceIdentifier': 'sw1', 'power': False}).encode())  # свет на гирю
        send_to_serial(json.dumps({'deviceIdentifier': 'sw2', 'power': False}).encode())  # освещение лазера
        send_to_serial(json.dumps({'deviceIdentifier': 'sw3', 'power': True}).encode())  # гирлянда в аквариуме
        send_to_serial(
            json.dumps({'deviceIdentifier': 'sw5', 'power': False}).encode())  # освещение лазера
        send_to_serial(json.dumps({'deviceIdentifier': 'sw6', 'power': True}).encode())  # освещение шредера
        send_to_serial(json.dumps({'deviceIdentifier': 'sw12', 'power': False}).encode())  # аварийная сигнализация
        video_update(True)

    elif scene == 1:
        # 1 - дует вентилятор, может вернуться в 0
        send_to_serial(json.dumps({'deviceIdentifier': 'sw1', 'power': False}).encode())  # свет на гирю
        send_to_serial(json.dumps({'deviceIdentifier': 'sw2', 'power': False}).encode())  # освещение лазера
        send_to_serial(json.dumps({'deviceIdentifier': 'sw3', 'power': True}).encode())  # гирлянда в аквариуме
        send_to_serial(
            json.dumps({'deviceIdentifier': 'sw5', 'power': False}).encode())  # освещение лазера
        send_to_serial(json.dumps({'deviceIdentifier': 'sw6', 'power': True}).encode())  # освещение шредера
        send_to_serial(json.dumps({'deviceIdentifier': 'sw12', 'power': False}).encode())  # аварийная сигнализация
        video_update(True)
    elif scene == 2:
        # 2 - включена подсветка лазера
        send_to_serial(json.dumps({'deviceIdentifier': 'sw1', 'power': False}).encode())  # свет на гирю
        send_to_serial(json.dumps({'deviceIdentifier': 'sw2', 'power': True}).encode())  # освещение лазера
        send_to_serial(json.dumps({'deviceIdentifier': 'sw3', 'power': True}).encode())  # гирлянда в аквариуме
        send_to_serial(
            json.dumps({'deviceIdentifier': 'sw5', 'power': True}).encode())  # освещение лазера
        send_to_serial(json.dumps({'deviceIdentifier': 'sw6', 'power': True}).encode())  # освещение шредера
        send_to_serial(json.dumps({'deviceIdentifier': 'sw12', 'power': False}).encode())  # аварийная сигнализация
    elif scene == 3:
        # 3- включено питание лазера
        send_to_serial(json.dumps({'deviceIdentifier': 'sw1', 'power': False}).encode())  # свет на гирю
        send_to_serial(json.dumps({'deviceIdentifier': 'sw2', 'power': True}).encode())  # освещение лазера
        send_to_serial(json.dumps({'deviceIdentifier': 'sw3', 'power': True}).encode())  # гирлянда в аквариуме
        send_to_serial(
            json.dumps({'deviceIdentifier': 'sw5', 'power': True}).encode())  # освещение лазера
        send_to_serial(json.dumps({'deviceIdentifier': 'sw6', 'power': True}).encode())  # освещение шредера
        send_to_serial(json.dumps({'deviceIdentifier': 'sw12', 'power': False}).encode())  # аварийная сигнализация
        video_update(True)
    elif scene == 4:
        # 4 - произведен как минимум один тестовый выстрел
        send_to_serial(json.dumps({'deviceIdentifier': 'sw1', 'power': True}).encode())  # свет на гирю
        send_to_serial(
            json.dumps({'deviceIdentifier': 'sw5', 'power': True}).encode())  # освещение лазера
        send_to_serial(json.dumps({'deviceIdentifier': 'sw6', 'power': True}).encode())  # освещение шредера
        send_to_serial(json.dumps({'deviceIdentifier': 'sw12', 'power': False}).encode())  # аварийная сигнализация
        video_update(True)

    elif scene == 5:
        # 5 - произведен боевой выстрел
        send_to_serial(json.dumps({'deviceIdentifier': 'sw1', 'power': True}).encode())  # свет на гирю
        send_to_serial(json.dumps({'deviceIdentifier': 'sw2', 'power': False}).encode())  # освещение лазера
        send_to_serial(json.dumps({'deviceIdentifier': 'sw3', 'power': True}).encode())  # гирлянда в аквариуме
        send_to_serial(
            json.dumps({'deviceIdentifier': 'sw5', 'power': True}).encode())  # освещение лазера
        send_to_serial(json.dumps({'deviceIdentifier': 'sw6', 'power': True}).encode())  # освещение шредера
        send_to_serial(json.dumps({'deviceIdentifier': 'sw12', 'power': True}).encode())  # аварийная сигнализация
        send_to_serial(json.dumps({'deviceIdentifier': 'sw11', 'power': False}).encode())  # аварийная сигнализация
        send_to_serial(json.dumps({'deviceIdentifier': 'sw13', 'power': False}).encode())  # аварийная сигнализация
        send_to_serial(json.dumps({'deviceIdentifier': 'sw7', 'power': False}).encode())  # аварийная сигнализация
        send_to_serial(json.dumps({'deviceIdentifier': 'sw8', 'power': False}).encode())  # аварийная сигнализация
        send_to_serial(json.dumps({'deviceIdentifier': 'ws2813', 'power': True, 'color':'FF0000', 'level':20, 'start':0, 'end': 587}).encode())  # аварийная сигнализация
        video_update(False)


def video_update(shreder):
    global image
    global counter
    global finished
    global moneycounter
    counter = (counter + 1) % 5000
    if shreder:
        price = 0
        now = datetime.datetime.now()
        price = 24 * (now.day - 10) + (now.hour - 4)
        print("price= %d" % price, end="\n")
        if price > 200:
            price = 200
        fim_str = None
        if 0 <= now.second < 20:
            timer_str = "/home/pi/Pictures/Timers_AME/01_TIMER/01_TIMER" + "{:0>2}".format(31 + now.minute) + ".jpg"
            fim_str = timer_str
            if now.minute == 00:
                if price != moneycounter:
                    send_to_serial(json.dumps({'deviceIdentifier': 'sw14', 'power': True, 'period': 3700}).encode())
                    moneycounter = price
        elif 20 <= now.second < 40:
            money_yep_str = "/home/pi/Pictures/Timers_AME/02_Money_Yep/02_Money_Yep" + "{:0>3}".format(price) + ".jpg"
            fim_str = money_yep_str
        elif 40 <= now.second < 60:
            money_nope_str = "/home/pi/Pictures/Timers_AME/03_Money_Nope/03_Money_Nope" + "{:0>3}".format(
                price) + ".jpg"
            fim_str = money_nope_str
        if image is not None:
            image.kill()
        image = subprocess.Popen(["fim", "-q", "-r", "1920×1080", fim_str])
    else:
        global timestamp
        if image is not None:
            image.kill()
        if timestamp is None:
            timestamp = datetime.datetime.now()
            video = subprocess.Popen(["omxplayer", "/home/pi/Pictures/01_TIMER_start_Laser.mp4"])
        now = datetime.datetime.now()
        if 5400 < (now - timestamp).total_seconds() < 5520:
            send_to_serial(
                json.dumps({'deviceIdentifier': 'pwm1', 'power': True, 'level': 255, 'period': 200000}).encode())
            if counter % 4 == 0:
                send_to_serial(json.dumps({'deviceIdentifier': 'sw9', 'power': True, 'period': 2000}).encode())
        if 5520 < (now - timestamp).total_seconds() < 6000:
            send_to_serial(json.dumps({'deviceIdentifier': 'sw15', 'power': True, 'period': 30000}).encode())
        if 6000 < (now - timestamp).total_seconds() and finished is None:
            video = subprocess.Popen(["omxplayer", "--loop", "/home/pi/Pictures/RuVDS_FINAL_REN.mp4"])
            finished = True


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
state = 0
image = None
timestamp = None
counter = 0
finished = None
moneycounter = 0

if __name__ == '__main__':
    consume()
