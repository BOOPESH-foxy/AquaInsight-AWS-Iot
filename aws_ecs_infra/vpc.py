import os
from botocore.exceptions import ClientError
from dotenv import load_dotenv

from aws_clients import ec2_client
from aws_ecs_infra.route_table import modify_route_table

load_dotenv()
ec2 = ec2_client()

SECURITY_GROUP_NAME = os.getenv("SECURITY_GROUP_NAME")
VPC_NAME = os.getenv("VPC_NAME")
CIDR_BLOCK = os.getenv("CIDR_BLOCK")
REGION = os.getenv("REGION", "ap-south-1")

SUBNET_CIDR_BLOCKS = [
    cidr.strip()
    for cidr in os.getenv(
        "SUBNET_CIDR_BLOCKS",
        ""
    ).split(",")
    if cidr.strip()
]


def get_availability_zones(max_azs: int | None = None):
    """Get a list of availability zones (name + id) in the region. We'll use one subnet per AZ, up to 'max_azs' (or all if None)."""

    print(f"! Fetching AZs for region {REGION}")
    response = ec2.describe_availability_zones(
        Filters=[{"Name": "region-name", "Values": [REGION]}],
    )
    zones = response["AvailabilityZones"]
    if not zones:
        raise RuntimeError(f"No availability zones found for region {REGION}")

    if max_azs is None:
        max_azs = len(zones)

    chosen = zones[:max_azs]
    azs = [{"ZoneName": z["ZoneName"], "ZoneId": z["ZoneId"]} for z in chosen]
    print("! Using AZs:", ", ".join([z["ZoneName"] for z in azs]))
    print("\n")
    return azs


def check_vpc_existence():
    print(f"! Checking if VPC '{VPC_NAME}' already exists")
    response = ec2.describe_vpcs(
        Filters=[{"Name": "tag:Name", "Values": [VPC_NAME]}]
    )
    vpc_list = response.get("Vpcs", [])
    if vpc_list:
        vpc_id = vpc_list[0]["VpcId"]
        print(f"! VPC {VPC_NAME} exists (id={vpc_id})\n")
        return vpc_id
    else:
        print(f"! VPC {VPC_NAME} doesn't exist.")
        return False


def check_security_group_existence(vpc_id: str):
    print(f"! Checking if Security Group '{SECURITY_GROUP_NAME}' already exists")
    response = ec2.describe_security_groups(
        Filters=[
            {"Name": "vpc-id", "Values": [vpc_id]},
            {"Name": "group-name", "Values": [SECURITY_GROUP_NAME]},
        ]
    )
    sg_list = response.get("SecurityGroups", [])
    if sg_list:
        sg_id = sg_list[0]["GroupId"]
        print(f"! Security Group {SECURITY_GROUP_NAME} exists (id={sg_id})\n")
        return sg_id
    else:
        print(f"! Security Group {SECURITY_GROUP_NAME} doesn't exist, creating one.")
        return False


def check_igw_existence(vpc_id: str):
    print(f"! Checking if Internet Gateway exists and is attached to {VPC_NAME}")
    response = ec2.describe_internet_gateways(
        Filters=[{"Name": "attachment.vpc-id", "Values": [vpc_id]}]
    )
    igws = response.get("InternetGateways", [])
    if igws:
        igw_id = igws[0]["InternetGatewayId"]
        print(f"! Internet Gateway already exists (id={igw_id})\n")
        return igw_id
    else:
        print(f"! Internet Gateway for {VPC_NAME} doesn't exist, creating one.")
        return False


def create_vpc():
    vpc_id = check_vpc_existence()
    if vpc_id:
        return vpc_id

    try:
        print("! Creating VPC")
        response_vpc = ec2.create_vpc(
            CidrBlock=CIDR_BLOCK,
            TagSpecifications=[
                {
                    "ResourceType": "vpc",
                    "Tags": [
                        {"Key": "Name", "Value": VPC_NAME},
                        {"Key": "AquaInsight", "Value": "ECS"},
                    ],
                },
            ],
        )
        vpc_id = response_vpc["Vpc"]["VpcId"]
        print(f"+ Created VPC id={vpc_id}")
        return vpc_id

    except ClientError as e:
        print(":: Error creating VPC:", e)
        raise


def create_security_group(vpc_id: str):
    security_group_id = check_security_group_existence(vpc_id)
    if security_group_id:
        return security_group_id

    try:
        print("! Creating Security Group")
        response_security_group = ec2.create_security_group(
            Description="AquaInsight ECS VPC",
            GroupName=SECURITY_GROUP_NAME,
            VpcId=vpc_id,
            TagSpecifications=[
                {
                    "ResourceType": "security-group",
                    "Tags": [
                        {"Key": "AquaInsight", "Value": "ECS"},
                    ],
                },
            ],
        )
        sg_id = response_security_group["GroupId"]
        print("+ Created Security Group id=", sg_id)

       ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 8086,
                    'ToPort': 8086,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'InfluxDB HTTPS access'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 443,
                    'ToPort': 443,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTPS access'}]
                }
            ]
        )
        
        ec2.authorize_security_group_egress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 443,
                    'ToPort': 443,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTPS for AWS APIs'}]
                },
                {
                    'IpProtocol': 'tcp', 
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTP for package installs'}]
                }
            ]
        )

        return sg_id

    except ClientError as e:
        print(":: Error creating Security Group:", e)
        raise


