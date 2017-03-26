#!/usr/bin/env python

#---------------------------------------------------------------------------------------
# Load configuration values
#
#---------------------------------------------------------------------------------------

# see https://wiki.python.org/moin/ConfigParserShootout
from configobj import ConfigObj
config = ConfigObj('pythonMqttPublisher.cfg')

print("{0}".format("Python MQTT Publisher"))


#---------------------------------------------------------------------------------------
# Modules and methods to support MQTT
#
#---------------------------------------------------------------------------------------

import paho.mqtt.client as mqtt

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc) :
	print("Connected with result code "+str(rc))
	# Subscribing in on_connect() means that if the connection is lost
	# the subscriptions will be renewed when reconnecting.
	# print("Subscribing to topics ...")
	# for topic in config['mqtt_topics']['TOPICS'] :
	# 	client.subscribe(topic)
	# 	print("{0}".format(topic))

def on_publish(client, userdata, mid) :
    print("mid: {0}".format(str(mid)))

def on_disconnect(client, userdata, rc) :
	print("Disconnect returned:")
	print("client: {0}".format(str(client)))
	print("userdata: {0}".format(str(userdata)))
	print("result: {0}".format(str(rc)))

def on_log(client, userdata, level, buf) :
    print("{0}".format(buf))

client               = mqtt.Client()
client.on_connect    = on_connect
client.on_publish    = on_publish
client.on_disconnect = on_disconnect
# Uncomment to enable debug messages
#client.on_log       = on_log

client.connect(
               config['mqtt_configuration']['MQTT_BROKER_IP'],
               int(config['mqtt_configuration']['MQTT_BROKER_PORT']),
               int(config['mqtt_configuration']['MQTT_BROKER_PORT_TIMEOUT']),
               )

client.loop_start()


#---------------------------------------------------------------------------------------
# Modules and methods to support namedTuple
#
#---------------------------------------------------------------------------------------

import collections

Measurement = collections.namedtuple('Measurement', 'temperature pressure')


#---------------------------------------------------------------------------------------
# Modules and methods to support bmp180
#
#---------------------------------------------------------------------------------------

from smbus import SMBus
from time import sleep
from ctypes import c_short

addr = 0x77
oversampling = 3        # 0..3

bus = SMBus(1);         # 0 for R-Pi Rev. 1, 1 for Rev. 2

# return two bytes from data as a signed 16-bit value
def get_short(data, index):
        return c_short((data[index] << 8) + data[index + 1]).value

# return two bytes from data as an unsigned 16-bit value
def get_ushort(data, index):
        return (data[index] << 8) + data[index + 1]

def bmp180measurement() :

	(chip_id, version) = bus.read_i2c_block_data(addr, 0xD0, 2)
	print "Chip Id:", chip_id, "Version:", version

	# Convert byte data to word values
	ac1 = get_short(cal, 0)
	ac2 = get_short(cal, 2)
	ac3 = get_short(cal, 4)
	ac4 = get_ushort(cal, 6)
	ac5 = get_ushort(cal, 8)
	ac6 = get_ushort(cal, 10)
	b1 = get_short(cal, 12)
	b2 = get_short(cal, 14)
	mb = get_short(cal, 16)
	mc = get_short(cal, 18)
	md = get_short(cal, 20)

	# Starting temperature conversion...
	bus.write_byte_data(addr, 0xF4, 0x2E)
	sleep(0.005)
	(msb, lsb) = bus.read_i2c_block_data(addr, 0xF6, 2)
	ut = (msb << 8) + lsb

	# Starting pressure conversion...
	bus.write_byte_data(addr, 0xF4, 0x34 + (oversampling << 6))
	sleep(0.04)
	(msb, lsb, xsb) = bus.read_i2c_block_data(addr, 0xF6, 3)
	up = ((msb << 16) + (lsb << 8) + xsb) >> (8 - oversampling)

	# Calculating temperature...
	x1 = ((ut - ac6) * ac5) >> 15
	x2 = (mc << 11) / (x1 + md)
	b5 = x1 + x2
	t = (b5 + 8) >> 4

	# Calculating pressure...
	b6 = b5 - 4000
	b62 = b6 * b6 >> 12
	x1 = (b2 * b62) >> 11
	x2 = ac2 * b6 >> 11
	x3 = x1 + x2
	b3 = (((ac1 * 4 + x3) << oversampling) + 2) >> 2

	x1 = ac3 * b6 >> 13
	x2 = (b1 * b62) >> 16
	x3 = ((x1 + x2) + 2) >> 2
	b4 = (ac4 * (x3 + 32768)) >> 15
	b7 = (up - b3) * (50000 >> oversampling)

	p = (b7 * 2) / b4
	#p = (b7 / b4) * 2

	x1 = (p >> 8) * (p >> 8)
	x1 = (x1 * 3038) >> 16

	x2 = (-7357 * p) >> 16
	p = p + ((x1 + x2 + 3791) >> 4)

	print "Temperature:", t/10.0, "C"
	print "Pressure:", p / 100.0, "hPa"

	measurement = Measurement(temperature=t/10.0, pressure=p/100.0)
	return(measurement)


#---------------------------------------------------------------------------------------
# Modules and methods to support publishing data in JSON format
#
#---------------------------------------------------------------------------------------

import json

def publish_measurements() :
	measurement = bmp180measurement()
	m = {'type': 'bmp180', 'temperature' : measurement.temperature, 'humidity' : measurement.pressure}
	print(json.dumps(m))
	client.publish("sensor/berryimu/measurements", json.dumps(m))


#---------------------------------------------------------------------------------------
# Main program methods
#
#---------------------------------------------------------------------------------------

def tidyupAndExit() :
	t.cancel()
	running = False       #Stop thread1
	# Disconnect mqtt client			mqttc.loop_stop()
	client.disconnect()
	print("Bye")
	exit(0)

from threading import Timer

def main() :
	try :
		t = Timer(float(config['PUBLISH_INTERVAL']), publish_measurements)
		t.start()
	except KeyboardInterrupt :      #Triggered by pressing Ctrl+C
		tidyupAndExit()

if __name__ == "__main__" : main()
