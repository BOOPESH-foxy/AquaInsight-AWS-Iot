from awsiot import mqtt_connection_builder
from awscrt import io,mqtt
from sensor_data_operations.tank_metadata import topic,endpoint


def response_message_processor():
    pass

def main():
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint = endpoint,
        keep_alive_secs=30
    )

    connection = mqtt_connection.connect()
    connection.result()

    response_subscriber = mqtt_connection.subscribe(
        topic = topic,
        qos = mqtt.QoS.AT_LEAST_ONCE,
        callback = response_message_processor()
    )