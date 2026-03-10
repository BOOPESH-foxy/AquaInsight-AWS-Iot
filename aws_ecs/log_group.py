from botocore.exceptions import ClientError
from aws_clients import logs_client
import os
from config_manager import get_config

LOG_GROUP = get_config("LOG_GROUP", "/aquainsight/ecs/log-group")

logs = logs_client()

def create_log_group():
    try:
        logs.create_log_group(logGroupName=LOG_GROUP)
        print(f"+ Created log group {LOG_GROUP}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceAlreadyExistsException":
            print(f"! Log group {LOG_GROUP} already exists")
        else:
            print(":: Error creating log group ::", e)
            raise