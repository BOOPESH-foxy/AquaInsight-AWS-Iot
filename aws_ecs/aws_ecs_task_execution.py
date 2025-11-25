import json
from aws_clients import iam_client
from botocore.exceptions import ClientError

client = iam_client()


def check_execution_role_existence(role_name: str = "ecsTaskExecutionRole"):
    """Check if an ECS task execution role exists. Return its ARN if it exists, else None."""
    try:
        response = client.get_role(RoleName=role_name)
        return response["Role"]["Arn"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            print(f"Execution role {role_name} not found.")
            return None
        raise


def create_ecs_task_execution_role(role_name: str = "ecsTaskExecutionRole") -> str:
    """ Ensure an ECS task Execution role exists.
    - Trusts ecs-tasks.amazonaws.com
    - Has AmazonECSTaskExecutionRolePolicy attached 
    returns the role ARN."""

    role_arn = check_execution_role_existence(role_name)
    if role_arn:
        print(f"! Execution role {role_name} already exists")
        return role_arn

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

    try:
        response = client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Task execution role for ECS to pull images from ECR and push logs to cloudwatch",
        )
        role_arn = response["Role"]["Arn"]

        client.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
        )

        print(f"+ Created ECS task execution role: {role_name}")
        return role_arn

    except Exception as e:
        print(":: Error creating ECS task execution role ::", e)
        raise
