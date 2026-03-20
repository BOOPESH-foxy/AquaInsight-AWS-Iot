import os
from botocore.exceptions import ClientError
from aws_clients import ssm_client

ssm = ssm_client()

def put_parameter(name, value, parameter_type='String', description='', overwrite=True):
    """ Create or update an SSM parameter """

    try:
        response = ssm.put_parameter(
            Name=name,
            Value=value,
            Type=parameter_type,
            Description=description,
            Overwrite=overwrite
        )
        print(f"+ Created/Updated SSM parameter: {name}")
        return response
    except Exception as e:
        print(f":: Error creating parameter {name}: {e}")
        raise

def get_parameter(name, decrypt=True):
    """ Get a single parameter from SSM """

    try:
        response = ssm.get_parameter(Name=name, WithDecryption=decrypt)
        return response['Parameter']['Value']
    except ClientError as e:
        if e.response['Error']['Code'] == 'ParameterNotFound':
            return None
        print(f":: Error getting parameter {name}: {e}")
        raise

def get_parameters_by_path(path, decrypt=True):
    """ Get multiple parameters by path prefix """
    try:
        parameters = {}
        paginator = ssm.get_paginator('get_parameters_by_path')
        
        for page in paginator.paginate(Path=path, Recursive=True, WithDecryption=decrypt):
            for param in page['Parameters']:
                # Remove the path prefix to get just the parameter name
                param_name = param['Name'].replace(path, '').lstrip('/')
                parameters[param_name] = param['Value']
        
        return parameters
    except Exception as e:
        print(f":: Error getting parameters by path {path}: {e}")
        raise

def populate_ssm_from_env():
    """ Populate SSM Parameter Store with values from .env file """
    from dotenv import load_dotenv
    load_dotenv()
    
    print("! Populating SSM Parameter Store ")
    
    # Infrastructure parameters
    parameters = [
        ('REGION', '/aquainsight/infrastructure/region', 'AWS Region'),
        ('ACCOUNT_ID', '/aquainsight/infrastructure/account-id', 'AWS Account ID'),
        
        # VPC parameters
        ('VPC_NAME', '/aquainsight/vpc/name', 'VPC Name'),
        ('CIDR_BLOCK', '/aquainsight/vpc/cidr-block', 'VPC CIDR Block'),
        ('SECURITY_GROUP_NAME', '/aquainsight/vpc/security-group-name', 'Security Group Name'),
        ('SUBNET_CIDR_BLOCKS', '/aquainsight/vpc/subnet-cidr-blocks', 'Subnet CIDR Blocks'),
        
        # ECS parameters
        ('ECS_CLUSTER_NAME', '/aquainsight/ecs/cluster-name', 'ECS Cluster Name'),
        ('ECS_SERVICE_NAME', '/aquainsight/ecs/service-name', 'ECS Service Name'),
        ('ECS_TASK_FAMILY', '/aquainsight/ecs/task-family', 'ECS Task Family'),
        ('ECR_REPOSITORY', '/aquainsight/ecs/ecr-repository', 'ECR Repository Name'),
        ('LOG_GROUP', '/aquainsight/ecs/log-group', 'CloudWatch Log Group'),
        
        # InfluxDB parameters
        ('INFLUX_DB_INSTANCE_NAME', '/aquainsight/influxdb/instance-name', 'InfluxDB Instance Name'),
        ('INFLUX_DB_INSTANCE_TYPE', '/aquainsight/influxdb/instance-type', 'InfluxDB Instance Type'),
        ('INFLUX_STORAGE_TYPE', '/aquainsight/influxdb/storage-type', 'InfluxDB Storage Type'),
        ('INFLUX_ALLOCATED_STORAGE', '/aquainsight/influxdb/allocated-storage', 'InfluxDB Allocated Storage'),
        ('INFLUX_USERNAME', '/aquainsight/influxdb/username', 'InfluxDB Username'),
        ('INFLUX_PASSWORD', '/aquainsight/influxdb/password', 'InfluxDB Password'),
        ('INFLUX_ORGANIZATION', '/aquainsight/influxdb/organization', 'InfluxDB Organization'),
        ('INFLUX_BUCKET', '/aquainsight/influxdb/bucket', 'InfluxDB Bucket'),
        
        # IoT parameters
        ('ENDPOINT', '/aquainsight/iot/endpoint', 'IoT Endpoint'),
        
        # SNS parameters
        ('SNS_TIRUPPUR_EMAILS', '/aquainsight/sns/tiruppur-emails', 'Tiruppur Email Subscribers'),
        ('SNS_KARUR_EMAILS', '/aquainsight/sns/karur-emails', 'Karur Email Subscribers'),
        ('SNS_GENERAL_EMAILS', '/aquainsight/sns/general-emails', 'General Email Subscribers'),
    ]
    
    created_count = 0
    for env_key, ssm_path, description in parameters:
        env_value = os.getenv(env_key)
        if env_value:
            try:
                put_parameter(ssm_path, env_value, description=description)
                created_count += 1
            except Exception as e:
                print(f"! Failed to create {ssm_path}: {e}")
        else:
            print(f"! Skipping {env_key} (not found in .env)")
    
    print(f"+ Created {created_count} SSM parameters")
    print("! SSM Parameter Store populated successfully")
    return created_count