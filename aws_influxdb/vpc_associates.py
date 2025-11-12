import os
import botocore
from dotenv import load_dotenv
from aws_clients import ec2_client

load_dotenv()
ec2 = ec2_client()

SECURITY_GROUP_NAME = os.getenv('SECURITY_GROUP_NAME')
VPC_NAME = os.getenv('VPC_NAME')
CIDR_BLOCK = os.getenv('CIDR_BLOCK')
SSH_CIDR = os.getenv('SSH_CIDR')
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

def check_security_group_existence(vpc_id: str):
    print(f"! Checking if {SECURITY_GROUP_NAME} already exists")
    response_security_group_existence = ec2.describe_security_groups(
    Filters=[
        {"Name": "vpc-id", "Values": [vpc_id]},
        {"Name": "group-name", "Values":[SECURITY_GROUP_NAME]}
    ])
    sg_list = response_security_group_existence["SecurityGroups"]
    if(sg_list):
        sg_id = sg_list[0]["GroupId"]    
        print(f"! Security Group {SECURITY_GROUP_NAME} exists\n")
        return sg_id
    else:
        print(f"! Security Group {SECURITY_GROUP_NAME} doesn't exist, Creating one.")
        return False

def create_vpc():
    vpc_id = check_vpc_existence()
    if(vpc_id):
        return vpc_id
    else:
        try:
            print("! Creating VPC ")
            response_vpc = ec2.create_vpc(
            CidrBlock = CIDR_BLOCK,
            TagSpecifications=[
                {
                    'ResourceType': 'vpc',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': VPC_NAME
                        },
                    ],
                },
            ],
            )
            vpc_id = response_vpc["Vpc"]["VpcId"]
            print(f"+ Created VPC id={vpc_id}")
            return vpc_id
        
        except botocore.exceptions.ClientError as e:
            print(":: Error :",e)


def create_security_group(vpc_id: str):
    security_group_id = check_security_group_existence(vpc_id)
    if(security_group_id):
        return security_group_id
    
    else:
        try:
            print("! Creating security group")
            response_security_group = ec2.create_security_group(
                    Description = 'aquaInsight-db',
                    GroupName = SECURITY_GROUP_NAME,
                    VpcId = vpc_id,
                    TagSpecifications=[
                        {
                        'ResourceType': 'security-group',
                        'Tags': [
                            {
                                'Key': 'boto3-db',
                                'Value': 'foo-bar'
                            },
                        ]
                        },
                    ],
                )
            sg_id = response_security_group["GroupId"]
            ec2.authorize_security_group_ingress(
                GroupId = sg_id,
                IpPermissions=[{
                    "IpProtocol":"tcp",
                    "FromPort":22,
                    "ToPort":22,
                    'IpRanges':[{'CidrIp': SSH_CIDR}]
                }]
            )
            print("+ Created security group id=",sg_id,f"opening 22 from {SSH_CIDR}")
            return sg_id

        except botocore.exceptions.ClientError as e:
            print(":: Error :",e)
            raise