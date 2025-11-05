from aws_iot.aws_iot_iam_role import create_iot_to_sqs_role
from aws_clients import iot_client,iot_data_client
from aws_sqs.aws_sqs_resources import create_queue,get_queue_arn

client = iot_client()
iot = iot_data_client()
query = f"SELECT * FROM 'water/quality/+/+/+/data'"

def create_iot_rule():
    try:
        url = create_queue()
        queue_arn = get_queue_arn(url)
        arn = create_iot_to_sqs_role(queue_arn)
        response_rule_creation = client.create_topic_rule(
            ruleName = 'aqua_data_route_rule',
            topicRulePayload={
                'sql': query,
                'description': 'queue - water quality parameter',
                'actions':[{
                'sqs':{
                    'roleArn': arn,
                    'queueUrl': url,
                    }
            }]
            }
        )
        ruleId = response_rule_creation

    except Exception as e:
        print(":: Error ::",e)
        raise

def create_iot_thing():
    """Creates thing if not exists with specified name and prints the created id else prints the id if a thing exists with the given name"""
    try:
        response_create_thing = client.create_thing(
            thingName = 'AquaInsight'
        )
        thing_id = response_create_thing["thingId"]
        return thing_id

    except Exception as e:
        print(":: Error ::",e)
        raise
