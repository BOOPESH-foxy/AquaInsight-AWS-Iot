from aws_ecs.aws_ecs_task_role import create_ecs_task_role
from aws_ecs.aws_ecs_task_execution import create_ecs_task_execution_role
from aws_ecs.ecs_config import *
from aws_ecs.log_group import create_log_group


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
    """deploy ECS service using existing infrastructure"""
    subnet_ids = vpc_resource_list['subnet_ids']
    sg_id = vpc_resource_list['security_group_id']
    
    response = ecs.describe_task_definition(taskDefinition=TASK_FAMILY)
    task_definition_arn = response['taskDefinition']['taskDefinitionArn']
    
    create_ecs_service(task_definition_arn, subnet_ids, sg_id)
    print("+ ECS service deployed - containers are up !!")
