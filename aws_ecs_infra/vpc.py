import os
import botocore
from dotenv import load_dotenv
from aws_clients import ec2_client
from route_table import modify_route_table

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

def check_igw_existence(vpc_id: str):
    print(f"! checking if internet-gateway exists and attached to {VPC_NAME} ")
    response_igw_existence = ec2.describe_internet_gateways(
        Filters = [
            {"Name": "attachment.vpc-id", "Values": [vpc_id]}
        ]
    )
    available_internet_gateways = response_igw_existence["InternetGateways"]
    if(available_internet_gateways):
        igw_id = available_internet_gateways[0]['InternetGatewayId']
        print(f"! Internet-gateway already exists\n")
        return igw_id
    else:
        print(f"! Internet-gateway for {VPC_NAME} doesn't exist, creating one !")
        return False

def check_subnets_for_vpc(vpc_id: str):
    print(f"! checking if subnets exists for {VPC_NAME}")
    response_subnets_existence = ec2.describe_subnets(
        Filters=[
            {"Name": "vpc-id","Values": [vpc_id]}
        ]
    )
    subnets_available = response_subnets_existence['Subnets']
    if (subnets_available):
        subnet_id = subnets_available[0]['SubnetId']
        print(f"! Subnets for {VPC_NAME} already exists!\n")
        return subnet_id 
    else:
        print(f"! Subnets for {VPC_NAME} doesn't exist, creating one !")
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
                    Description = 'AquaInsight vpc',
                    GroupName = SECURITY_GROUP_NAME,
                    VpcId = vpc_id,
                    TagSpecifications=[
                        {
                        'ResourceType': 'security-group',
                        'Tags': [
                            {
                                'Key': 'AquaInsight',
                                'Value': 'ECS'
                            },
                        ]
                        },
                    ],
                )
            sg_id = response_security_group["GroupId"]
            print("+ Created security group id=",sg_id")
            return sg_id
            
        except botocore.exceptions.ClientError as e:
            print(":: Error :",e)
            raise

def create_internet_gateway(vpc_id: str):
    igw_id = check_igw_existence(vpc_id)
    if(igw_id):
        return igw_id
    else:
        try:
            print("! Creating internet-gateway")
            response_igw = ec2.create_internet_gateway(
                TagSpecifications=[
                    {
                        'ResourceType': 'internet-gateway',
                        'Tags': [
                            {
                                'Key': 'AquaInsight',
                                'Value': 'ECS'
                            },
                        ]
                    }
                ]
            )
            igw_id = response_igw['InternetGateway']['InternetGatewayId']
            print(f"+ Created internet-gateway id={igw_id} for {VPC_NAME}")
            print(f"! Attaching the internet gateway to the VPC")
            ec2.attach_internet_gateway(
                InternetGatewayId=igw_id,
                VpcId = vpc_id
            )
            print(f"+ Attached the internet gateway successfully!")
            return igw_id

        except botocore.exceptions.ClientError as e:
            print(":: Error :",e)
            raise
        

def create_subnets_for_vpc(vpc_id: str,az_name: str,az_id: str):
    subnet_id = check_subnets_for_vpc(vpc_id)
    if(subnet_id):
        return subnet_id
    else:
        try:
            print("! Creating subnets")
            response_subnet = ec2.create_subnet(
                TagSpecifications=[
                    {
                        'ResourceType': 'subnet',
                        'Tags':[
                            {
                                'Key': 'AquaInsight',
                                'Value': 'ECS'
                            },
                        ]
                    },
                ],
                AvailabilityZoneId=az_id,
                CidrBlock=SUBNET_CIDR_BLOCK,
                VpcId=vpc_id,
            )
            subnet = (response_subnet['Subnet'])
            subnet_id = subnet['SubnetId']

            response_modified_attribute = ec2.modify_subnet_attribute(
                MapPublicIpOnLaunch={
                    "Value": True
                },
                SubnetId=subnet_id
            )
            print(f"+ Created subnet for {VPC_NAME}")
            return subnet_id
        
        except botocore.exceptions.ClietError as e:
            print("::Error::",e)
            raise

def setup_ecs_infra():
    vpc_id = create_vpc()
    sg_id = create_security_group(vpc_id)
    igw_id = create_internet_gateway(vpc_id)
    az_name, az_id = get_availability_zones()
    subnet_id = create_subnets_for_vpc(vpc_id, az_name, az_id)
    route_table_id = modify_route_table(vpc_id,subnet_id,igw_id)
    
    return {
        "vpc_id": vpc_id,
        "sg_id": sg_id,
        "subnet_id": subnet_id,
    }
