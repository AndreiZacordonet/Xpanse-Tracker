import boto3
from botocore.exceptions import ClientError

from lambda_manager import AWSLambdaManager
from credentials import *
from constants import *


class AWSAcademyAPIGatewayManager:

    def __init__(self, aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, aws_session_token=AWS_SESSION_TOKEN, region_name=REGION):
        self.region_name = region_name
        self.session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name=self.region_name
        )
        self.apigw_client = self.session.client('apigateway')

        self.lambda_manager = AWSLambdaManager(
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            aws_session_token=AWS_SESSION_TOKEN,
            region_name=REGION
        )

        with open('api_id', 'r') as f:
            api_id = f.readline()
            self.api_id = api_id if api_id else ''


    def create_lambda_api(self, api_name, lambda_name, stage_name='prod'):
        print(f"Attempting to create API Gateway '{api_name}'...")

        try:
            # create REST API
            api = self.apigw_client.create_rest_api(name=api_name)
            api_id = api['id']
            print(f"Created API with ID: {api_id}")

            # save api_id
            self.api_id = api_id
            with open('api_id', 'w') as f:
                f.write(str(api_id))

            # get Root Resource ID ('/' path)
            resources = self.apigw_client.get_resources(restApiId=api_id)
            root_id = resources['items'][0]['id']

            # create POST Method on the Root
            self.apigw_client.put_method(
                restApiId=api_id,
                resourceId=root_id,
                httpMethod='POST',
                authorizationType='NONE'
            )

            lambda_arn = self.lambda_manager.get_arn(lambda_name)

            # integrate the POST Method with the Lambda Function
            integration_uri = f"arn:aws:apigateway:{self.region_name}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
            self.apigw_client.put_integration(
                restApiId=api_id,
                resourceId=root_id,
                httpMethod='POST',
                type='AWS_PROXY',   # NOTE: lambda return dictionary
                integrationHttpMethod='POST', 
                uri=integration_uri
            )

            # grant permission
            account_id = lambda_arn.split(':')[4]
            source_arn = f"arn:aws:execute-api:{self.region_name}:{account_id}:{api_id}/*/*"
            
            try:
                self.lambda_manager.lambda_client.add_permission(
                    FunctionName=lambda_name,
                    StatementId=f"apigw-invoke-{api_id}",
                    Action="lambda:InvokeFunction",
                    Principal="apigateway.amazonaws.com",
                    SourceArn=source_arn
                )
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceConflictException':
                    raise e

            # deploy API
            self.apigw_client.create_deployment(
                restApiId=api_id,
                stageName=stage_name
            )

            invoke_url = f"https://{api_id}.execute-api.{self.region_name}.amazonaws.com/{stage_name}/"
            print(f"Successfully deployed! API Endpoint URL: {invoke_url}")
            
            return invoke_url

        except ClientError as e:
            print(f"Error creating API Gateway: {e}")
            return None
        

    def api_status(self):
        print(f"Checking status for API ID: '{self.api_id}'...")

        if not self.api_id:
            print(f"API with ID '{self.api_id}' does not exist or has already been deleted.")
            return False

        try:
            # verify the REST API exists
            api = self.apigw_client.get_rest_api(restApiId=self.api_id)
            print(f"API '{api['name']}' exists.")
            
            # fetch active stages
            stages = self.apigw_client.get_stages(restApiId=self.api_id)
            stage_items = stages.get('item', [])
            
            if stage_items:
                print("Active deployments:")
                for stage in stage_items:
                    stage_name = stage['stageName']
                    invoke_url = f"https://{self.api_id}.execute-api.{self.region_name}.amazonaws.com/{stage_name}/"
                    print(f" - [{stage_name}] {invoke_url}")
                return True
            else:
                print("API exists but is not currently deployed to any stages.")
                return False
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NotFoundException':
                print(f"API with ID '{self.api_id}' does not exist or has already been deleted.")
            else:
                print(f"Error checking API status: {e}")
                
            return False


    def delete_api(self):
        print(f"Attempting to delete API with ID '{self.api_id}'...")

        try:
            self.apigw_client.delete_rest_api(restApiId=self.api_id)
            print(f"Successfully deleted API: '{self.api_id}'.")
            print("The Lambda function is no longer accessible via this endpoint.")

            self.api_id = ''
            with open('api_id', 'w') as f:
                f.write('')

            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NotFoundException':
                print(f"Error: API with ID '{self.api_id}' does not exist.")
            elif error_code == 'TooManyRequestsException':
                print("Error: Rate limit exceeded. Try again in a moment.")
            else:
                print(f"Error deleting API: {e}")
                
            return False


if __name__ == "__main__":
    
    # TODO: define these in constants.py 
    LAMBDA_FUNCTION_NAME = GENERATE_PRESIGNED_URL_LAMBDA.get('name')

    apigw_manager = AWSAcademyAPIGatewayManager(
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        aws_session_token=AWS_SESSION_TOKEN,
        region_name=REGION
    )
    
    while (action := input("1: status\t2: create api gateway\t3: delete api\nx: to exit\n")) != 'x':
        match action:
            case '1':
                apigw_manager.api_status()
            case '2':
                apigw_manager.create_lambda_api(API_NAME, LAMBDA_FUNCTION_NAME)
            case '3':
                apigw_manager.delete_api()
            case _:
                print(f"Huh? ({action})")
        
    print('exiting program...')
