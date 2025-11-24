from aws_ecs.aws_ecs_task_role import create_ecs_task_role
from aws_ecs.aws_ecs_task_execution import create_ecs_task_execution_role


def create_task_roles(queue_arn):
    create_ecs_task_role(queue_arn)
    create_ecs_task_execution_role()


def create_ecs_resources():
    pass