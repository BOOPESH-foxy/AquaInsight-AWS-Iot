import typer
import time
from aws_iot.aws_iot_resources import *
from aws_sqs.aws_sqs_resources import *
from aws_ecs.aws_ecs_resources import *
from botocore.exceptions import ClientError
from aws_ecs_infra.vpc import setup_ecs_infra
from aws_influxdb.db_config import create_influxdb_instance, get_influxdb_status, get_influxdb_endpoint
from sensor_data_operations import publish_sensor_data,mqtt_listener_client


app = typer.Typer(help="AWS IoT thing data processing - sensor")

@app.command("create_infrastructure")
def create_aws_resources():
    """create resources on the specified region"""

    url = create_queue()
    arn = get_queue_arn(url)
    role_arn = create_iot_to_sqs_role(queue_arn=arn)
    
    print("! Waiting for IAM role to propagate...")
    time.sleep(15)
    
    response_rule_creation = create_iot_rule(url,role_arn)

    ecs_roles = create_task_roles(queue_arn=arn)
    vpc_resource_list = setup_ecs_infra()
    
    print("\n=== Creating InfluxDB Instance ===")
    influxdb_instance = create_influxdb_instance(
        vpc_resource_list['subnet_ids'], 
        [vpc_resource_list['security_group_id']]
    )

    task_role_arn = ecs_roles[0]
    task_execution_role_arn = ecs_roles[1]
    create_ecs_resources(vpc_resource_list,task_role_arn,task_execution_role_arn,url)


@app.command("check_influxdb")
def check_influxdb_status():
    """Check InfluxDB instance status and get endpoint"""

    print("Checking InfluxDB status...")
    status = get_influxdb_status()
    
    if status == 'available':
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