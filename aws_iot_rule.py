from aws_clients import iot_client
from tank_metadata import tankName
from aws_sqs_resources import create_queue
client = iot_client()


def create_iot_rule():
    try:
        url,arn = create_queue()
        print(url,arn)
        response_rule_creation = client.create_topic_rule(
            ruleName = 'aqua_data_route_rule',
            topicRulePayload={
                'sql': f'select * from {tankName}/quality/data',
                'description': 'string',
                'actions':[{
                    {
                    'roleArn': arn,
                    'queueUrl': url,
                    # 'useBase64': True|False
                    }
                }]
            }
        )
        
    except Exception as e:
        print(":: Error ::",e)
        raise

