import os
from dotenv import load_dotenv

from aws_clients import ecs_client
from aws_ecs_infra.vpc import setup_ecs_infra

load_dotenv()

ecs = ecs_client()
image_tag = 'latest'

AWS_REGION       = os.getenv("REGION")
ACCOUNT_ID       = os.getenv("ACCOUNT_ID")
ECR_REPOSITORY   = os.getenv("ECR_REPOSITORY")

CLUSTER_NAME     = os.getenv("ECS_CLUSTER_NAME")
SERVICE_NAME     = os.getenv("ECS_SERVICE_NAME")
TASK_FAMILY      = os.getenv("ECS_TASK_FAMILY")


def get_image_uri():
    """Compose ECR image URI: {account}.dkr.ecr.{region}.amazonaws.com/{repo}:{tag}"""

    if not ACCOUNT_ID:
        raise RuntimeError("ACCOUNT_ID must be set in .env")
    return f"{ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com/{ECR_REPOSITORY}:{image_tag}"


def ensure_cluster(cluster_name):
    """Ensure ECS cluster exists, return its ARN."""

    response = ecs.describe_clusters(clusters=[cluster_name])
    clusters = response.get("clusters", [])
    if clusters and clusters[0]["status"] == "ACTIVE":
        print(f"! ECS cluster '{cluster_name}' already exists")
        return clusters[0]["clusterArn"]

    print(f"! Creating ECS cluster '{cluster_name}'...")
    response = ecs.create_cluster(clusterName=cluster_name)
    cluster_arn = response["cluster"]["clusterArn"]
    print(f"+ Created cluster {cluster_name} ({cluster_arn})")
    return cluster_arn


def register_task_definition(image_uri, task_role_arn, task_execution_role_arn, queue_url):
    """Register (or re-register) a Fargate task definition for the worker. Returns the task definition ARN."""
    
    if not task_role_arn or not task_execution_role_arn:
        raise RuntimeError("ECS_TASK_ROLE_ARN and ECS_EXEC_ROLE_ARN must be set in .env")

    if not queue_url:
        raise RuntimeError("SQS_QUEUE_URL must be set in .env")

    print(f"! Registering task definition family '{TASK_FAMILY}' with image {image_uri}")

    response = ecs.register_task_definition(
        family=TASK_FAMILY,
        requiresCompatibilities=["FARGATE"],
        networkMode="awsvpc",
        cpu="256",    
        memory="512",  
        taskRoleArn=task_role_arn,
        executionRoleArn=task_execution_role_arn,
        containerDefinitions=[
            {
                "name": "aqua-container",
                "image": image_uri,
                "essential": True,
                "command": ["python", "main.py", "start_queue_processor"],
                "environment": [
                    {"name": "AWS_REGION", "value": AWS_REGION},
                    {"name": "SQS_QUEUE_URL", "value": queue_url},
                ],
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": "/ecs/aqua-container",
                        "awslogs-region": AWS_REGION,
                        "awslogs-stream-prefix": "aqua",
                    },
                },
            }
        ],
        runtimePlatform={
            "cpuArchitecture": "X86_64",
            "operatingSystemFamily": "LINUX",
        },
    )

    task_def_arn = response["taskDefinition"]["taskDefinitionArn"]
    print(f"+ Registered task definition: {task_def_arn}")
    return task_def_arn


def create_ecs_service(cluster_name, task_def_arn: str, subnet_ids: list[str], sg_id: str):
    """Ensure an ECS service exists and is using the latest task definition."""

    response = ecs.describe_services(cluster=cluster_name, services=[SERVICE_NAME])
    services = response.get("services", [])

    network_conf = {
        "awsvpcConfiguration": {
            "subnets": subnet_ids,           
            "securityGroups": [sg_id],
            "assignPublicIp": "ENABLED",   
        }
    }

    if services and services[0]["status"] != "INACTIVE":
        print(f"! ECS service '{SERVICE_NAME}' already exists, updating...")
        ecs.update_service(
            cluster=cluster_name,
            service=SERVICE_NAME,
            taskDefinition=task_def_arn,
            desiredCount=1,
            networkConfiguration=network_conf,
        )
        print("+ Service updated.")
        return

    print(f"! Creating ECS service '{SERVICE_NAME}'...")
    ecs.create_service(
        cluster=cluster_name,
        serviceName=SERVICE_NAME,
        taskDefinition=task_def_arn,
        desiredCount=1,
        launchType="FARGATE",
        networkConfiguration=network_conf,
    )
    print("+ Service created.")
