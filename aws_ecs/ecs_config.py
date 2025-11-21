from aws_clients import *
from aws_ecs.aws_ecs_task_role import create_ecs_task_role
import botocore


def create_task_role():
    create_ecs_task_role()


def create_ecs_task_execution_role():
    pass