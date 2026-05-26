import boto3
import json
import io
import zipfile
from botocore.exceptions import ClientError

from credentials import *
from constants import *


def create_zip_deployment(file_name):
        try:
            with open(file_name, 'r') as file:
                code = file.read()
            
            # Create a zip file in memory
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.writestr(file_name, code)
            
            return zip_buffer.getvalue()
        except FileNotFoundError:
            print(f"Error: Could not find '{file_name}'. Ensure it is in the same directory.")
            return None


class AWSLambdaManager:
    def __init__(self, aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, aws_session_token=AWS_SESSION_TOKEN, region_name=REGION):
        self.lambda_client = boto3.client(
            'lambda',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name=region_name
        )


    def create_function(self, function_name, role_arn, file_name):

        print(f"Creating Lambda function '{function_name}'...")

        zip_bytes = create_zip_deployment(file_name)
        if not zip_bytes:
            return False

        try:
            response = self.lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.12', # adjust if needed
                Role=role_arn,
                Handler=f"{file_name.replace('.py', '')}.lambda_handler",
                Code={'ZipFile': zip_bytes},
                Description='A simple Hello World Lambda function',
                Timeout=10,
                MemorySize=128
            )
            print(f"Successfully created Lambda function: '{function_name}'")

            return True
        except ClientError as e:
            print(f"Error creating function: {e}")

            return False
        

    def update_function(self, function_name, file_name):
        print(f"Updating Lambda function '{function_name}' code...")

        zip_bytes = create_zip_deployment(file_name)
        if not zip_bytes:
            return False

        try:
            response = self.lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_bytes
            )
            print(f"Successfully updated Lambda function code for: '{function_name}'")
            return True
            
        except self.lambda_client.exceptions.ResourceNotFoundException:
            print(f"Error: Function '{function_name}' does not exist. Create it first.")
            return False
        except ClientError as e:
            print(f"Error updating function: {e}")
            return False


    def get_status(self, function_name):

        try:
            response = self.lambda_client.get_function(FunctionName=function_name)
            state = response['Configuration']['State']
            last_update_status = response['Configuration']['LastUpdateStatus']

            print(f"Status of '{function_name}': State={state}, Last Update={last_update_status}")

            return response
        
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"Function '{function_name}' does not exist.")
            else:
                print(f"Error getting function status: {e}")

            return None


    def invoke_function(self, function_name):

        print(f"Invoking Lambda function '{function_name}'...")

        try:
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse' # Waits for the function to finish and return a result
            )
            
            # Read the payload stream returned by the function
            payload = response['Payload'].read().decode('utf-8')
            payload_dict = json.loads(payload)
            
            print(f"Invocation successful. Result:")
            print(json.dumps(payload_dict, indent=2))

            # extract the URL from the response body
            if 'body' in payload_dict:
                body_data = payload_dict['body']
                if isinstance(body_data, str):
                    body_data = json.loads(body_data)
                
                url = body_data.get('upload_url')
                if url:
                    return url
            
            # fallback
            return payload_dict.get('upload_url')
        
        except ClientError as e:
            print(f"Error invoking function: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from Lambda response: {e}")
            return None


    def delete_function(self, function_name):

        print(f"Deleting Lambda function '{function_name}'...")
        try:
            self.lambda_client.delete_function(FunctionName=function_name)
            print(f"Successfully deleted Lambda function: '{function_name}'")

            return True
        
        except ClientError as e:
            print(f"Error deleting function: {e}")

            return False


    def get_arn(self, function_name):
        try:
            response = self.lambda_client.get_function(FunctionName=function_name)
            arn = response['Configuration']['FunctionArn']
            print(f'arn={arn}')
            return arn
        
        except Exception as e:
            print(f"Error fetching Lambda ARN: {e}")
            return None


if __name__ == "__main__":

    # Initialize manager
    lambda_manager = AWSLambdaManager(
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        aws_session_token=AWS_SESSION_TOKEN,
        region_name=REGION
    )

    while (action := input(f'1: {EXTRACT_TEXT_LAMBDA['name']}\t2: {GENERATE_PRESIGNED_URL_LAMBDA['name']}\nChoose function:\n')) not in ('1', '2'):
        pass

    FUNCTION_NAME, FUNCTION_FILE = (EXTRACT_TEXT_LAMBDA.get('name'), EXTRACT_TEXT_LAMBDA.get('file')) if action == '1' \
                                    else (GENERATE_PRESIGNED_URL_LAMBDA.get('name'), GENERATE_PRESIGNED_URL_LAMBDA.get('file'))

    while (action := input("1: status\t2: create function\t3: update function\t4: trigger function\t5: delete function\t6: get arn\nx: to exit\nChoose (1 - 6):\n")) != 'x':
        match action:
            case '1':
                lambda_manager.get_status(FUNCTION_NAME)
            case '2':
                lambda_manager.create_function(FUNCTION_NAME, ROLE_ARN, FUNCTION_FILE)
            case '3':
                lambda_manager.update_function(FUNCTION_NAME, FUNCTION_FILE)
            case '4':
                result = lambda_manager.invoke_function(FUNCTION_NAME)
                print(result, type(result))
            case '5':
                lambda_manager.delete_function(FUNCTION_NAME)
            case '6':
                lambda_manager.get_arn(FUNCTION_NAME)
            case _:
                print(f'Huh? ({action})')

    print('exitin...')
