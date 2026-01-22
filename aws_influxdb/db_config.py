import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from aws_clients import timestream_influxdb_client

load_dotenv()

# InfluxDB Configuration
INFLUX_DB_INSTANCE_NAME = os.getenv("INFLUX_DB_INSTANCE_NAME")
INFLUX_DB_INSTANCE_TYPE = os.getenv("INFLUX_DB_INSTANCE_TYPE")
INFLUX_STORAGE_TYPE = os.getenv("INFLUX_STORAGE_TYPE")
INFLUX_ALLOCATED_STORAGE = int(os.getenv("INFLUX_ALLOCATED_STORAGE", "400"))
INFLUX_USERNAME = os.getenv("INFLUX_USERNAME")
INFLUX_PASSWORD = os.getenv("INFLUX_PASSWORD")
INFLUX_ORGANIZATION = os.getenv("INFLUX_ORGANIZATION")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")

client = timestream_influxdb_client()

def create_influxdb_instance(subnet_ids, security_group_ids):
    """Create Amazon Timestream for InfluxDB instance"""
    
    try:
        response = client.get_db_instance(identifier=INFLUX_DB_INSTANCE_NAME)
        print(f"! InfluxDB instance '{INFLUX_DB_INSTANCE_NAME}' already exists")
        return response['dbInstance']
        
    except ClientError as e:
        if e.response['Error']['Code'] != 'ResourceNotFoundFault':
            raise
    
    print(f"! Creating InfluxDB instance '{INFLUX_DB_INSTANCE_NAME}'...")
    
    try:
        response = client.create_db_instance(
            name=INFLUX_DB_INSTANCE_NAME,
            dbInstanceType=INFLUX_DB_INSTANCE_TYPE,
            dbStorageType=INFLUX_STORAGE_TYPE,
            allocatedStorage=INFLUX_ALLOCATED_STORAGE,
            vpcSubnetIds=subnet_ids,
            vpcSecurityGroupIds=security_group_ids,
            username=INFLUX_USERNAME,
            password=INFLUX_PASSWORD,
            organization=INFLUX_ORGANIZATION,
            bucket=INFLUX_BUCKET,
            publiclyAccessible=False,
            tags=[
                {'key': 'AquaInsight', 'value': 'InfluxDB'},
                {'key': 'Name', 'value': INFLUX_DB_INSTANCE_NAME}
            ]
        )
        
        print(f"+ Creating InfluxDB instance: {INFLUX_DB_INSTANCE_NAME}")
        print("! Instance creation initiated. This may take up to 20 minutes...")
        
        return response['dbInstance']
        
    except Exception as e:
        print(f":: Error creating InfluxDB instance: {e}")
        raise

def get_influxdb_endpoint():
    """get the influxDB instance endpoint"""

    try:
        response = client.get_db_instance(identifier=INFLUX_DB_INSTANCE_NAME)
        instance = response['dbInstance']
        
        if instance['status'] == 'available':
            endpoint = instance['endpoint']
            print(f"! InfluxDB endpoint: {endpoint}")
            return endpoint
        else:
            print(f"! InfluxDB instance status: {instance['status']}")
            return None
            
    except Exception as e:
        print(f":: Error getting InfluxDB endpoint: {e}")
        raise
