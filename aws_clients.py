import os
import boto3
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv('REGION')

def iot_data_client():
    return boto3.client('iot-data',region_name = REGION)

def iot_client():
    return boto3.client('iot',region_name = REGION)

def sqs_client():
    return boto3.client('sqs',region_name=REGION)

def iam_client():
    return boto3.client('iam',region_name=REGION)

def timestream_influxdb_client():
    return boto3.client('timestream-influxdb', region_name=REGION)

def ec2_client():
    return boto3.client('ec2',region_name = REGION)

def ec2_resource():
    return boto3.resource('ec2')

def ecs_client():
    return boto3.client("ecs")

def ecr_client():
    return boto3.client("ecr")

def logs_client():
    return boto3.client("logs")