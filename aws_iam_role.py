import json
from aws_clients import iam_client
client = iam_client()


def check_role_existence(role_name="iot_to_sqs_role"):
    """ Ensures an iam role exists for AWS IoT to send messages to SQS. Returns the role arn."""
    try:
        response_existense = client.get_role(RoleName=role_name)
        print(f"Reusing existing role: {role_name}")
        role_arn = response_existense["Role"]["Arn"]
        if(role_arn):
            print("!    Role exists")
            return role_arn
        else:
            return 0
        
    except Exception as e:
        print(":: Erroe ::",e)
        raise

def create_iot_to_sqs_role(queue_arn, role_name = "iot_to_sqs_role"):
    """ checks for existence and in absense creates an iam role for AWS IoT to send messages to SQS and returns the role arn."""

    role_arn = check_role_existence(role_name)
    if(role_arn):
        return role_arn
    
    else:
        try:
            trust_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "iot.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }

            response_role_creation = client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Role for AWS IoT Core to send messages to SQS",
            )
            role_arn = response_role_creation["Role"]["Arn"]

            policy_name = f"{role_name}-sqs-access"
            policy_doc = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "sqs:SendMessage",
                            "sqs:GetQueueAttributes",
                            "sqs:GetQueueUrl",
                        ],
                        "Resource": queue_arn,
                    }
                ],
            }

            client.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_doc),
            )

            waiter = client.get_waiter("role_exists")
            waiter.wait(
                RoleName=role_name
                )
            check_role_existence(role_name)
            return role_arn

        except Exception as e:
            print(":: Error ::",e)
            raise
