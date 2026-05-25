from botocore.exceptions import ClientError

from lambda_manager import *
from s3_manager import *
from dynamo_manager import *


def setup_s3_lambda_trigger(lambda_manager, s3_manager):
    print("Linking S3 and Lambda...")

    # STEP 1: Give S3 permission to invoke your Lambda function
    try:
        lambda_manager.lambda_client.add_permission(
            FunctionName=FUNCTION_NAME,
            StatementId='s3-invoke-permission-1', # Must be unique each time you run this
            Action='lambda:InvokeFunction',
            Principal='s3.amazonaws.com',
            SourceArn=f'arn:aws:s3:::{BUCKET_NAME}'
        )
        print("Granted S3 permission to invoke Lambda.")

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceConflictException':
            print("Permission already exists. Skipping.")
        else:
            print(f"Error adding permission: {e}")
            return False

    # STEP 2: Configure the S3 bucket to send the notification
    try:
        s3_manager.s3_client.put_bucket_notification_configuration(
            Bucket=BUCKET_NAME,
            NotificationConfiguration={
                'LambdaFunctionConfigurations': [
                    {
                        'LambdaFunctionArn': lambda_manager.get_arn(FUNCTION_NAME),
                        'Events': ['s3:ObjectCreated:*'] # Triggers on ANY file upload
                    }
                ]
            }
        )
        print(f"Configured S3 bucket '{BUCKET_NAME}' to trigger Lambda.")

        return True
    except ClientError as e:
        print(f"Error configuring S3 notifications: {e}")

        return False
    

if __name__ == "__main__":

    # Initilize s3 manager
    s3_manager = AWSAcademyS3Manager(
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        aws_session_token=AWS_SESSION_TOKEN,
        region_name=REGION
    )

    # Initialize lambda manager
    lambda_manager = AWSLambdaManager(
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        aws_session_token=AWS_SESSION_TOKEN,
        region_name=REGION
    )

    # Initialize dynamodb manager
    dynamodb_manager = AWSAcademyDynamoDBManager(
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        aws_session_token=AWS_SESSION_TOKEN,
        region_name=REGION
    )

    while (action := input('1: status all\t2: create all\t3: connect all\t4: trigger flow\t5: all down\nx: exit\n')) != 'x':
        match action:
            case '1':
                s3_manager.bucket_status(BUCKET_NAME)
                lambda_manager.get_status(FUNCTION_NAME)
                dynamodb_manager.table_status(RECEIPT_TABLE)
            case '2':
                s3_manager.create_bucket(BUCKET_NAME)
                lambda_manager.create_function(FUNCTION_NAME)
                dynamodb_manager.create_table(RECEIPT_TABLE)
            case '3':
                setup_s3_lambda_trigger(lambda_manager, s3_manager)
            case '4':
                s3_manager.upload_file(BUCKET_NAME, FILE_NAME)
            case '5':
                s3_manager.empty_bucket(BUCKET_NAME)
                s3_manager.remove_bucket(BUCKET_NAME)
                lambda_manager.delete_function(FUNCTION_NAME)
                dynamodb_manager.delete_table(RECEIPT_TABLE)
            case _:
                print(f'Huh? ({action})')


    print('exiting program...')

