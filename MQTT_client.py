import spidev
from time import sleep
import datetime
import time
import RPi.GPIO as GPIO
import os, urlparse
import paho.mqtt.client as mqtt

spi = spidev.SpiDev()
spi.open(0,0)
time_ =  time.time()
systemTime =time.strftime("%H:%M:%S", time.gmtime(time.time()-time_))
readFrequency = 1
readInt = 0
msg = "nothing"
#-----------------------------------------------------------------
def setup():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(11, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.setup(13, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.setup(15, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.setup(12, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.setup(7, GPIO.OUT)
    print("setup done!")
#-----------------------------------------------------------------
def analogInput(channel):
    spi.max_speed_hz = 1350000
    adc = spi.xfer2([1,(8+channel)<<4,0])
    data = ((adc[1]&3) << 8)+ adc[2]
    return data
#-----------------------------------------------------------------
def changeInterval(e):
    global readFrequency
    if readFrequency ==1:
        readFrequency =2
    elif readFrequency==2:
        readFrequency=5
    elif readFrequency==5:
        readFrequency=1
#------------------------------------------------------------------
def resetSysTime(e):
    global systemTime
    global time_
    time_ = time.time()
    systemTime = time.strftime("%H:%M:%S", time.gmtime(time.time()-time_))
#------------------------------------------------------------------------
def alarm():
    GPIO.output(7, 1)
#-------------------------------------------------------------------------
def pause_start(e):
    global readInt
    if readInt==0:
        readInt=1
    elif readInt==1:
        readInt=0
#---------------------------------------------------------------------------
    
#---------------------------------------------------------------------------
def checkBtn():
    GPIO.add_event_detect(11, GPIO.FALLING, callback = changeInterval, bouncetime=300)
    #GPIO.add_event_detect(13, GPIO.FALLING, callback = dismissAlarn, bouncetime=300)
    GPIO.add_event_detect(15, GPIO.FALLING, callback = resetSysTime, bouncetime=300)
    GPIO.add_event_detect(12, GPIO.FALLING, callback = pause_start, bouncetime=300)
#-----------------------------------------------------------------------------
#Methods for connecting, publish and subscribing to MQTT broker
def on_connect(client, userdata, flags, rc):
    print("rc: " + str(rc))
    #pass
def on_publish(client, obj, right):
    #print("mid: " + str(right))
     pass
def on_log(client, obj, level, string):
     print(string)
     #pass
def on_subscribe(client, obj, mid, qos):
    print("mid for subscribe: " +str(mid))
def on_message(client, obj, msg):
    print(msg.topc+ " " + str(msg.qos)+ " " +str(msg.payload))
#-----------------------------------------------------------------------------

#----------------------MAIN METHOD--------------------------------------------
def main():  
#---------------------CONNECT TO MQTT BROKER----------------------------------
    mqttc = mqtt.Client()
    mqttc.on_connect = on_connect
    mqttc.on_publish = on_publish
    mqttc.on_subscribe = on_subscribe
    mqttc.on_message = on_message
    url_str  = os.environ.get('soldier.cloudmqtt.com','http://192.168.137.15:1880')
    url = urlparse.urlparse(url_str)
    mqttc.username_pw_set('pi2', '1234')
    mqttc.connect('soldier.cloudmqtt.com', 10201)
    #mqttc.loop_start()
#----------------------------------------------------------------------------
    while True:
        global readInt
        if readInt ==0:
            humidity = analogInput(0)
            temperature = analogInput(2)
            light = analogInput(1)
        localtime = datetime.datetime.now()
        rtc_time = localtime.strftime("%H:%M:%S")
        global systemTime
        systemTime = time.strftime("%H:%M:%S", time.gmtime(time.time()-time_))
        tempValue = int(round(((temperature * 330)//1023)-70))
        humValue = round(abs((humidity-9)/310.0)*1.0,1)
        v_out = round((float(light)/1023.0)*humValue, 2)
        if v_out <0.65 or v_out>2.65:
            alarm()
            mqttc.publish('alarm',"ALARM!" )
#--------------------START PUBLISHING TO MQTT BROKER---------------------------
        mqttc.publish('rtcTime', rtc_time)
        mqttc.publish('systemTime', systemTime)
        mqttc.publish('temperature', tempValue)
        mqttc.publish('humidity', humValue)
        mqttc.publish('light', light)
        mqttc.publish('dacOut', v_out)
        mqttc.subscribe('dismiss', 0)
        if readInt ==0:
            mqttc.publish('startStop', "TRUE")
        elif readInt ==1:
            mqttc.publish('startStop', "FALSE")
        #print("Done")
        sleep(readFrequency)
if __name__=='__main__':
    setup()
    checkBtn()
    main()
#----------------------------------------------------------------------------
