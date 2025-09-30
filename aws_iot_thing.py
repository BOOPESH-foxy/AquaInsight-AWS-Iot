from aws_iot_core import iot_client

iot = iot_client

def create_aws_thing():
    response_create_thing = iot.create_thing(
        thingName = 'AquaInsight'
    )
    thing_id = response_create_thing["thingId"]
    return thing_id
