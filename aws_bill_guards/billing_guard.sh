#!/bin/bash

REGION="ap-south-1"
ACCOUNT_ID="588443559335"

echo "AquaInsight Billing Guard - Comprehensive Resource Check"
echo "Region: $REGION | Account: $ACCOUNT_ID"
echo "============================================================"

TOTAL_COST_RESOURCES=0
HIGH_COST_FOUND=0

# Function to check and report resources
check_resource() {
    local service=$1
    local resource_type=$2
    local count=$3
    local cost_level=$4  # HIGH, MEDIUM, LOW
    local details=$5
    
    if [ "$count" -gt 0 ]; then
        case $cost_level in
            "HIGH")
                echo "HIGH COST: $service - $resource_type"
                echo "   Found: $count resources"
                HIGH_COST_FOUND=$((HIGH_COST_FOUND + count))
                ;;
            "MEDIUM")
                echo "MEDIUM COST: $service - $resource_type"
                echo "   Found: $count resources"
                ;;
            "LOW")
                echo "LOW COST: $service - $resource_type"
                echo "   Found: $count resources"
                ;;
        esac
        
        if [ ! -z "$details" ]; then
            echo "   Details: $details"
        fi
        
        TOTAL_COST_RESOURCES=$((TOTAL_COST_RESOURCES + count))
        echo ""
    fi
}

echo "Scanning for billable resources..."
echo ""

# 1. HIGHEST COST RESOURCES FIRST

echo "=== HIGH COST RESOURCES ==="

# InfluxDB (MOST EXPENSIVE)
echo "Checking InfluxDB instances..."
INFLUX_INSTANCES=$(aws timestream-influxdb list-db-instances --region $REGION --query 'items[?contains(name, `aquainsight`)]' --output json 2>/dev/null || echo "[]")
INFLUX_COUNT=$(echo "$INFLUX_INSTANCES" | jq length 2>/dev/null || echo "0")
if [ "$INFLUX_COUNT" -gt 0 ]; then
    INFLUX_DETAILS=$(echo "$INFLUX_INSTANCES" | jq -r '.[] | "\(.name) (\(.status)) - \(.dbInstanceType)"' | tr '\n' '; ')
    check_resource "Timestream InfluxDB" "Database Instances" "$INFLUX_COUNT" "HIGH" "$INFLUX_DETAILS"
fi

# RDS Instances (if any)
echo "Checking RDS instances..."
RDS_COUNT=$(aws rds describe-db-instances --region $REGION --query 'length(DBInstances[?contains(DBName, `aqua`) || contains(DBInstanceIdentifier, `aqua`)])' --output text 2>/dev/null || echo "0")
if [ "$RDS_COUNT" -gt 0 ]; then
    check_resource "RDS" "Database Instances" "$RDS_COUNT" "HIGH" "Check AWS Console"
fi

# EC2 Instances
echo "Checking EC2 instances..."
EC2_COUNT=$(aws ec2 describe-instances --region $REGION --filters "Name=tag:AquaInsight,Values=*" "Name=instance-state-name,Values=running,pending,stopping,stopped" --query 'length(Reservations[].Instances[])' --output text 2>/dev/null || echo "0")
if [ "$EC2_COUNT" -gt 0 ]; then
    check_resource "EC2" "Compute Instances" "$EC2_COUNT" "HIGH" "Check AWS Console"
fi

# NAT Gateways
echo "Checking NAT Gateways..."
NAT_COUNT=$(aws ec2 describe-nat-gateways --region $REGION --filter "Name=state,Values=available,pending" --query 'length(NatGateways[])' --output text 2>/dev/null || echo "0")
if [ "$NAT_COUNT" -gt 0 ]; then
    check_resource "VPC" "NAT Gateways" "$NAT_COUNT" "HIGH" "~$45/month each"
fi

# Load Balancers
echo "Checking Load Balancers..."
ALB_COUNT=$(aws elbv2 describe-load-balancers --region $REGION --query 'length(LoadBalancers[?contains(LoadBalancerName, `aqua`) || contains(LoadBalancerName, `AquaInsight`)])' --output text 2>/dev/null || echo "0")
ELB_COUNT=$(aws elb describe-load-balancers --region $REGION --query 'length(LoadBalancerDescriptions[?contains(LoadBalancerName, `aqua`) || contains(LoadBalancerName, `AquaInsight`)])' --output text 2>/dev/null || echo "0")
TOTAL_LB=$((ALB_COUNT + ELB_COUNT))
if [ "$TOTAL_LB" -gt 0 ]; then
    check_resource "ELB/ALB" "Load Balancers" "$TOTAL_LB" "HIGH" "~$20/month each"
