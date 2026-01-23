#!/bin/bash

# Billing Monitor - Continuous polling for cost protection
REGION="ap-south-1"
POLL_INTERVAL=300  # 5 minutes
MAX_POLLS=288      # 24 hours (288 * 5 minutes)

echo "AquaInsight Billing Monitor - Continuous Protection"
echo "Polling every $POLL_INTERVAL seconds for $MAX_POLLS cycles (24 hours)"
echo "Press Ctrl+C to stop monitoring"
echo ""

# Function to send alert
send_alert() {
    local message=$1
    local urgency=$2
    
    echo "BILLING ALERT: $message"
    
    # Log to file
    echo "$(date): $urgency - $message" >> billing_alerts.log
}

# Trap Ctrl+C
trap 'echo "\nMonitoring stopped by user"; exit 0' INT

poll_count=0

while [ $poll_count -lt $MAX_POLLS ]; do
    poll_count=$((poll_count + 1))
    current_time=$(date '+%H:%M:%S')
    
    echo "[$current_time] Poll #$poll_count - Checking for billable resources..."
    
    # Quick check for HIGH COST resources only
    high_cost_found=0
    
    # Check InfluxDB (MOST EXPENSIVE)
    influx_count=$(aws timestream-influxdb list-db-instances --region $REGION --query 'length(items[?contains(name, `aquainsight`)])' --output text 2>/dev/null || echo "0")
    if [ "$influx_count" -gt 0 ]; then
        influx_status=$(aws timestream-influxdb list-db-instances --region $REGION --query 'items[?contains(name, `aquainsight`)][0].status' --output text 2>/dev/null || echo "UNKNOWN")
        if [ "$influx_status" = "AVAILABLE" ] || [ "$influx_status" = "CREATING" ]; then
            send_alert "InfluxDB instance running ($influx_status) - ~$200-500/month" "HIGH"
            high_cost_found=$((high_cost_found + 1))
        elif [ "$influx_status" = "DELETING" ]; then
            echo "  InfluxDB: Deleting (charges stopping)"
        fi
    fi
    
    # Check EC2 instances
    ec2_count=$(aws ec2 describe-instances --region $REGION --filters "Name=tag:AquaInsight,Values=*" "Name=instance-state-name,Values=running,pending" --query 'length(Reservations[].Instances[])' --output text 2>/dev/null || echo "0")
    if [ "$ec2_count" -gt 0 ]; then
        send_alert "$ec2_count EC2 instances running - ~$50-200/month each" "HIGH"
        high_cost_found=$((high_cost_found + 1))
    fi
    
    # Check NAT Gateways
    nat_count=$(aws ec2 describe-nat-gateways --region $REGION --filter "Name=state,Values=available" --query 'length(NatGateways[])' --output text 2>/dev/null || echo "0")
    if [ "$nat_count" -gt 0 ]; then
        send_alert "$nat_count NAT Gateways running - ~$45/month each" "HIGH"
        high_cost_found=$((high_cost_found + 1))
    fi
    
    # Check RDS instances
    rds_count=$(aws rds describe-db-instances --region $REGION --query 'length(DBInstances[?contains(DBName, `aqua`) || contains(DBInstanceIdentifier, `aqua`)])' --output text 2>/dev/null || echo "0")
    if [ "$rds_count" -gt 0 ]; then
        send_alert "$rds_count RDS instances running - ~$100-300/month each" "HIGH"
        high_cost_found=$((high_cost_found + 1))
    fi
    
    # Check Load Balancers
    alb_count=$(aws elbv2 describe-load-balancers --region $REGION --query 'length(LoadBalancers[?contains(LoadBalancerName, `aqua`)])' --output text 2>/dev/null || echo "0")
    if [ "$alb_count" -gt 0 ]; then
        send_alert "$alb_count Load Balancers running - ~$20/month each" "MEDIUM"
        high_cost_found=$((high_cost_found + 1))
    fi
    
    # Check ECS running tasks
    ecs_tasks=0
    ecs_clusters=$(aws ecs list-clusters --region $REGION --query 'clusterArns[?contains(@, `AquaInsight`)]' --output text 2>/dev/null || echo "")
    if [ ! -z "$ecs_clusters" ]; then
        for cluster in $ecs_clusters; do
            cluster_tasks=$(aws ecs list-tasks --cluster "$cluster" --region $REGION --query 'length(taskArns)' --output text 2>/dev/null || echo "0")
            ecs_tasks=$((ecs_tasks + cluster_tasks))
        done
    fi
    if [ "$ecs_tasks" -gt 0 ]; then
        send_alert "$ecs_tasks ECS tasks running - Fargate charges apply" "MEDIUM"
    fi
    
    # Summary for this poll
    if [ "$high_cost_found" -eq 0 ]; then
        echo "  No high-cost resources found"
    else
        echo "  $high_cost_found HIGH-COST resources detected!"
        echo "  Potential monthly cost: $50-500+"
        echo "  Run: ./cleanup_script.sh"
    fi
    
    # Wait before next poll (unless it's the last one)
    if [ $poll_count -lt $MAX_POLLS ]; then
        echo "  Next check in $POLL_INTERVAL seconds..."
        echo ""
        sleep $POLL_INTERVAL
    fi
done

echo "Monitoring completed after $MAX_POLLS polls"
echo "Check billing_alerts.log for any alerts that occurred"