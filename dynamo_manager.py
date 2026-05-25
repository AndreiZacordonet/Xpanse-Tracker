import boto3
from botocore.exceptions import ClientError

from credentials import *
from constants import *


class AWSAcademyDynamoDBManager:
    def __init__(self, aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, aws_session_token=AWS_SESSION_TOKEN, region_name=REGION):
        
        self.region_name = region_name
        self.session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name=self.region_name
        )
        self.dynamodb_client = self.session.client('dynamodb')
        self.dynamodb_resource = self.session.resource('dynamodb')


    def list_tables(self):
        print("Fetching DynamoDB tables...")

        try:
            response = self.dynamodb_client.list_tables()
            tables = response.get('TableNames', [])
            if tables:
                print(f"Found {len(tables)} table(s):")
                for table in tables:
                    print(f" - {table}")
            else:
                print("No tables found in this region.")

            return tables
        
        except ClientError as e:
            print(f"Error listing tables: {e}")

            return None


    def table_status(self, table_name):
        try:
            response = self.dynamodb_client.describe_table(TableName=table_name)
            status = response['Table']['TableStatus']
            print(f"Table '{table_name}' exists. Current status: {status}")

            return True
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                print(f"Table '{table_name}' does not exist.")
            elif error_code == 'AccessDeniedException':
                print(f"Table '{table_name}' might exist, but you do not have permission to access it.")
            else:
                print(f"Error checking table status: {e}")

            return False


    def create_table(self, table_name):
        print(f"Attempting to create table '{table_name}'...")

        try:
            # Creating a simple table with a string partition key called 'id'
            table = self.dynamodb_resource.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'id', 'KeyType': 'HASH'}  # Partition key
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'id', 'AttributeType': 'S'}  # S = String
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            
            # Wait for the table to exist before proceeding
            print(f"Waiting for table '{table_name}' to be created (this may take a moment)...")
            table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
            
            print(f"Successfully created table: '{table_name}'")

            return True
        
        except ClientError as e:
            error_code = e.response['Error']['Code']

            if error_code == 'ResourceInUseException':
                print(f"Error: Table '{table_name}' already exists or is currently being created.")
            else:
                print(f"Error creating table: {e}")

            return False


    def delete_table(self, table_name):
        print(f"Attempting to delete table '{table_name}'...")

        try:
            self.dynamodb_client.delete_table(TableName=table_name)
            
            # Wait for the table to be deleted
            print(f"Waiting for table '{table_name}' to be deleted...")
            self.dynamodb_client.get_waiter('table_not_exists').wait(TableName=table_name)
            
            print(f"Successfully deleted table: '{table_name}'")

            return True
        
        except ClientError as e:
            error_code = e.response['Error']['Code']

            if error_code == 'ResourceNotFoundException':
                print(f"Error: Table '{table_name}' does not exist.")
            else:
                print(f"Error deleting table: {e}")

            return False


if __name__ == "__main__":
    
    dynamodb_manager = AWSAcademyDynamoDBManager(
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        aws_session_token=AWS_SESSION_TOKEN,
        region_name=REGION
    )
    
    while (action := input("1: list tables\t2: table status\t3: create table\t4: delete table\nx: to exit\n")) != 'x':
        match action:
            case '1':
                dynamodb_manager.list_tables()
            case '2':
                dynamodb_manager.table_status(RECEIPT_TABLE)
            case '3':
                dynamodb_manager.create_table(RECEIPT_TABLE)
            case '4':
                dynamodb_manager.delete_table(RECEIPT_TABLE)
            case _:
                print(f"Huh? ({action})")
        

    print('exiting program...')