fi

echo "=== MEDIUM COST RESOURCES ==="

# ECS Services (running tasks)
echo "Checking ECS running tasks..."
ECS_CLUSTERS=$(aws ecs list-clusters --region $REGION --query 'clusterArns[?contains(@, `AquaInsight`)]' --output text 2>/dev/null || echo "")
RUNNING_TASKS=0
if [ ! -z "$ECS_CLUSTERS" ]; then
    for cluster in $ECS_CLUSTERS; do
        CLUSTER_TASKS=$(aws ecs list-tasks --cluster "$cluster" --region $REGION --query 'length(taskArns)' --output text 2>/dev/null || echo "0")
        RUNNING_TASKS=$((RUNNING_TASKS + CLUSTER_TASKS))
    done
fi
if [ "$RUNNING_TASKS" -gt 0 ]; then
    check_resource "ECS" "Running Tasks" "$RUNNING_TASKS" "MEDIUM" "Fargate charges per vCPU/memory/hour"
fi

# ECR Repositories with images
echo "Checking ECR repositories..."
ECR_REPOS=$(aws ecr describe-repositories --region $REGION --query 'repositories[?contains(repositoryName, `aquainsight`)]' --output json 2>/dev/null || echo "[]")
ECR_COUNT=$(echo "$ECR_REPOS" | jq length 2>/dev/null || echo "0")
if [ "$ECR_COUNT" -gt 0 ]; then
    # Check for images in repos
    TOTAL_IMAGES=0
    for repo in $(echo "$ECR_REPOS" | jq -r '.[].repositoryName' 2>/dev/null); do
        IMAGE_COUNT=$(aws ecr list-images --repository-name "$repo" --region $REGION --query 'length(imageIds)' --output text 2>/dev/null || echo "0")
        TOTAL_IMAGES=$((TOTAL_IMAGES + IMAGE_COUNT))
    done
    check_resource "ECR" "Container Repositories" "$ECR_COUNT" "MEDIUM" "$TOTAL_IMAGES images stored"
fi

# CloudWatch Log Groups with data
echo "Checking CloudWatch Log Groups..."
LOG_GROUPS=$(aws logs describe-log-groups --region $REGION --query 'logGroups[?contains(logGroupName, `aquainsight`) || contains(logGroupName, `/aws/ecs/aquainsight`)]' --output json 2>/dev/null || echo "[]")
LOG_COUNT=$(echo "$LOG_GROUPS" | jq length 2>/dev/null || echo "0")
if [ "$LOG_COUNT" -gt 0 ]; then
    TOTAL_LOG_SIZE=0
    for log_group in $(echo "$LOG_GROUPS" | jq -r '.[].logGroupName' 2>/dev/null); do
        LOG_SIZE=$(aws logs describe-log-groups --log-group-name-prefix "$log_group" --region $REGION --query 'logGroups[0].storedBytes' --output text 2>/dev/null || echo "0")
        if [ "$LOG_SIZE" != "None" ] && [ "$LOG_SIZE" != "null" ]; then
            TOTAL_LOG_SIZE=$((TOTAL_LOG_SIZE + LOG_SIZE))
        fi
    done
    LOG_SIZE_MB=$((TOTAL_LOG_SIZE / 1024 / 1024))
    check_resource "CloudWatch" "Log Groups" "$LOG_COUNT" "MEDIUM" "${LOG_SIZE_MB}MB stored"
fi

echo "=== LOW COST RESOURCES ==="

# VPC Resources
echo "Checking VPC resources..."
VPC_COUNT=$(aws ec2 describe-vpcs --region $REGION --filters "Name=tag:Name,Values=AquaInsight-VPC" --query 'length(Vpcs)' --output text 2>/dev/null || echo "0")
if [ "$VPC_COUNT" -gt 0 ]; then
    check_resource "VPC" "Virtual Private Clouds" "$VPC_COUNT" "LOW" "Minimal cost"
fi

# Internet Gateways
IGW_COUNT=$(aws ec2 describe-internet-gateways --region $REGION --filters "Name=tag:AquaInsight,Values=*" --query 'length(InternetGateways)' --output text 2>/dev/null || echo "0")
if [ "$IGW_COUNT" -gt 0 ]; then
    check_resource "VPC" "Internet Gateways" "$IGW_COUNT" "LOW" "Free when attached"
fi

