import os
import json
from dotenv import load_dotenv
from awscrt import io,mqtt
from awsiot import mqtt_connection_builder
from sensor_data_operations.tank_metadata import topic,endpoint

load_dotenv()

endpoint = os.getenv("ENDPOINT")

def response_message_processor(payload):
    try:
        data = json.loads(payload.decode("utf-8"))
    except json.JSONDecodeError:
        print("  Raw payload:", payload)
        return 
    
    print("  Payload:", json.dumps(data, indent=2))
    cl_actions = data.get("command")
    if(cl_actions == "Dispense Cl"):
        pass
    elif(cl_actions == "No-changes"):
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