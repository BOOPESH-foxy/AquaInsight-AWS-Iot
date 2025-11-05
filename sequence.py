from aws_iot.aws_iot_resources import create_iot_thing,create_iot_rule

def create_aws_iot_sqs_resources():
    """Creates the complete IoT and SQS needed resources"""
    create_iot_thing()
    create_iot_rule()
    return True

def create_aws_db_resouces():
    pass
