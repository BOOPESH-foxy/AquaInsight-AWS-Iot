import json
import time
from botocore.exceptions import ClientError
from aws_clients import iam_client
client = iam_client()

def check_role_existence(role_name: str = "ecs_task_role"):
    """Check if an IAM role exists. Return its ARN if it exists, else None."""
    try:
        response_existence = client.get_role(RoleName=role_name)
        role_arn = response_existence["Role"]["Arn"]
        return role_arn
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            print(f"Role {role_name} not found. Creating...")
            return None
        raise


def create_ecs_task_role(queue_arn: str, role_name: str = "ecs_task_role") -> str:
    """Checks for existence and, in absence, creates an IAM role for AWS ECS to perform operations on SQS and Timestream. Returns the role ARN."""

    role_arn = check_role_existence(role_name)
    if role_arn:
        print("! Role exists")
        return role_arn

    try:
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                }
            ],
        }

        response_role_creation = client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Role for AWS ECS to perform operations on queue and db",
        )
        role_arn = response_role_creation["Role"]["Arn"]

        policy_name = f"{role_name}-ecs-tasks"
        policy_doc = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "SqsReadAndWrite",
                    "Effect": "Allow",
                    "Action": [
                        "sqs:DeleteMessage",
                        "sqs:ReceiveMessage",
                        "sqs:GetQueueAttributes",
                        "sqs:ChangeMessageVisibility",
                        "sqs:GetQueueUrl",
                    ],
                    "Resource": queue_arn,
                },
                {
                    "Sid": "TimestreamWrite",
                    "Effect": "Allow",
                    "Action": [
                        "timestream:WriteRecords",
                        "timestream:DescribeEndpoints",
                        "timestream-influxdb:GetDbInstance",
                        "timestream-influxdb:ListDbInstances"
                    ],
                    "Resource": "*",
                },
            ],
        }

        client.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_doc),
        )

        time.sleep(3)

        role_existence = check_role_existence(role_name)
        if not role_existence:
            raise RuntimeError(
                f"Role {role_name} was created but could not be retrieved."
            )
        else:
            print("+ Created Role ")
            return role_existence

    except Exception as e:
        print(":: Error ::", e)
        raise