# Security Groups
SG_COUNT=$(aws ec2 describe-security-groups --region $REGION --filters "Name=tag:AquaInsight,Values=*" --query 'length(SecurityGroups)' --output text 2>/dev/null || echo "0")
if [ "$SG_COUNT" -gt 0 ]; then
    check_resource "VPC" "Security Groups" "$SG_COUNT" "LOW" "Free"
fi

# Subnets
SUBNET_COUNT=$(aws ec2 describe-subnets --region $REGION --filters "Name=tag:AquaInsight,Values=*" --query 'length(Subnets)' --output text 2>/dev/null || echo "0")
if [ "$SUBNET_COUNT" -gt 0 ]; then
    check_resource "VPC" "Subnets" "$SUBNET_COUNT" "LOW" "Free"
fi

# Route Tables
RT_COUNT=$(aws ec2 describe-route-tables --region $REGION --filters "Name=tag:AquaInsight,Values=*" --query 'length(RouteTables)' --output text 2>/dev/null || echo "0")
if [ "$RT_COUNT" -gt 0 ]; then
    check_resource "VPC" "Route Tables" "$RT_COUNT" "LOW" "Free"
fi

# SQS Queues
SQS_COUNT=$(aws sqs list-queues --region $REGION --query 'length(QueueUrls[?contains(@, `AquaInsight`)])' --output text 2>/dev/null || echo "0")
if [ "$SQS_COUNT" -gt 0 ]; then
    check_resource "SQS" "Message Queues" "$SQS_COUNT" "LOW" "Pay per request"
fi

# SNS Topics
SNS_COUNT=$(aws sns list-topics --region $REGION --query 'length(Topics[?contains(TopicArn, `AquaInsight`)])' --output text 2>/dev/null || echo "0")
if [ "$SNS_COUNT" -gt 0 ]; then
    check_resource "SNS" "Notification Topics" "$SNS_COUNT" "LOW" "Pay per message"
fi

# IoT Rules
IOT_COUNT=$(aws iot list-topic-rules --region $REGION --query 'length(rules[?contains(ruleName, `aqua`)])' --output text 2>/dev/null || echo "0")
if [ "$IOT_COUNT" -gt 0 ]; then
    check_resource "IoT Core" "Topic Rules" "$IOT_COUNT" "LOW" "Pay per message"
fi

# IAM Roles
IAM_COUNT=$(aws iam list-roles --query 'length(Roles[?contains(RoleName, `iot_to_sqs`) || contains(RoleName, `ecs_task`)])' --output text 2>/dev/null || echo "0")
if [ "$IAM_COUNT" -gt 0 ]; then
    check_resource "IAM" "Service Roles" "$IAM_COUNT" "LOW" "Free"
fi

echo "============================================================"

# SUMMARY AND RECOMMENDATIONS
echo "BILLING GUARD SUMMARY"
echo ""

if [ "$HIGH_COST_FOUND" -gt 0 ]; then
    echo "CRITICAL: $HIGH_COST_FOUND HIGH-COST resources found!"
    echo "   These resources can cost $50-500+ per month"
    echo "   Action: Delete immediately if not needed"
    echo ""
fi

if [ "$TOTAL_COST_RESOURCES" -eq 0 ]; then
    echo "EXCELLENT: No billable resources found"
    echo "Estimated monthly cost: $0"
elif [ "$HIGH_COST_FOUND" -eq 0 ] && [ "$TOTAL_COST_RESOURCES" -lt 10 ]; then
    echo "ACCEPTABLE: $TOTAL_COST_RESOURCES low-cost resources found"
    echo "Estimated monthly cost: $1-10"
else
    echo "ATTENTION NEEDED: $TOTAL_COST_RESOURCES total resources found"
    echo "Estimated monthly cost: $10-100+"
fi

echo ""
echo "RECOMMENDED ACTIONS:"

if [ "$HIGH_COST_FOUND" -gt 0 ]; then
    echo "1. Run cleanup script immediately: ./cleanup_script.sh"
    echo "2. Verify deletion: ./billing_guard.sh"
    echo "3. Check AWS Billing Dashboard"
else
    echo "1. Resources look clean"
    echo "2. Monitor billing dashboard regularly"
    echo "3. Set up billing alerts if not already done"
fi

echo ""
echo "Pro Tips:"
echo "• Run this script daily during development"
echo "• Set up AWS Budget alerts for your account"
echo "• Always cleanup after testing"
echo "• Use AWS Cost Explorer to track spending"

echo ""
echo "Last checked: $(date)"
echo "============================================================"