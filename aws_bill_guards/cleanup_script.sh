#!/bin/bash
set -e

REGION="ap-south-1"
echo "COMPLETE AquaInsight AWS Resource Cleanup..."
echo "This will DELETE ALL AquaInsight resources in region: $REGION"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# 1. InfluxDB cleanup (MOST EXPENSIVE - DELETE FIRST)
echo "Deleting InfluxDB instances..."
INFLUX_INSTANCES=$(aws timestream-influxdb list-db-instances --region $REGION --query 'items[?contains(name, `aquainsight`)].name' --output text 2>/dev/null || echo "")
if [ ! -z "$INFLUX_INSTANCES" ]; then
    for instance in $INFLUX_INSTANCES; do
        echo "Deleting InfluxDB instance: $instance"
        aws timestream-influxdb delete-db-instance --identifier "$instance" --region $REGION 2>/dev/null || echo "Failed to delete $instance"
    done
else
    echo "No InfluxDB instances found"
fi

# 2. ECS cleanup
echo "Deleting ECS resources..."
# Stop and delete services first
aws ecs update-service --cluster AquaInsight-Cluster --service AquaInsight-Service --desired-count 0 --region $REGION 2>/dev/null || echo "Service not found"
sleep 15
aws ecs delete-service --cluster AquaInsight-Cluster --service AquaInsight-Service --region $REGION 2>/dev/null || echo "Service not found"

# Delete task definitions
TASK_ARNS=$(aws ecs list-task-definitions --family-prefix AquaInsight-Task --region $REGION --query 'taskDefinitionArns' --output text 2>/dev/null || echo "")
if [ ! -z "$TASK_ARNS" ]; then
    for arn in $TASK_ARNS; do
        aws ecs deregister-task-definition --task-definition "$arn" --region $REGION 2>/dev/null || echo "Failed to deregister $arn"
    done
fi

# Delete cluster
aws ecs delete-cluster --cluster AquaInsight-Cluster --region $REGION 2>/dev/null || echo "Cluster not found"

# 3. ECR cleanup
echo "Deleting ECR repositories..."
aws ecr delete-repository --repository-name aqua-container --force --region $REGION 2>/dev/null || echo "ECR repo not found"

# 4. IoT cleanup
echo "Deleting IoT resources..."
aws iot delete-topic-rule --rule-name aqua_data_route_rule --region $REGION 2>/dev/null || echo "IoT rule not found"

# 5. SQS cleanup
echo "Deleting SQS queues..."
QUEUE_URL=$(aws sqs get-queue-url --queue-name AquaInsight-queue --region $REGION --query 'QueueUrl' --output text 2>/dev/null || echo "None")
if [ "$QUEUE_URL" != "None" ] && [ ! -z "$QUEUE_URL" ]; then
    aws sqs delete-queue --queue-url "$QUEUE_URL" --region $REGION
    echo "Deleted SQS queue"
else
    echo "SQS queue not found"
fi

# 6. IAM cleanup
echo "Deleting IAM roles and policies..."
# IoT to SQS role
aws iam detach-role-policy --role-name iot_to_sqs_role --policy-arn arn:aws:iam::588443559335:policy/iot_to_sqs_role-sqs-access 2>/dev/null || echo "Policy not attached"
aws iam delete-policy --policy-arn arn:aws:iam::588443559335:policy/iot_to_sqs_role-sqs-access 2>/dev/null || echo "Policy not found"
aws iam delete-role --role-name iot_to_sqs_role 2>/dev/null || echo "iot_to_sqs_role not found"

# ECS task role
aws iam detach-role-policy --role-name ecs_task_role --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy 2>/dev/null || echo "Policy not attached"
aws iam delete-role-policy --role-name ecs_task_role --policy-name ecs_task_role-ecs-tasks 2>/dev/null || echo "Inline policy not found"
aws iam delete-role --role-name ecs_task_role 2>/dev/null || echo "ecs_task_role not found"

# ECS execution role
aws iam detach-role-policy --role-name ecs_task_execution_role --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy 2>/dev/null || echo "Policy not attached"
aws iam delete-role --role-name ecs_task_execution_role 2>/dev/null || echo "ecs_task_execution_role not found"

# 7. CloudWatch cleanup
echo "Deleting CloudWatch logs..."
aws logs delete-log-group --log-group-name /aws/ecs/aquainsight --region $REGION 2>/dev/null || echo "Log group not found"

