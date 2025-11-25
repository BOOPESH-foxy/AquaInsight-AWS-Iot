from aws_ecs.aws_ecs_task_role import create_ecs_task_role
from aws_ecs.aws_ecs_task_execution import create_ecs_task_execution_role
from aws_ecs.ecs_config import *


def create_task_roles(queue_arn):
    task_role = create_ecs_task_role(queue_arn)
    task_exec_role = create_ecs_task_execution_role()
    return task_role,task_exec_role


def create_ecs_resources(vpc_resource_list,task_role_arn,task_execution_role_arn,queue_url):
    data = vpc_resource_list
    print(vpc_resource_list)
    subnet_ids = vpc_resource_list[0]
    sg_id = vpc_resource_list[1]
    cluster_arn = create_cluster()
    image_uri = get_image_uri()
    task_definition_arn = register_task_definition(image_uri,task_role_arn,task_execution_role_arn,queue_url)
    ecs_service = create_ecs_service(task_definition_arn,subnet_ids,sg_id)