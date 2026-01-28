from aws_ecs.ecs_config import *
from aws_ecs.log_group import create_log_group
from aws_ecs.aws_ecs_task_role import create_ecs_task_role
from aws_influxdb.db_config import get_influxdb_endpoint
from aws_ecs.aws_ecs_task_execution import create_ecs_task_execution_role


def create_task_roles(queue_arn):
    """create ECS task role and execution role"""
    task_role = create_ecs_task_role(queue_arn)
    task_exec_role = create_ecs_task_execution_role()
    return task_role, task_exec_role


def create_ecs_infrastructure(vpc_resource_list, task_role_arn, task_execution_role_arn, queue_url):
    """create all ECS infrastructure (NO service deployment)"""
    create_log_group()
    create_cluster()
    ensure_ecr_repository()
    
    image_uri = get_image_uri()
    register_task_definition(image_uri, task_role_arn, task_execution_role_arn, queue_url)
    
    print("+ ECS infrastructure ready (cluster, ECR, task definition)")


def deploy_ecs_service(vpc_resource_list):
    """Deploy ECS service using existing infrastructure"""
    
    subnet_ids = vpc_resource_list['subnet_ids']
    sg_id = vpc_resource_list['security_group_id']
    
    existing_influx_url = os.getenv("INFLUX_URL")
    
    if existing_influx_url:
        print(f"Using existing InfluxDB from .env: {existing_influx_url}")
        influxdb_endpoint = existing_influx_url
    else:
        influxdb_endpoint = get_influxdb_endpoint()
        if not influxdb_endpoint:
            raise RuntimeError("InfluxDB endpoint not available and no existing URL in .env")
    
    response = ecs.describe_task_definition(taskDefinition=TASK_FAMILY)
    current_task = response['taskDefinition']
    
    task_role_arn = current_task['taskRoleArn']
    execution_role_arn = current_task['executionRoleArn']
    
    queue_url = None
    for env_var in current_task['containerDefinitions'][0]['environment']:
        if env_var['name'] == 'SQS_QUEUE_URL':
            queue_url = env_var['value']
            break
    
    image_uri = get_image_uri()
    task_definition_arn = register_task_definition(
        image_uri, task_role_arn, execution_role_arn, queue_url, influxdb_endpoint
    )
    
    create_ecs_service(task_definition_arn, subnet_ids, sg_id)
    print("+ ECS service deployed - containers are up !!")
