import os
import botocore
from dotenv import load_dotenv
from aws_clients import ec2_client

load_dotenv()
ec2 = ec2_client()

VPC_NAME = os.getenv('VPC_NAME')

def check_route_table_existence(vpc_id: str):
    rt_response = ec2.describe_route_tables(
        Filters=[
            {"Name": "vpc-id", "Values": [vpc_id]}
        ]
    )
    available_route_tables = rt_response['RouteTables']
    if(available_route_tables):
        route_table_id = available_route_tables[0]['RouteTableId']
        print(f"! Route table exists for {VPC_NAME}")
        return route_table_id
    else:
        print(f"No route tables found for {VPC_NAME}")
        route_table_id = create_route_table(vpc_id)
        return route_table_id


def create_route_table(vpc_id: str):
    try:
        print(f"Creating route table for {VPC_NAME}")
        response_route_table_creation = ec2.create_route_table(
            TagSpecifications=[
                {
                    'ResourceType': "route-table",
                    'Tags':[
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
        print(f"+ Created route-table id={route_table_id} for {VPC_NAME}")
        return route_table_id
    
    except botocore.Exception as e:
        print(":: Error ::",e)
        raise


def modify_route_table(vpc_id: str,subnet_id: str,igw_id: str):
    route_table_id = check_route_table_existence(vpc_id)
    existing_routes = [r['DestinationCidrBlock'] for r in ec2.describe_route_tables(RouteTableIds=[route_table_id])['RouteTables'][0]['Routes']]
    if '0.0.0.0/0' not in existing_routes:
        print("! Creating route to IGW")
        result_creating_route = ec2.create_route(RouteTableId=route_table_id, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw_id)
    print("! Associating route-table to Subnet")
    result_associating_route = ec2.associate_route_table(RouteTableId=route_table_id,SubnetId=subnet_id)
    return route_table_id