import os
import time
import typer
from aws_iot.aws_iot_resources import *
from aws_sqs.aws_sqs_resources import *
from aws_sns.aws_sns_resources import *
from aws_ecs.aws_ecs_resources import *
from botocore.exceptions import ClientError
from aws_ecs_infra.vpc import setup_ecs_infra
from sensor_data_operations import publish_sensor_data,mqtt_listener_client
from aws_influxdb.db_config import create_influxdb_instance, get_influxdb_status, get_influxdb_endpoint


app = typer.Typer(help="AWS IoT thing data processing - sensor")

@app.command("create_infrastructure")
def create_aws_resources():
    """create resources on the specified region"""
    
    url = create_queue()
    arn = get_queue_arn(url)
    sns_topics = create_district_topics()
    role_arn = create_iot_to_sqs_role(queue_arn=arn)
    
    print("! Waiting for IAM role to propagate...")
    time.sleep(15)
    
    response_rule_creation = create_iot_rule(url,role_arn)
    ecs_roles = create_task_roles(queue_arn=arn)

    vpc_resource_list = setup_ecs_infra()

    influxdb_instance = create_influxdb_instance(
        vpc_resource_list['subnet_ids'], 
        [vpc_resource_list['security_group_id']]
    )

    task_role_arn = ecs_roles[0]
    task_execution_role_arn = ecs_roles[1]
    create_ecs_infrastructure(vpc_resource_list,task_role_arn,task_execution_role_arn,url)
 


@app.command("deploy_ecs")
def deploy_ecs_only():
    """Deploy ECS service (start containers) when InfluxDB is ready"""
    
    print("=== Checking Prerequisites ===")
    
    status = get_influxdb_status()
    if status != 'AVAILABLE':
        print(f"InfluxDB not ready (status: {status})")
        print("Wait for InfluxDB to be AVAILABLE before deploying containers")
        return
    
    print("InfluxDB is ready")
    
    from aws_ecs_infra.vpc import get_vpc_resources
    try:
        vpc_resource_list = get_vpc_resources()
    except RuntimeError as e:
        print(f"{e}")
        print("Run: python main.py create_infrastructure first")
        return
    
    print("=== Deploying ECS Service ===")
    deploy_ecs_service(vpc_resource_list)

    
@app.command("stop_ecs")
def stop_ecs_service():
    """Stop ECS service (set desired count to 0)"""
    from aws_ecs.ecs_config import ecs, CLUSTER_NAME, SERVICE_NAME
    
    try:
        ecs.update_service(
            cluster=CLUSTER_NAME,
            service=SERVICE_NAME,
            desiredCount=0
        )
        print("- ECS service stopped (desired count = 0)")
    except Exception as e:
        print(f"! Error stopping service: {e}")


@app.command("start_ecs") 
def start_ecs_service():
    """Start ECS service (set desired count to 1)"""
    from aws_ecs.ecs_config import ecs, CLUSTER_NAME, SERVICE_NAME
    
    status = get_influxdb_status()
    if status != 'AVAILABLE':
        print(f"InfluxDB not ready (status: {status})")
        return
    
    try:
        ecs.update_service(
            cluster=CLUSTER_NAME,
            service=SERVICE_NAME,
            desiredCount=1
        )
        print("+ ECS service started (desired count = 1)")
    except Exception as e:
        print(f"! Error starting service: {e}")


@app.command("check_influxdb")
def check_influxdb_status():
    """Check InfluxDB instance status and get endpoint"""

    print("Checking InfluxDB status...")
    status = get_influxdb_status()
    if status == 'AVAILABLE':
        endpoint = get_influxdb_endpoint()
        print(f"AquaInsight setup done! InfluxDB ready at: {endpoint}")
    elif status == 'not-found':
        print("InfluxDB instance not found. Check if creation failed.")
    elif status is None:
        print("Error checking InfluxDB status")
    else:
        print(f"InfluxDB status: {status}")
    

@app.command("publish_data")
def publish_sensor_data_typer():
    """Starts publishing the sensor data to AWS IoT thing"""
    publish_sensor_data.publish_sensor_data_iot()


@app.command("iot_listener")
def listener_sensor_data_typer():
    """Starts listening to AWS IoT topic - response from ECS"""
    mqtt_listener_client.topic_listener()


@app.command("debug_influxdb")
def debug_influxdb():
    """Debug InfluxDB creation issues"""
    from aws_influxdb.db_config import INFLUX_DB_INSTANCE_NAME
    from aws_clients import timestream_influxdb_client
    
    client = timestream_influxdb_client()
    
    print(f"Looking for InfluxDB instance: {INFLUX_DB_INSTANCE_NAME}")
    print(f"Region: {os.getenv('REGION')}")
    
    try:
        response = client.list_db_instances()
        instances = response.get('items', [])
        
        print(f"\nFound {len(instances)} InfluxDB instances:")
        for instance in instances:
            print(f"- Name: {instance['name']}")
            print(f"  Status: {instance['status']}")
            print(f"  Type: {instance['dbInstanceType']}")
            print()
            
        if not instances:
            print("No InfluxDB instances found in this region")
            
    except Exception as e:
        print(f"Error listing instances: {e}")

if __name__ == "__main__":
    app()