# 8. VPC and Networking cleanup (MOST COMPLEX)
echo "Deleting VPC and networking resources..."

# Get VPC ID
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=AquaInsight-VPC" --query 'Vpcs[0].VpcId' --output text --region $REGION 2>/dev/null || echo "None")

if [ "$VPC_ID" != "None" ] && [ ! -z "$VPC_ID" ]; then
    echo "Found VPC: $VPC_ID"
    
    # Delete NAT Gateways (if any)
    NAT_GATEWAYS=$(aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=$VPC_ID" --query 'NatGateways[?State==`available`].NatGatewayId' --output text --region $REGION 2>/dev/null || echo "")
    if [ ! -z "$NAT_GATEWAYS" ]; then
        for nat in $NAT_GATEWAYS; do
            echo "Deleting NAT Gateway: $nat"
            aws ec2 delete-nat-gateway --nat-gateway-id $nat --region $REGION
        done
        echo "Waiting for NAT Gateways to delete..."
        sleep 60
    fi
    
    # Delete route table associations and routes
    ROUTE_TABLES=$(aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:AquaInsight,Values=ECS" --query 'RouteTables[].RouteTableId' --output text --region $REGION 2>/dev/null || echo "")
    if [ ! -z "$ROUTE_TABLES" ]; then
        for rt in $ROUTE_TABLES; do
            echo "Cleaning route table: $rt"
            # Delete custom routes
            aws ec2 delete-route --route-table-id $rt --destination-cidr-block 0.0.0.0/0 --region $REGION 2>/dev/null || echo "Route not found"
            
            # Disassociate subnets
            ASSOCIATIONS=$(aws ec2 describe-route-tables --route-table-ids $rt --query 'RouteTables[0].Associations[?!Main].RouteTableAssociationId' --output text --region $REGION 2>/dev/null || echo "")
            if [ ! -z "$ASSOCIATIONS" ]; then
                for assoc in $ASSOCIATIONS; do
                    aws ec2 disassociate-route-table --association-id $assoc --region $REGION 2>/dev/null || echo "Association not found"
                done
            fi
            
            # Delete route table
            aws ec2 delete-route-table --route-table-id $rt --region $REGION 2>/dev/null || echo "Route table not found"
        done
    fi
    
    # Delete subnets
    SUBNETS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:AquaInsight,Values=ECS" --query 'Subnets[].SubnetId' --output text --region $REGION 2>/dev/null || echo "")
    if [ ! -z "$SUBNETS" ]; then
        for subnet in $SUBNETS; do
            echo "Deleting subnet: $subnet"
            aws ec2 delete-subnet --subnet-id $subnet --region $REGION 2>/dev/null || echo "Subnet not found"
        done
    fi
    
    # Delete security groups (except default)
    SECURITY_GROUPS=$(aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:AquaInsight,Values=ECS" --query 'SecurityGroups[].GroupId' --output text --region $REGION 2>/dev/null || echo "")
    if [ ! -z "$SECURITY_GROUPS" ]; then
        for sg in $SECURITY_GROUPS; do
            echo "Deleting security group: $sg"
            aws ec2 delete-security-group --group-id $sg --region $REGION 2>/dev/null || echo "Security group not found"
        done
    fi
    
    # Detach and delete internet gateway
    IGW_ID=$(aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=$VPC_ID" --query 'InternetGateways[0].InternetGatewayId' --output text --region $REGION 2>/dev/null || echo "None")
    if [ "$IGW_ID" != "None" ] && [ ! -z "$IGW_ID" ]; then
        echo "Detaching and deleting Internet Gateway: $IGW_ID"
        aws ec2 detach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID --region $REGION 2>/dev/null || echo "IGW not attached"
        aws ec2 delete-internet-gateway --internet-gateway-id $IGW_ID --region $REGION 2>/dev/null || echo "IGW not found"
    fi
    
    # Finally delete VPC
    echo "Deleting VPC: $VPC_ID"
    aws ec2 delete-vpc --vpc-id $VPC_ID --region $REGION 2>/dev/null || echo "VPC not found"
    
else
    echo "AquaInsight VPC not found"
fi

echo ""
echo "COMPLETE CLEANUP FINISHED!"
echo "All AquaInsight resources have been deleted"
echo "This should stop all charges related to AquaInsight"
echo ""
echo "Note: InfluxDB deletion may take up to 20 minutes to complete"
