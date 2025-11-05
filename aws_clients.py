import os
import boto3
import botocore
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