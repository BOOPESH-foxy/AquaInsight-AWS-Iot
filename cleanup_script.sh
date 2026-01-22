#!/bin/bash
echo "🧹 Cleaning up AquaInsight AWS resources..."

# ECS cleanup
echo "Deleting ECS resources..."
aws ecs update-service --cluster AquaInsight-Cluster --service AquaInsight-Service --desired-count 0 --region ap-south-1 2>/dev/null
sleep 10
aws ecs delete-service --cluster AquaInsight-Cluster --service AquaInsight-Service --region ap-south-1 2>/dev/null
aws ecs delete-cluster --cluster AquaInsight-Cluster --region ap-south-1 2>/dev/null

# IoT cleanup
echo "Deleting IoT resources..."
aws iot delete-topic-rule --rule-name aqua_data_route_rule --region ap-south-1 2>/dev/null

# SQS cleanup
echo "Deleting SQS queue..."
QUEUE_URL=$(aws sqs get-queue-url --queue-name AquaInsight-queue --region ap-south-1 --query 'QueueUrl' --output text 2>/dev/null)
if [ "$QUEUE_URL" != "None" ]; then
    aws sqs delete-queue --queue-url $QUEUE_URL --region ap-south-1
fi

# IAM cleanup
echo "Deleting IAM roles..."
aws iam delete-role-policy --role-name iot_to_sqs_role --policy-name iot_to_sqs_role-sqs-access 2>/dev/null
aws iam delete-role --role-name iot_to_sqs_role 2>/dev/null
aws iam delete-role-policy --role-name ecs_task_role --policy-name ecs_task_role-ecs-tasks 2>/dev/null
aws iam delete-role --role-name ecs_task_role 2>/dev/null

# CloudWatch cleanup
echo "Deleting CloudWatch logs..."
aws logs delete-log-group --log-group-name /aws/ecs/aquainsight --region ap-south-1 2>/dev/null

echo "✅ Cleanup complete!"
