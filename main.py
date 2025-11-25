from aws_iot.aws_iot_resources import *
from aws_sqs.aws_sqs_resources import *
from aws_ecs.aws_ecs_resources import *
from aws_ecs_infra.vpc import setup_ecs_infra

from sensor_data_operations import publish_sensor_data,mqtt_listener_client

import typer

app = typer.Typer(help="AWS IoT thing data processing - sensor")

@app.command("create_infrastructure")
def create_aws_resources():
    """Create AWS resources on the specified region"""
    url = create_queue()
    arn = get_queue_arn(url)
    role_arn = create_iot_to_sqs_role(queue_arn=arn)
    response_rule_creation = create_iot_rule(url,role_arn)

    ecs_roles = create_task_roles(queue_arn=arn)

    vpc_resource_list =  setup_ecs_infra()

    task_role_arn = ecs_roles[0]
    task_execution_role_arn = ecs_roles[1]
    create_ecs_resources(vpc_resource_list,task_role_arn,task_execution_role_arn,url)


@app.command("publish_data")
def publish_sensor_data_typer():
    """Starts publishing the sensor data to AWS IoT thing"""
    publish_sensor_data.publish_sensor_data_iot()


@app.command("mqtt_listener")
def publish_sensor_data_typer():
    """Starts listening to AWS IoT topic - response from ECS"""
    mqtt_listener_client.topic_listener()

if __name__ == "__main__":
    app()