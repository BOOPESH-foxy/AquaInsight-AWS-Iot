import json
import time
from tank_metadata import tankName
from aws_clients import iot_data_client

iot = iot_data_client()

def create_iot_thing():
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
