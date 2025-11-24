from aws_iot.aws_iot_resources import *
from aws_sqs.aws_sqs_resources import *

from sensor_data_operations import publish_sensor_data,mqtt_listener_client
from sequence import create_aws_iot_sqs_resources

import typer

app = typer.Typer(help="AWS IoT thing data processing - sensor")

@app.command("create_iot_resources")
def create_aws_iot_resources():
    """Create AWS thing on the specified region"""
    create_aws_iot_sqs_resources()

@app.command("create_rule")
def create_aws_rule_typer():
    """Creates IoT rule to send the received data to required AWS resources(such as s3,timestream etc)"""
    pass

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