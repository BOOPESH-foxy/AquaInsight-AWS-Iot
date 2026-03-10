import os
from botocore.exceptions import ClientError
from aws_clients import timestream_influxdb_client
from config_manager import get_config

INFLUX_DB_INSTANCE_NAME = get_config("INFLUX_DB_INSTANCE_NAME", "/aquainsight/influxdb/instance-name")
INFLUX_DB_INSTANCE_TYPE = get_config("INFLUX_DB_INSTANCE_TYPE", "/aquainsight/influxdb/instance-type")
INFLUX_STORAGE_TYPE = get_config("INFLUX_STORAGE_TYPE", "/aquainsight/influxdb/storage-type")
INFLUX_ALLOCATED_STORAGE = int(get_config("INFLUX_ALLOCATED_STORAGE", "/aquainsight/influxdb/allocated-storage", "400"))
INFLUX_USERNAME = get_config("INFLUX_USERNAME", "/aquainsight/influxdb/username")
INFLUX_PASSWORD = get_config("INFLUX_PASSWORD", "/aquainsight/influxdb/password")
INFLUX_ORGANIZATION = get_config("INFLUX_ORGANIZATION", "/aquainsight/influxdb/organization")
INFLUX_BUCKET = get_config("INFLUX_BUCKET", "/aquainsight/influxdb/bucket")

influxdb_client = timestream_influxdb_client()

def create_influxdb_instance(subnet_ids, security_group_ids):
    """Create Amazon Timestream for InfluxDB instance"""
    
    try:
        response = influxdb_client.get_db_instance(identifier=INFLUX_DB_INSTANCE_NAME)
        print(f"! InfluxDB instance '{INFLUX_DB_INSTANCE_NAME}' already exists")
        instance = response['dbInstance']
        
        if instance['status'] == 'available':
            endpoint = instance['endpoint']
            print(f"! InfluxDB endpoint: https://{endpoint}:8086")
            return instance
        else:
            print(f"! InfluxDB instance status: {instance['status']}")
            return instance
            
    except ClientError as e:
        if e.response['Error']['Code'] != 'ResourceNotFoundException':  # Fixed!
            raise
    
    print(f"=== Creating InfluxDB Instance ===")
    print(f"! Creating InfluxDB instance '{INFLUX_DB_INSTANCE_NAME}'...")
    
    try:
        response = influxdb_client.create_db_instance(
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
            publiclyAccessible=True,
            tags={ 
                'AquaInsight': 'InfluxDB',
                'Name': INFLUX_DB_INSTANCE_NAME
            }
        )
        
        print(f"+ Created InfluxDB instance: {INFLUX_DB_INSTANCE_NAME}")
        print("! Instance creation initiated (takes ~20 minutes)")
        
        return response.get('dbInstance', response)
        
    except Exception as e:
        print(f":: Error creating InfluxDB instance: {e}")
        raise

def get_influxdb_endpoint():
    """Get the InfluxDB instance endpoint"""
    try:
        response = influxdb_client.list_db_instances()
        instances = response.get('items', [])
        
        for instance in instances:
            if instance['name'] == INFLUX_DB_INSTANCE_NAME:
                if instance['status'] == 'AVAILABLE':
                    endpoint = instance['endpoint']
                    print(f"! InfluxDB endpoint: https://{endpoint}:8086")
                    return f"https://{endpoint}:8086"
                else:
                    print(f"! InfluxDB instance status: {instance['status']}")
                    return None
        
        print(f"! InfluxDB instance '{INFLUX_DB_INSTANCE_NAME}' not found")
        return None
            
    except Exception as e:
        print(f":: Error getting InfluxDB endpoint: {e}")
        raise


def get_influxdb_status():
    """Get the current status of InfluxDB instance"""
    try:
        response = influxdb_client.list_db_instances()
        instances = response.get('items', [])
        
        for instance in instances:
            if instance['name'] == INFLUX_DB_INSTANCE_NAME:
                return instance['status']
        
        return 'not-found'
        
    except ClientError as e:
        print(f":: Error getting InfluxDB status: {e}")
        return None
    except Exception as e:
        print(f":: Error getting InfluxDB status: {e}")
        return None


