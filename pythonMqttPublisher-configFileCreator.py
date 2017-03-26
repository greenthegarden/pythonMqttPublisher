# config file creator

from configobj import ConfigObj
config = ConfigObj()
config.filename = 'pythonMqttPublisher.cfg'


# mqtt configuration
mqtt_configuration = {
	'MQTT_BROKER_IP'           : "192.168.1.52",
	'MQTT_BROKER_PORT'         : "1883",
	'MQTT_BROKER_PORT_TIMEOUT' : "60",
	}
config['mqtt_configuration'] = mqtt_configuration

config['PUBLISH_INTERVAL'] = 15.0


config.write()
