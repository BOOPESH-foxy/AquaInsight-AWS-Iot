""" This file is used to create the IoT rule dependent resources (SQS,Timestream)"""
from tank_metadata import tankName,location
from aws_clients import sqs_client
sqs_client = sqs_client()

def create_queue():
    """Creates an AWS SQS queue"""
    try:
        response_queue_creation = sqs_client.create_queue(
            QueueName=f'{tankName}-queue',
            tags={
                'TankLocation': f'{location}'
            }
        )
        url =  response_queue_creation['QueueUrl']
        return url
    
    except Exception as e:
        print(":: Error ::",e)
        raise


def get_queue_arn(url):
    """Gets the queue arn for the provided name : if exists"""
    try:
        response_queue_attributes = sqs_client.get_queue_attributes(
        QueueUrl=f'{url}',
        AttributeNames=[
            'QueueArn'
            ])
        arn = response_queue_attributes['Attributes']['QueueArn']
        return arn

    except Exception as e:
        print(":: Error ::",e)
        raise
        


def get_queue_url(QueueName):
    """Gets the queue url for the provided name : if exists"""
    try:
        response_url = sqs_client.get_queue_url(
            QueueName=f'{QueueName}'
        )
        return response_url['QueueUrl']

    except Exception as e:
        print(":: Error ::",e)
        raise


def delete_queue(QueueName):
    """Deletes the queus in AWS SQS with the provided name"""
    queue_url = get_queue_url(QueueName)
    try:
        response_deletion = sqs_client.delete_queue(
            QueueUrl=queue_url
        )
        print(f"- Deleted Queue {QueueName}")

    except Exception as e:
        print(":: Error ::",e)
        raise
