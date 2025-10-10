import json
from tank_metadata import tankName
from aws_iot_core import iot_client
from sensor_data import generate_sensor_data

iot = iot_client

def create_aws_thing():
    """Creates thing if not exists with specified name and prints the created id else prints the id if a thing exists with the given name"""
    try:
        response_create_thing = iot.create_thing(
            thingName = 'AquaInsight'
        )
        thing_id = response_create_thing["thingId"]
        print("+ Thing Id ",thing_id)
        return thing_id

    except Exception as e:
        print(":: Error ::",e)
        raise

def publish_sensor_data_iot():
    
    response_data = generate_sensor_data()
    topic = f"{tankName}/quality/data"
    payload = json.dumps(response_data)

    json_response = iot_client.publish(topic=topic,qos=1,payload=payload)
    print(f"Data sent to AWS IoT: {response_data}")


publish_sensor_data_iot()

