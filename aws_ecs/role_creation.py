import json
import time
from botocore.exceptions import ClientError
from aws_clients import iam_client
client = iam_client()


def check_role_existence(role_name="ecs_aquaInsight"):
    """ Ensures an iam role exists for AWS IoT to send messages to SQS. Returns the role arn."""
    try:
        response_existense = client.get_role(RoleName=role_name)
        role_arn = response_existense["Role"]["Arn"]
        return role_arn
        
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchEntity":
            print(f"Role {role_name} not found. Creating...")
            return 0
