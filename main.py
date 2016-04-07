#by Charlie Chong 
#for ENGO 500 GIScience smart cities for smart citizens
#class in F2015, W2016

import os
import sys
import csv
import datetime
import time
import requests
from requests.exceptions import ConnectionError
import json
import glob
import RPi.GPIO as GPIO

#this may be unecessary
time.sleep(5) #pi seems to ignore some initial scripts sometimes unless it sleeps for a bit first

sleeptime = 10 #minutes: how often should Pi gather data

upstream = "1701279" #stream for upload speed
dnstream = "1701229" #stream for download speed
tmstream = "1701177" #stream for temperature stream
duststream = "1701332" #stream for dust sensor
noisestream = "1701382" #stream for noise level

ipstream = "1701686"
ipfeat = "1701682"

tmfeat = "1701156"
dnfeat = "1701208"
upfeat = "1701261"
dustfeat = "1701313"
noisefeat = "1701363"

token = "b1937bfb-c9fc-41e9-ae19-1b455f7a9443" #pg-sensorup api key
path = "/home/pi/" #path
pi_name = "pi13" #which pi is this?

#set these to false if the sensor is not in use
ip = True
temp = True
wifi = True
dust = True
noise= True

#Testing?
#will output values as it is read if testing
testing = False

#will print final results, and upload statuses
#Flase for minimal printing
prnt = True

#ignore the following variables unless there is change in wiring

#set GPIO readings to BCM
GPIO.setmode(GPIO.BCM)

#define and setup dust led pin
dustpin = 21
GPIO.setup(dustpin, GPIO.OUT) ## Setup GPIO Pin 7 to OUT

#setup ADC GPIO
DEBUG = 1
SPICLK = 18
SPIMISO = 23
SPIMOSI = 24
SPICS = 25
# set up the SPI interface pins
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)


#setup temperature sensor
if temp:
	os.system('modprobe w1-gpio')
	os.system('modprobe w1-therm')

	base_dir = '/sys/bus/w1/devices/'
	device_folder = glob.glob(base_dir + '28*')[0]
	device_file = device_folder + '/w1_slave'

#to get internet speeds

def ip():
	lol = os.popen("ifconfig").read()
	lel = lol.rstrip().split('\n')

	if len(lel) > 20:
		lul = lol.rstrip().split('\n')[18].rstrip().split(' ')[11]
	else:
		lul = lol.rstrip().split('\n')[1].rstrip().split(' ')[11]

	if prnt:
		print("ip address is:")
		print(lul)
		print(len(lel))
	upload(pi_name+lul,ipstream,ipfeat)

def test():
    #run speedtest-cli
    if prnt:
        print 'running test'
    a = os.popen("python /home/pi/speedtest-cli/speedtest_cli.py --simple").read()
    if prnt:
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
    upload(d,dnstream,dnfeat)
    upload(u,upstream,upfeat)


def upload(data,dstream,feat):
    #dstream=sys.argv[1]
    #data=sys.argv[2]
    #dstream=str(dstream)
    con_suc=True #success of connection
    data=str(data)
    dstream = str(dstream)
    url= 'http://chashuhotpot.sensorup.com/OGCSensorThings/v1.0/Datastreams('+dstream+')/Observations'
    headers= {
    "Content-Type":"application/json"
    }
    payload = {"result":data,"FeatureOfInterest":{"@iot.id":feat}}
    print(payload)
    try:
        r=requests.post(url, data=json.dumps(payload), headers=headers)
    except ConnectionError as e:
        print e
        r = "Check internet connection, or server status"
        con_suc= False #failed to connect
    if prnt:
        print(r)
    if con_suc:
        if prnt:
            print(r.text.rstrip().split("\n"))

#reads from ADC given ADC channel
def read_adc(adcnum):
	return	readadc(adcnum, SPICLK,SPIMOSI,SPIMISO,SPICS)



#from Sharp dust sensor datasheet, measurment is to occur 280 microseconds after LED is turned on
#from experimenting with arduino, it still works after 1000 microseconds, but becomes jittery after

#This is adcread, but the data is taken from ADC immediately after LED turns on
#Rpi b+ is much quicker than b, so there is a 100 microsecond sleep to wait for pulse
#Rpi b+ gets dust data in ~300-400 microseconds

#Raspberry pi b+ gets results comparable with arduino uno
#if using Rpi b, remove time.sleep(), but it will still get bad jittery results
def readadcdust(adcnum, clockpin, mosipin, misopin, cspin):
	#print("Measuring ADC")
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
	beg = time.time()
	#turn on the LED, and read from ADC immediately after
	GPIO.output(dustpin,False)
	#Rpi b+ is quicker than 280 microseconds, so sleep 100
	time.sleep(100.0/1000000.0)
	#this ADC reading process takes ~200 microseconds, good enough to get decent result
	#read in one empty bit, one null bit, and 10 ADC bits
	for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1
        GPIO.output(cspin, True)
	if testing:
		end = time.time()
		print((end-beg)*1000000)
	GPIO.output(dustpin,True)

        adcout >>= 1       # first bit is 'null' so drop it
        return adcout

