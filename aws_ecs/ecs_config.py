import os
from dotenv import load_dotenv
from aws_clients import ecs_client,ecr_client

load_dotenv()
ecr = ecr_client()
ecs = ecs_client()
image_tag = 'latest'

AWS_REGION       = os.getenv("REGION")
ACCOUNT_ID       = os.getenv("ACCOUNT_ID")
LOG_GROUP        = os.getenv("LOG_GROUP")
ECR_REPOSITORY   = os.getenv("ECR_REPOSITORY")
CLUSTER_NAME     = os.getenv("ECS_CLUSTER_NAME")
SERVICE_NAME     = os.getenv("ECS_SERVICE_NAME")
TASK_FAMILY      = os.getenv("ECS_TASK_FAMILY")
# QUEUE_URL        = os.getenv(queue_url)
# influxdb_endpoint= os.getenv(influxdb_endpoint)

def ensure_ecr_repository():
    """ensures ecr repository exists else creates one if it doesn't """
    
    try:
        response = ecr.describe_repositories(repositoryNames=[ECR_REPOSITORY])
        print(f"! ECR repository '{ECR_REPOSITORY}' already exists")
        return response['repositories'][0]['repositoryUri']

    except ecr.exceptions.RepositoryNotFoundException:
        print(f"! Creating ECR repository '{ECR_REPOSITORY}'...")
        response = ecr.create_repository(repositoryName=ECR_REPOSITORY)
        print(f"+ Created ECR repository: {ECR_REPOSITORY}")
        return response['repository']['repositoryUri']


def get_image_uri():
    """Compose ECR image URI: {account}.dkr.ecr.{region}.amazonaws.com/{repo}:{tag}"""

    if not ACCOUNT_ID:
        raise RuntimeError("ACCOUNT_ID must be set in .env")
    return f"{ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com/{ECR_REPOSITORY}:{image_tag}"


def create_cluster():
    """Ensure ECS cluster exists, return its ARN."""

    try:
        response = ecs.describe_clusters(
            clusters=[CLUSTER_NAME]
            )
        clusters = response.get("clusters", [])
        if clusters and clusters[0]["status"] == "ACTIVE":
            print(f"! ECS cluster '{CLUSTER_NAME}' already exists")
            return clusters[0]["clusterArn"]

        print(f"! Creating ECS cluster '{CLUSTER_NAME}'...")
        response = ecs.create_cluster(
            clusterName=CLUSTER_NAME,
            tags=[
                    {'key': 'AquaInsight', 'value': 'ECS'},
                    {'key': 'Name', 'value': CLUSTER_NAME}
                ]
            )

        cluster_arn = response["cluster"]["clusterArn"]
        print(f"+ Created cluster {CLUSTER_NAME}")
        return cluster_arn
    
    except Exception as e:
        raise e


def register_task_definition(image_uri, task_role_arn, task_execution_role_arn, queue_url):
    """Register (or re-register) a Fargate task definition for the worker. Returns the task definition ARN."""
    
    try:
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
                    "stopTimeout":30,
                    "healthCheck": {
                        "command": ["CMD-SHELL", "python -c 'import boto3; print(\"healthy\")'"],
                        "interval": 30,
                        "timeout": 5,
                        "retries": 3,
                        "startPeriod": 60
                    },                    
                "environment": [
                    {"name": "AWS_REGION", "value": AWS_REGION},
                    {"name": "SQS_QUEUE_URL", "value": queue_url},
                    {"name": "INFLUX_URL", "value": influxdb_endpoint},
                    {"name": "INFLUX_ORG", "value": "AquaInsight"},
                    {"name": "INFLUX_BUCKET", "value": "water-quality-data"},
                ],
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": LOG_GROUP,
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

        task_definition_arn = response["taskDefinition"]["taskDefinitionArn"]
        print(f"+ Registered task definition: {task_definition_arn}")
        return task_definition_arn

    except Exception as e:
        raise e

def create_ecs_service(task_definition_arn, subnet_ids, sg_id):
    """Ensure an ECS service exists and is using the latest task definition."""

    response = ecs.describe_services(cluster=CLUSTER_NAME, services=[SERVICE_NAME])
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
            cluster=CLUSTER_NAME,
            service=SERVICE_NAME,
            taskDefinition=task_definition_arn,
            desiredCount=1,
            networkConfiguration=network_conf,
        )
        print("+ Service updated.")
        return

    print(f"! Creating ECS service '{SERVICE_NAME}'...")
    ecs.create_service(
        cluster=CLUSTER_NAME,
        serviceName=SERVICE_NAME,
        taskDefinition=task_definition_arn,
        desiredCount=1,
        launchType="FARGATE",
        networkConfiguration=network_conf,
    )
    print("+ Service created.")
