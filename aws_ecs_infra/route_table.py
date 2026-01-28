import os
import botocore
from dotenv import load_dotenv
from aws_clients import ec2_client

load_dotenv()
ec2 = ec2_client()

VPC_NAME = os.getenv('VPC_NAME')

def check_route_table_existence(vpc_id: str):
    # looks for custom route table with AquaInsight tag
    rt_response = ec2.describe_route_tables(
        Filters=[
            {"Name": "vpc-id", "Values": [vpc_id]},
            {"Name": "tag:AquaInsight", "Values": ["ECS"]}
        ]
    )
    available_route_tables = rt_response['RouteTables']
    if available_route_tables:
        route_table_id = available_route_tables[0]['RouteTableId']
        print(f"! Custom route table exists for {VPC_NAME} (id={route_table_id})")
        return route_table_id
    else:
        print(f"! No custom route table found for {VPC_NAME}, creating one...")
        route_table_id = create_route_table(vpc_id)
        return route_table_id


def create_route_table(vpc_id: str):
    try:
        print(f"! Creating route table for {VPC_NAME}...")
        response_route_table_creation = ec2.create_route_table(
            TagSpecifications=[
                {
                    'ResourceType': "route-table",
                    'Tags':[
                        {
                            'Key': 'Name',
                            'Value': f'{VPC_NAME}-public-rt'
                        },
                        {
                            'Key': 'AquaInsight',
                            'Value': 'ECS'
                        }
                    ]
                }
            ],
            VpcId=vpc_id
        )
        route_table_id = response_route_table_creation['RouteTable']['RouteTableId']
        print(f"+ Created route table: {route_table_id}")
        return route_table_id
    
    except botocore.Exception as e:
        print(":: Error ::",e)
        raise


def modify_route_table(vpc_id: str,subnet_id: str,igw_id: str):
    route_table_id = check_route_table_existence(vpc_id)

    existing_routes = [r['DestinationCidrBlock'] for r in ec2.describe_route_tables(RouteTableIds=[route_table_id])['RouteTables'][0]['Routes']]
    if '0.0.0.0/0' not in existing_routes:
        print("! Creating route to Internet Gateway...")
        result_creating_route = ec2.create_route(RouteTableId=route_table_id, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw_id)
        print("+ Added route to Internet Gateway")
    else:
        print("! Route to IGW already exists")

    associations = ec2.describe_route_tables(RouteTableIds=[route_table_id])['RouteTables'][0]['Associations']
    associated_subnets = [a.get('SubnetId') for a in associations if a.get('SubnetId')]
    
    if subnet_id not in associated_subnets:
        print(f"! Associating route table to subnet {subnet_id}...")
        result_associating_route = ec2.associate_route_table(RouteTableId=route_table_id, SubnetId=subnet_id)
        print("+ Associated route table to subnet")
    else:
        print(f"! Subnet {subnet_id} already associated with route table")
    
    return route_table_id