from aws_ecs.aws_ecs_task_role import create_ecs_task_role
from aws_ecs.aws_ecs_task_execution import create_ecs_task_execution_role
import botocore


def create_task_roles():
    create_ecs_task_role()
    create_ecs_task_execution_role()


def create_ecs_task_execution_role():
    pass


create_task_roles()