import os
import boto3
import botocore
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv('REGION')

iot_client = boto3.client('iot',region_name = REGION)