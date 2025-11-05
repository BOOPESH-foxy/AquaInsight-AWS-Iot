from aws_clients import iot_client
from tank_metadata import tankName
from aws_sqs_resources import create_queue,get_queue_arn
from aws_iam_role import create_iot_to_sqs_role
client = iot_client()
query = f"SELECT * FROM '{tankName}/quality/data'"


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
        print(ruleId)

    except Exception as e:
        print(":: Error ::",e)
        raise

create_iot_rule()