from aws_clients import iot_client
from tank_metadata import tankName
from aws_sqs_resources import create_queue,get_queue_arn
client = iot_client()


def create_iot_rule():
    try:
        url = create_queue()
        arn = get_queue_arn(url)
        response_rule_creation = client.create_topic_rule(
            ruleName = 'aqua_data_route_rule',
            topicRulePayload={
                'sql': f'select * from {tankName}/quality/data',
                'description': 'string',
                'actions':[{
                    {
                    'roleArn': arn,
                    'queueUrl': url,
                    }
                }]
            }
        )

    except Exception as e:
        print(":: Error ::",e)
        raise

create_iot_rule()