def readadc(adcnum, clockpin, mosipin, misopin, cspin):
	#print("Measuring ADC")
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
        return adcout

def read_temp_raw():
	f = open(device_file, 'r')
	lines = f.readlines()
	f.close()
	return lines

def read_temp():
	lines = read_temp_raw()
	while lines[0].strip()[-3:] != 'YES':
		time.sleep(0.2)
		lines = read_temp_raw()
	equals_pos = lines[1].find('t=')
	if equals_pos != -1:
		temp_string = lines[1][equals_pos+2:]
		temp_c = float(temp_string) / 1000.0
		#degrees F if you want
		#temp_f = temp_c * 9.0 / 5.0 + 32.0

		print("\n\nTemperature: "+ str(temp_c))
		upload(temp_c,tmstream,tmfeat)
		out_file = open(path+'temp.csv','a')
		ts = time.time()
		writer = csv.writer(out_file)
		writer.writerow((ts*1000,temp_c))
		return temp_c#, temp_f

def read_dust(chan):
	#delay times i should be following but can't because pi can't
	voltavg = 0.0
	voltmax = 0.0
	for j in range(0,3):
		voltmax = 0
		for i in range(0,10):
			dustVal = readadcdust(chan, SPICLK,SPIMOSI,SPIMISO,SPICS) # read the dust value via pin chan of the ADC
			volt = dustVal*3.3/1023.0 #Rpi GPIO is 3.3V, and dust sensor and ADC are connected with 3.3V
			#equation derrived from dust sensor datasheet
			dust = 0.17 * volt - 0.1
			if voltmax < volt:
				voltmax = volt
			time.sleep(1)
			if testing:
				print("num: " + str(dustVal))
		voltavg = voltavg + voltmax
	voltfin = voltavg / 3.0
	#raspberry Pi voltage is jittery, and timing with sensor is not great, so the max is just taken instead of the average, it should be unlikely more than 3.3V is obtained
	#pi reading sensor seems to underestimate very much more often than overestimate from testing
	dust = 0.17 * voltavg -.1
#	print("voltage " + str(voltfin) +" Dust density: " + str(dust))
	if dust < 0.1: #dust sensor datasheet did not give information on anything under 0.5V or 0.1 mg/m^3 of dust
		dust = 0
	print("dust: " + str(dust))
	upload(str(dust),duststream,dustfeat)	

def read_noise(chan):
	sample_window = 50.0/1000.0 #s 50 ms means 20Hz right? and that should be good enough hopefully
	total_time = 30.0 #colelct data for how long?
	time_begin = time.time() #the time at the start of it all
	count = 0.0
	pk2pkavg = 0.0 #average of all peak to peaks
	while(time.time() - time_begin < total_time):
		max = 0.0 #smallest it can be, will for sure be overriden
		min = 1023.0 #largest it can be, will for sure be overriden
		begin_int = time.time() #current time at start of interval
		while (time.time()-begin_int < sample_window):
			sample = read_adc(chan)
			if sample > max:
				max = sample
			if sample < min:
				min = sample
		pk2pk = max - min #peak to peak of the signal
		pk2pkavg = pk2pk+pk2pkavg
		count = count+1
		if testing:
			print("Volume: "+ str(pk2pk))
	pk2pkavg = pk2pkavg/count
	if testing:
		print("count: " + str(count))
	print("noise: " + str(pk2pkavg))
	#not an electrical engineer
	#geo
	#dunno what i'm doing
	#this is how it works right?
	#what even makes this microphone electret
	#close enuf
	upload(str(int(pk2pkavg)),noisestream,noisefeat)


interval = 5
sleeptime = sleeptime*60
if ip:
	ip()

intervals = sleeptime/interval
while(True):
	init = int(time.time())
	if noise:
		read_noise(0)
	if dust:
		read_dust(1)
	if temp:
		read_temp()
	if wifi:
		test()

	fint = int(time.time())
	diff = abs(init - fint)
	print("Process took "+str(diff)+" seconds")
	print("Sleeping for " + str(sleeptime-diff) + " more seconds")
	time.sleep((sleeptime-diff)%interval)
	rmint = int((sleeptime-diff)/interval)
	while(rmint > 0):
		if prnt:
			print(str((intervals-rmint)*interval)+" seconds passed")
			print(str((rmint)*interval) + " seconds remaining")
		time.sleep(interval)
		rmint = rmint-1

