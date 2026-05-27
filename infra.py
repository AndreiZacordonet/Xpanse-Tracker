from botocore.exceptions import ClientError
import requests

from lambda_manager import *
from s3_manager import *
from dynamo_manager import *
from apigw_manager import *


def setup_s3_lambda_trigger(lambda_manager, s3_manager, function_name):
    print("Linking S3 and Lambda...")

    # STEP 1: Give S3 permission to invoke your Lambda function
    try:
        lambda_manager.lambda_client.add_permission(
            FunctionName=function_name,
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
                        'LambdaFunctionArn': lambda_manager.get_arn(function_name),
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
    

def upload_file(file_name, presigned_url):
    if presigned_url:
        print(f"\nUploading '{file_name}'...")
        
        try:
            with open(file_name, 'rb') as file_data:
                response = requests.put(presigned_url, data=file_data)
                
            response.raise_for_status()
            
            print("\nFile uploaded successfully via requests")
            
        except FileNotFoundError:
            print(f"\nUpload failed: The file '{file_name}' was not found locally.")
        except requests.exceptions.RequestException as e:
            print(f"\nUpload failed: {e}")
            
    else:
        print("\nSkipping upload: Could not retrieve presigned URL.")


def get_presigned_url_and_s3_id(api_url) -> tuple[str, str]:
    response = requests.post(api_url)
    
    response.raise_for_status()
    
    data = response.json()
    
    return data.get("upload_url"), data.get("s3_key")


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

    # Initialize apigw manager
    apigw_manager = AWSAcademyAPIGatewayManager(
        lambda_manager=lambda_manager,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        aws_session_token=AWS_SESSION_TOKEN,
        region_name=REGION
    )

    while (action := input('1: status all\t2: create all\t3: connect all\t4: trigger flow\t5: all down\nx: exit\n')) != 'x':
        match action:
            case '1':
                s3_manager.bucket_status(BUCKET_NAME)
                lambda_manager.get_status(EXTRACT_TEXT_LAMBDA.get('name'))
                lambda_manager.get_status(GENERATE_PRESIGNED_URL_LAMBDA.get('name'))
                lambda_manager.get_status(GET_RECEIPT_DATA_LAMBDA.get('name'))
                dynamodb_manager.table_status(RECEIPT_TABLE)
                apigw_manager.api_status()
            case '2':
                s3_manager.create_bucket(BUCKET_NAME)
                lambda_manager.create_function(EXTRACT_TEXT_LAMBDA.get('name'), ROLE_ARN, EXTRACT_TEXT_LAMBDA.get('file'))
                lambda_manager.create_function(GENERATE_PRESIGNED_URL_LAMBDA.get('name'), ROLE_ARN, GENERATE_PRESIGNED_URL_LAMBDA.get('file'))
                lambda_manager.create_function(GET_RECEIPT_DATA_LAMBDA.get('name'), ROLE_ARN, GET_RECEIPT_DATA_LAMBDA.get('file'))
                dynamodb_manager.create_table(RECEIPT_TABLE)
                apigw_manager.create_lambda_api(api_name=API_NAME, 
                                                generate_url_lambda_name=GENERATE_PRESIGNED_URL_LAMBDA.get('name'),
                                                get_receipt_data_lambda_name=GET_RECEIPT_DATA_LAMBDA.get('name'))
            case '3':
                setup_s3_lambda_trigger(lambda_manager, s3_manager, EXTRACT_TEXT_LAMBDA.get('name'))
            case '4':
                presigned_url, s3_id = get_presigned_url_and_s3_id(apigw_manager.get_url())
                upload_file(RECEIPT_TEST_FILE, presigned_url)
            case '5':
                s3_manager.empty_bucket(BUCKET_NAME)
                s3_manager.remove_bucket(BUCKET_NAME)
                lambda_manager.delete_function(EXTRACT_TEXT_LAMBDA.get('name'))
                lambda_manager.delete_function(GENERATE_PRESIGNED_URL_LAMBDA.get('name'))
                lambda_manager.delete_function(GET_RECEIPT_DATA_LAMBDA.get('name'))
                dynamodb_manager.delete_table(RECEIPT_TABLE)
                apigw_manager.delete_api()
            case _:
                print(f'Huh? ({action})')


    print('exiting program...')

