import boto3
import json
from botocore.exceptions import ClientError

iam = boto3.client("iam")


def ensure_iot_to_sqs_role(queue_arn, role_name = "iot_to_sqs_role"):
    """ ensures an iam role exists for AWS IoT to send messages to SQS. Returns the role arn."""
    try:
        response_existense = iam.get_role(role_name)
        print(f"Reusing existing role: {role_name}")
        return response_existense["Role"]["Arn"]
    except ClientError as e:
        print(":: Error ::",e)
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

    response_role_creation = iam.create_role(
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

    iam.put_role_policy(
        RoleName=role_name,
        PolicyName=policy_name,
        PolicyDocument=json.dumps(policy_doc),
    )

    print("+ Attached inline policy for SQS access")
    return role_arn
