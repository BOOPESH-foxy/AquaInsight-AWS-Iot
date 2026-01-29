import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from aws_clients import sns_client

load_dotenv()

sns = sns_client()

AWS_REGION = os.getenv("REGION")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")

def create_sns_topic(topic_name, display_name=None):
    """Create SNS topic for alerts"""
    
    try:
        # Check if topic already exists
        response = sns.list_topics()
        topic_arn = f"arn:aws:sns:{AWS_REGION}:{ACCOUNT_ID}:{topic_name}"
        
        for topic in response.get('Topics', []):
            if topic['TopicArn'] == topic_arn:
                print(f"! SNS topic '{topic_name}' already exists")
                return topic_arn
        
        print(f"! Creating SNS topic '{topic_name}'...")
        
        create_params = {
            'Name': topic_name,
            'Tags': [
                {'Key': 'AquaInsight', 'Value': 'SNS'},
                {'Key': 'Name', 'Value': topic_name}
            ]
        }
        
        if display_name:
            create_params['Attributes'] = {'DisplayName': display_name}
        
        response = sns.create_topic(**create_params)
        
        topic_arn = response['TopicArn']
        print(f"+ Created SNS topic: {topic_arn}")
        return topic_arn
        
    except Exception as e:
        print(f":: Error creating SNS topic '{topic_name}': {e}")
        raise


def create_district_topics():
    """Create SNS topics for different districts"""
    
    topics = {}
    
    # General topic for all alerts
    topics['general'] = create_sns_topic(
        'aquaInsight-alerts-general',
        'AquaInsight General Alerts'
    )
    
    # District-specific topics (can be expanded)
    district_topics = [
        'karur',
        'tiruppur'
    ]
    
    for district in district_topics:
        topic_name = f'aquaInsight-alerts-{district}'
        display_name = f'AquaInsight {district.title()} District Alerts'
        topics[district] = create_sns_topic(topic_name, display_name)
    
    return topics


def get_topic_arn(topic_name):
    """Get SNS topic ARN by name"""
    return f"arn:aws:sns:{AWS_REGION}:{ACCOUNT_ID}:{topic_name}"


def list_all_topics():
    """List all AquaInsight SNS topics"""
    
    try:
        response = sns.list_topics()
        aqua_topics = []
        
        for topic in response.get('Topics', []):
            topic_arn = topic['TopicArn']
            if 'aquaInsight' in topic_arn:
                aqua_topics.append(topic_arn)
        
        print(f"! Found {len(aqua_topics)} AquaInsight SNS topics:")
        for topic in aqua_topics:
            topic_name = topic.split(':')[-1]
            print(f"  - {topic_name}: {topic}")
            
        return aqua_topics
        
    except Exception as e:
        print(f":: Error listing topics: {e}")
        raise


def subscribe_email_to_topic(topic_arn, email_address):
    """Subscribe an email address to SNS topic"""
    
    try:
        print(f"! Subscribing email '{email_address}' to topic...")
        
        response = sns.subscribe(
            TopicArn=topic_arn,
            Protocol='email',
            Endpoint=email_address
        )
        
        subscription_arn = response['SubscriptionArn']
        print(f"+ Email subscription created: {subscription_arn}")
        print(f"! Check email '{email_address}' to confirm subscription")
        
        return subscription_arn
        
    except Exception as e:
        print(f":: Error subscribing email: {e}")
        raise


def get_topic_subscriptions(topic_arn):
    """Get all subscriptions for a topic"""
    
    try:
        response = sns.list_subscriptions_by_topic(TopicArn=topic_arn)
        subscriptions = response.get('Subscriptions', [])
        
        print(f"! Found {len(subscriptions)} subscriptions:")
        for sub in subscriptions:
            protocol = sub['Protocol']
            endpoint = sub['Endpoint']
            status = sub.get('SubscriptionArn', 'PendingConfirmation')
            print(f"  - {protocol}: {endpoint} ({status})")
            
        return subscriptions
        
    except Exception as e:
        print(f":: Error listing subscriptions: {e}")
        raise