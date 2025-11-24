from aws_iot.aws_iot_iam_role import create_iot_to_sqs_role
from aws_clients import iot_client,iot_data_client

client = iot_client()
iot = iot_data_client()
query = f"SELECT * FROM 'water/quality/+/+/+/data'"

def create_iot_rule(url,role_arn):
    try:
        response_rule_creation = client.create_topic_rule(
            ruleName = 'aqua_data_route_rule',
            topicRulePayload={
                'sql': query,
                'description': 'queue - water quality parameter',
                'actions':[{
                'sqs':{
                    'roleArn': role_arn,
                    'queueUrl': url,
                    }
            }]
            }
        )

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
