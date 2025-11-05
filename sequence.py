from aws_iot_thing import create_aws_thing
from aws_iot_rule import create_iot_rule

def create_aws_iot_sqs_resources():
    """Creates the complete IoT and SQS needed resources"""
    create_aws_thing()
    create_iot_rule()
    return True

def create_aws_db_resouces():
    pass
