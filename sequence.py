
def create_aws_iot_sqs_resources():
    """Creates the complete IoT and SQS needed resources"""
    create_iot_thing()
    create_iot_rule()
    return True

def create_aws_db_resouces():
    pass


def create_aws_sqs_resouces():
    url = create_queue()
    arn = get_queue_arn(url)