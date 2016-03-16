import os
import sys
import csv
import datetime
import time
import requests
import json
import glob
import RPi.GPIO as GPIO

#code by Charlie Chong for ENGO500 GIScience#1 project Smart Cities for Smart citizens
#code contains sections not written by me but taken from online tutorials

#this may be unecessary
time.sleep(5) #pi sometimes seems to ignore some initial scripts sometimes unless it sleeps for a bit first

upstream = "259349" #stream for upload speed
dnstream = "259343" #stream for download speed
tmstream = "258944" #stream for temperature stream
analogstream = "259355" #stream for analog
ipstream = "259361" #stream for loacl ip addresses for SSH

token = "b1937bfb-c9fc-41e9-ae19-1b455f7a9443" #pg-sensorup api key
path = "/home/pi/" #path
pi_name = "ENE333" #which pi is this? This will upload with the IP address so the PI can be connected by SSH

#Setting up GPIO for MCP 3008 section obtained from adafruit tutorial: Analog Inputs for Raspberry Pi Using the MCP3008
#setup ADC GPIO
GPIO.setmode(GPIO.BCM)
DEBUG = 1
SPICLK = 18  #clock pin
SPIMISO = 23 #Data Out from MCP 3008
SPIMOSI = 24 #DIN, Data In from Raspberry Pi
SPICS = 25   #CS, Chip select
# set up the SPI interface pins
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)


#setup temperature sensor
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

#uploads the PI's name and local IP address to the API
def ip():
	lol = os.popen("ifconfig").read() #ifconfig network interface configuration
	lel = lol.rstrip().split('\n')
	if len(lel) > 20:
		lul = lol.rstrip().split('\n')[18].rstrip().split(' ')[11]
	else:
		lul = lol.rstrip().split('\n')[1].rstrip().split(' ')[11]

	print("ip address is:")
	print(lul)
	upload(pi_name+lul,ipstream)

#code was part of AlekseyP's code that automatically tweeted Comcast when his internet was slow
def test():
    #run speedtest-cli
    print 'running test'
    a = os.popen("python /home/pi/speedtest-cli/speedtest_cli.py --simple").read()
    print 'ran'
    #split the 3 line result (ping,down,up)
    lines = a.split('\n')
    print a
    ts = time.time()
    date =datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    #if speedtest could not connect set the speeds to 0
    if "Cannot" in a:
        p = 100
        d = 0
        u = 0
        #extract the values for ping down and up values
    else:
        p = lines[0][6:11]
        d = lines[1][10:14]
        u = lines[2][8:12]
        print date,p, d, u
        #save the data to file for local network plotting
        out_file = open( path+ 'data.csv', 'a')
        writer = csv.writer(out_file)
        writer.writerow((ts*1000,p,d,u))
        out_file.close()
    upload(d,dnstream)
    upload(u,upstream)

#Function to upload to pg-api sensorup
#give it the data to be sent, and the stream ID
def upload(data,dstream):
    data=str(data)
    dstream = str(dstream)
    url= 'http://pg-api.sensorup.com/st-playground/proxy/v1.0/Datastreams('+dstream+')/Observations'
    headers= {
    "Content-Type":"application/json",
    "St-P-Access-Token":token,
    }
    payload = {"result":data}
    print(payload)
    r=requests.post(url, data=json.dumps(payload), headers=headers)
    print(r)
    print(r.text)

#give function the ADC channel and returns the reading from the MCP3008
def read_adc(adcnum):
	return readadc(adcnum, SPICLK,SPIMOSI,SPIMISO,SPICS)

#function taken from tutorial
# Written by Limor "Ladyada" Fried for Adafruit Industries, (c) 2015
# This code is released into the public domain
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
	print("Measuring ADC")
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, True)

        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)     # bring CS low

        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin, True)
                else:
                        GPIO.output(mosipin, False)
                commandout <<= 1
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1

        GPIO.output(cspin, True)

        adcout >>= 1       # first bit is 'null' so drop it
	upload(adcout,analogstream)
        return adcout

def read_temp_raw():
	f = open(device_file, 'r')
	lines = f.readlines()
	f.close()
	return lines

#code taken from tutorial on adafruit
#Adafruit's Raspberry Pi Lesson 11. DS18B20 Temperature Sensing
def read_temp():
	lines = read_temp_raw()
	while lines[0].strip()[-3:] != 'YES':
		time.sleep(0.2)
		lines = read_temp_raw()
	equals_pos = lines[1].find('t=')
	if equals_pos != -1:
		temp_string = lines[1][equals_pos+2:]
		temp_c = float(temp_string) / 1000.0
		#temp_f = temp_c * 9.0 / 5.0 + 32.0
		upload(temp_c,tmstream)
		return temp_c#, temp_f

ip() #upload IP address

interval = 5 #PI will gather data every "" minutes

sleeptime = 5*60
intervals = sleeptime/interval


while(True):
    init = int(time.time())
    read_temp()
    read_adc(0)
    test()
    fint = int(time.time())
    diff = abs(init - fint)
    print("Process took "+str(diff)+" seconds")
    print("Sleeping for " + str(sleeptime-diff) + " more seconds")
    time.sleep((sleeptime-diff)%interval)
    rmint = int((sleeptime-diff)/interval)
    while(rmint > 0):
        print(str((intervals-rmint)*interval)+" seconds passed")
        print(str((rmint)*interval) + " seconds remaining")
	time.sleep(interval)
	rmint = rmint-1
