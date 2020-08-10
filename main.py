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
    request = json.loads(body)
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


def processing_request(request):
    state = request['state']
    scene_update (state)
    if request['device'] == 'pwm1':
        if request['level'] == 10:
                send_to_serial(json.dumps({'device': 'sw9', 'power': True, 'period':2000}))
                time.sleap(1)
                send_to_serial(json.dumps({'device': 'pwm1', 'power': True, 'level': 10, 'period': 5000}))
            return
        elif request['level'] == 255:
            process_full_laser_run()
        return 
    elif request['device'] == 'ssr2':
        
            if request['power'] > 30:
                send_to_serial((json.dumps({'device': 'sw4', 'power': True}))
                send_to_serial((json.dumps({'device': 'ssr3', 'power': True, 'level': request['level']}))
                if request['power'] > 180:
                    send_to_serial(json.dumps({'device': 'ssr2', 'power': True, 'level': request['level']}))
                else:
                    send_to_serial((json.dumps({'device': 'ssr2', 'power': False}))
            else:
                send_to_serial((json.dumps({'device': 'sw4', 'power': False}))
                send_to_serial((json.dumps({'device': 'ssr3', 'power': False}))
                send_to_serial((json.dumps({'device': 'ssr2', 'power': False}))
        return
    

def scene_update (scene):
    if scene == 0:
        # 0 - на старте
        send_to_serial((json.dumps({'device': 'sw1', 'power': False}))  #свет на гирю
        send_to_serial((json.dumps({'device': 'sw2', 'power': False}))  #освещение лазера
        send_to_serial((json.dumps({'device': 'sw3', 'power': True}))   #гирлянда в аквариуме
        send_to_serial((json.dumps({'device': 'sw5', 'power': False}))  #освещение лазера                    
        send_to_serial((json.dumps({'device': 'sw6', 'power': True}))   #освещение шредера
        send_to_serial((json.dumps({'device': 'sw12', 'power': False})) #аварийная сигнализация
        video_update(True)

    elif scene == 1:
        #1 - дует вентилятор, может вернуться в 0
        send_to_serial((json.dumps({'device': 'sw1', 'power': False}))  #свет на гирю
        send_to_serial((json.dumps({'device': 'sw2', 'power': False}))  #освещение лазера
        send_to_serial((json.dumps({'device': 'sw3', 'power': True}))   #гирлянда в аквариуме
        send_to_serial((json.dumps({'device': 'sw5', 'power': False}))  #освещение лазера                    
        send_to_serial((json.dumps({'device': 'sw6', 'power': True}))   #освещение шредера
        send_to_serial((json.dumps({'device': 'sw12', 'power': False})) #аварийная сигнализация
        video_update(True)               
    elif scene == 2:
        #2 - включена подсветка лазера
        send_to_serial((json.dumps({'device': 'sw1', 'power': False}))  #свет на гирю
        send_to_serial((json.dumps({'device': 'sw2', 'power': True}))  #освещение лазера
        send_to_serial((json.dumps({'device': 'sw3', 'power': True}))   #гирлянда в аквариуме
        send_to_serial((json.dumps({'device': 'sw5', 'power': True}))  #освещение лазера                    
        send_to_serial((json.dumps({'device': 'sw6', 'power': True}))   #освещение шредера
        send_to_serial((json.dumps({'device': 'sw12', 'power': False})) #аварийная сигнализация     
    elif scene == 3:
        #3- включено питание лазера
        send_to_serial((json.dumps({'device': 'sw1', 'power': False}))  #свет на гирю
        send_to_serial((json.dumps({'device': 'sw2', 'power': True}))  #освещение лазера
        send_to_serial((json.dumps({'device': 'sw3', 'power': True}))   #гирлянда в аквариуме
        send_to_serial((json.dumps({'device': 'sw5', 'power': True}))  #освещение лазера                    
        send_to_serial((json.dumps({'device': 'sw6', 'power': True}))   #освещение шредера
        send_to_serial((json.dumps({'device': 'sw12', 'power': False})) #аварийная сигнализация
        video_update(True)
   elif scene == 4:
        #4 - произведен как минимум один тестовый выстрел
        send_to_serial((json.dumps({'device': 'sw1', 'power': True}))  #свет на гирю
        send_to_serial((json.dumps({'device': 'sw2', 'power': True}))  #освещение лазера
        send_to_serial((json.dumps({'device': 'sw3', 'power': True}))   #гирлянда в аквариуме
        send_to_serial((json.dumps({'device': 'sw5', 'power': True}))  #освещение лазера                    
        send_to_serial((json.dumps({'device': 'sw6', 'power': True}))   #освещение шредера
        send_to_serial((json.dumps({'device': 'sw12', 'power': False})) #аварийная сигнализация
        video_update(True)

    elif scene == 5:
        #5 - произведен боевой выстрел
        send_to_serial((json.dumps({'device': 'sw1', 'power': True}))  #свет на гирю
        send_to_serial((json.dumps({'device': 'sw2', 'power': False}))  #освещение лазера
        send_to_serial((json.dumps({'device': 'sw3', 'power': True}))   #гирлянда в аквариуме
        send_to_serial((json.dumps({'device': 'sw5', 'power': False}))  #освещение лазера                    
        send_to_serial((json.dumps({'device': 'sw6', 'power': True}))   #освещение шредера
        send_to_serial((json.dumps({'device': 'sw12', 'power': True})) #аварийная сигнализация
        video_update(False)
    
def video_update(shreder):
    if shreder == True:
        price = 0
        now = datetime.datetime.now()
        if now.day == 10:
            #if now.hour>=10:
                price = 200 - now.hour + 10
        
        elif now.day == 11:
            price = 200 - now.hour - 14
        elif now.day == 12:
            price = 200 - now.hour - 38
        elif now.day == 13:
            price = 200 - now.hour - 62
        elif now.day == 14:    
            price = 200 - now.hour - 86
        elif now.day == 15:
            price = 200 - now.hour - 110
        elif now.day == 16:
            price = 200 - now.hour - 134
        elif now.day == 17:
            price = 200 - now.hour - 158
        elif now.day == 18:
            price = 200 - now.hour - 182

    if now.second >= 0 && now.second <20 :
        timer_str = "/home/pi/Pictures/Timers_AME/01_TIMER/01_TIMER" + "{:0>2}".format(60 - now.minute) + ".jpg"
        image = subprocess.Popen(["fim", "-q","-r","1920×1080", timer_str])
    elif now.second >= 20 && now.second <40 :
        money_yep_str = "/home/pi/Pictures/Timers_AME/02_Money_Yep/02_Money_Yep" + "{:0>3}".format(price) + ".jpg"
        image = subprocess.Popen(["fim", "-q","-r","1920×1080", money_yep_str])
    elif now.second >= 40 && now.second <60 :    
        money_nope_str = "/home/pi/Pictures/Timers_AME/03_Money_Nope/03_Money_Nope" + "{:0>3}".format(200 - price) + ".jpg"
        image = subprocess.Popen(["fim", "-q","-r","1920×1080", money_nope_str])
        

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

if __name__ == '__main__':
    consume()
