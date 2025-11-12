import os
import botocore
from dotenv import load_dotenv
from aws_clients import ec2_client

load_dotenv()
ec2 = ec2_client()

SECURITY_GROUP_NAME = os.getenv('SECURITY_GROUP_NAME')
VPC_NAME = os.getenv('VPC_NAME')
CIDR_BLOCK = os.getenv('CIDR_BLOCK')
REGION = os.getenv('REGION')
SUBNET_CIDR_BLOCK = os.getenv('SUBNET_CIDR_BLOCK')

def get_availability_zones():
    response_availability_zone_list = ec2.describe_availability_zones(
    )
    az_filtered = response_availability_zone_list['AvailabilityZones']
    az_name = az_filtered[0]['ZoneName']
    az_id = az_filtered[0]['ZoneId']
    return az_name,az_id

def check_vpc_existence():
    print(f"! Checking if {VPC_NAME} already exists")
    response_vpc_existence = ec2.describe_vpcs(Filters=[{"Name":"tag:Name","Values":[VPC_NAME]}])
    vpc_list = response_vpc_existence["Vpcs"]
    if(vpc_list):
        vpc_id = response_vpc_existence["Vpcs"][0]["VpcId"]
        print(f"! VPC {VPC_NAME} exists\n")
        return vpc_id
    else:
        print(f"! Vpc {VPC_NAME} doesn't exist.")
        return False