def create_internet_gateway(vpc_id: str):
    igw_id = check_igw_existence(vpc_id)
    if igw_id:
        return igw_id

    try:
        print("! Creating Internet Gateway")
        response_igw = ec2.create_internet_gateway(
            TagSpecifications=[
                {
                    "ResourceType": "internet-gateway",
                    "Tags": [
                        {"Key": "AquaInsight", "Value": "ECS"},
                    ],
                }
            ]
        )
        igw_id = response_igw["InternetGateway"]["InternetGatewayId"]
        print(f"+ Created Internet Gateway id={igw_id} for {VPC_NAME}")
        print("! Attaching the Internet Gateway to the VPC")
        ec2.attach_internet_gateway(
            InternetGatewayId=igw_id,
            VpcId=vpc_id,
        )
        print("+ Attached the Internet Gateway successfully!")
        return igw_id

    except ClientError as e:
        print(":: Error creating/attaching Internet Gateway:", e)
        raise


def get_existing_ecs_subnets(vpc_id: str):
    """
    Return a mapping of AZ ID -> subnet for existing AquaInsight ECS subnets.
    """
    response = ec2.describe_subnets(
        Filters=[
            {"Name": "vpc-id", "Values": [vpc_id]},
            {"Name": "tag:AquaInsight", "Values": ["ECS"]},
        ]
    )
    subnets = response.get("Subnets", [])
    mapping = {}
    for s in subnets:
        az_id = s["AvailabilityZoneId"]
        mapping[az_id] = s
    return mapping


def create_subnets_for_vpc(vpc_id: str, azs: list[dict]):

    if not SUBNET_CIDR_BLOCKS:
        raise RuntimeError("SUBNET_CIDR_BLOCKS must be set in .env")

    if len(SUBNET_CIDR_BLOCKS) < len(azs):
        raise RuntimeError(
            f"Not enough SUBNET_CIDR_BLOCKS ({len(SUBNET_CIDR_BLOCKS)}) "
            f"for AZs requested ({len(azs)})."
        )

    existing_by_az = get_existing_ecs_subnets(vpc_id)
    subnet_ids = []

    for index, az in enumerate(azs):
        az_name = az["ZoneName"]
        az_id = az["ZoneId"]
        cidr = SUBNET_CIDR_BLOCKS[index]

        if az_id in existing_by_az:
            subnet_id = existing_by_az[az_id]["SubnetId"]
            print(f"! Subnet already exists in {az_name} ({subnet_id}), reusing.")
            subnet_ids.append(subnet_id)
            continue
        print("\n")

        try:
            print(f"! Creating subnet in {az_name} with CIDR {cidr}")
            response_subnet = ec2.create_subnet(
                TagSpecifications=[
                    {
                        "ResourceType": "subnet",
                        "Tags": [
                            {"Key": "AquaInsight", "Value": "ECS"},
                            {
                                "Key": "Name",
                                "Value": f"{VPC_NAME}-public-{az_name}",
                            },
                        ],
                    },
                ],
                AvailabilityZoneId=az_id,
                CidrBlock=cidr,
                VpcId=vpc_id,
            )
            subnet = response_subnet["Subnet"]
            subnet_id = subnet["SubnetId"]

            ec2.modify_subnet_attribute(
                MapPublicIpOnLaunch={"Value": True},
                SubnetId=subnet_id,
            )
            print(f"+ Created subnet {subnet_id} for {VPC_NAME} in AZ {az_name}")
            subnet_ids.append(subnet_id)

        except ClientError as e:
            print(f":: Error creating subnet in {az_name}:", e)
            raise

    return subnet_ids


def setup_ecs_infra():

    vpc_id = create_vpc()
    sg_id = create_security_group(vpc_id)
    igw_id = create_internet_gateway(vpc_id)

    azs = get_availability_zones(max_azs=len(SUBNET_CIDR_BLOCKS))
    subnet_ids = create_subnets_for_vpc(vpc_id, azs)

    # Create ONE route table, associate with ALL subnets
    rt_id = modify_route_table(vpc_id, subnet_ids[0], igw_id)  # Create once
    for subnet_id in subnet_ids[1:]:
        ec2.associate_route_table(RouteTableId=rt_id, SubnetId=subnet_id)
    route_table_ids = [rt_id]

    return {
        "vpc_id": vpc_id,
        "security_group_id": sg_id,
        "subnet_ids": subnet_ids,
        "route_table_ids": route_table_ids,
        "availability_zones": [az["ZoneName"] for az in azs],
    }

