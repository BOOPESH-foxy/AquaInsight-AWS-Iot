import boto3
import botocore

iot_client = boto3.client('iot')

iot_resource = boto3.resource('iot')