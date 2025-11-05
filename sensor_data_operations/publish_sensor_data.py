import time
import json
from tank_metadata import tankId,district,village
from aws_clients import iot_data_client
from generate_sensor_data import generate_sensor_data

iot = iot_data_client()

def publish_sensor_data_iot():
    """Generates mimiced sensor data and sends it to AWS IoT core"""
    try:
        while(True):
            response_data = generate_sensor_data()
            topic = f"water/quality/{district}/{village}/{tankId}/data"
            payload = json.dumps(response_data)

            json_response = iot.publish(topic=topic,qos=1,payload=payload)
            print(f"Data sent to AWS IoT: {response_data}")
            time.sleep(5)

    except Exception as e:
        print(":: Error ::",e)
        raise


