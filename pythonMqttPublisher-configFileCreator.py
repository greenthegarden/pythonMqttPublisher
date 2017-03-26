#!/usr/bin/env python3


# config file creator


from configobj import ConfigObj


config = ConfigObj()
config.filename = 'pythonMqttPublisher.cfg'


mqtt_configuration = {
	'MQTT_BROKER_IP'           : "192.168.1.52",
	'MQTT_BROKER_PORT'         : "1883",
	'MQTT_BROKER_PORT_TIMEOUT' : "60",
	}
config['mqtt_configuration'] = mqtt_configuration

# interval in seconds
config['PUBLISH_INTERVAL'] = 300


config.write()
