import json
from aws_clients import iam_client
client = iam_client()

def ensure_iot_to_sqs_role(queue_arn, role_name = "iot_to_sqs_role"):
    """ ensures an iam role exists for AWS IoT to send messages to SQS. Returns the role arn."""
    try:
        response_existense = client.get_role(role_name)
        print(f"Reusing existing role: {role_name}")
        return response_existense["Role"]["Arn"]
    except Exception as e:
        print(f"Role {role_name} not found. Creating...")

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "iot.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }

    response_role_creation = client.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description="Role for AWS IoT Core to send messages to SQS",
    )
    role_arn = response_role_creation["Role"]["Arn"]
    
    policy_name = f"{role_name}-sqs-access"
    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "sqs:SendMessage",
                    "sqs:GetQueueAttributes",
                    "sqs:GetQueueUrl",
                ],
                "Resource": queue_arn,
            }
        ],
    }

    client.put_role_policy(
        RoleName=role_name,
        PolicyName=policy_name,
        PolicyDocument=json.dumps(policy_doc),
    )

    return role_arn
