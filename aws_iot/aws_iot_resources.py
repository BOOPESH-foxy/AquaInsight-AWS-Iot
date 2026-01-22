import time
from botocore.exceptions import ClientError
from aws_iot.aws_iot_iam_role import create_iot_to_sqs_role
from aws_clients import iot_client,iot_data_client

client = iot_client()
iot = iot_data_client()
query = f"SELECT * FROM 'water/quality/+/+/+/data'"

def create_iot_rule(url, role_arn):
    rule_name = 'aqua_data_route_rule'
    try:
        response = client.get_topic_rule(ruleName=rule_name)
        print(f"! IoT rule '{rule_name}' already exists")
        return response
    except ClientError as e:
        if e.response['Error']['Code'] != 'UnauthorizedException':  # Rule doesn't exist
            print(f":: Error checking IoT rule: {e}")
            raise
    
    max_retries = 3
    retry_delay = 10
    
    for attempt in range(max_retries):
        try:
            print(f"! Creating IoT rule (attempt {attempt + 1}/{max_retries})")
            response_rule_creation = client.create_topic_rule(
                ruleName=rule_name,
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
            print("+ IoT rule created successfully")
            return response_rule_creation
            
        except ClientError as e:
            if "unable to assume role" in str(e) and attempt < max_retries - 1:
                print(f"! Role not ready yet, waiting {retry_delay} seconds...")
                time.sleep(retry_delay)
                continue
            elif "ConflictException" in str(e):
                print("! IoT rule already exists (created during retry)")
                return None
            else:
                print(":: Error ::",e)
                raise
        except Exception as e:
            print(":: Error ::",e)
            raise

