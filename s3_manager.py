import boto3
from botocore.exceptions import ClientError
from time import time_ns

from credentials import *
from constants import *


class AWSAcademyS3Manager:
    def __init__(self, aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY, aws_session_token=AWS_SESSION_TOKEN, region_name=REGION):

        self.region_name = region_name
        self.session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name=self.region_name
        )
        self.s3_client = self.session.client('s3')
        self.s3_resource = self.session.resource('s3')


    def create_bucket(self, bucket_name):
        try:
            if self.region_name == 'us-east-1':
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region_name}
                )
            print(f"Successfully created bucket: '{bucket_name}'")
            return True
        except ClientError as e:
            print(f"Error creating bucket: {e}")
            return False


    def bucket_status(self, bucket_name):
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            print(f"Bucket '{bucket_name}' exists and is accessible.")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '403':
                print(f"Bucket '{bucket_name}' exists, but you do not have permission to access it.")
            elif error_code == '404':
                print(f"Bucket '{bucket_name}' does not exist.")
            else:
                print(f"Error checking bucket status: {e}")
            return False


    def empty_bucket(self, bucket_name):
        print(f"Emptying bucket '{bucket_name}'...")
        try:
            bucket = self.s3_resource.Bucket(bucket_name)
            
            # Delete all standard objects
            bucket.objects.all().delete()
            
            # Delete all object versions (if versioning is enabled)
            bucket.object_versions.all().delete()
            
            print(f"Successfully emptied bucket: '{bucket_name}'")
            return True
        except ClientError as e:
            print(f"Error emptying bucket: {e}")
            return False

    def remove_bucket(self, bucket_name):
        try:
            self.s3_client.delete_bucket(Bucket=bucket_name)
            print(f"Successfully deleted bucket: '{bucket_name}'")
            return True
        except ClientError as e:
            print(f"Error deleting bucket: {e}")
            return False
        
    def upload_file(self, bucket_name, file_name='/Users/admin/Documents/CC/project/receips/receipt.jpeg'):
        try:
            # Local File, Target Bucket, Target Key
            self.s3_client.upload_file(file_name, bucket_name, str(time_ns()))
            print(f"Successfully uploaded file '{file_name}' to S3.")
            return True
        except FileNotFoundError:
            print(f"Error: The local file '{file_name}' was not found. Please check the path.")

            return False
        except ClientError as e:
            print(f"Error uploading file to S3: {e}")

            return False


if __name__ == "__main__":

    s3_manager = AWSAcademyS3Manager(
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        aws_session_token=AWS_SESSION_TOKEN,
        region_name=REGION
    )

    action = input("1: status\t2: create bucket\t3: empty bucket\t4: delete bucket\t5: upload file\nx: to exit\tChoose (1 - 4):\n")

    while action != 'x':
        match action:
            case '1':
                s3_manager.bucket_status(BUCKET_NAME)
            case '2':
                s3_manager.create_bucket(BUCKET_NAME)
            case '3':
                s3_manager.empty_bucket(BUCKET_NAME)
            case '4':
                s3_manager.remove_bucket(BUCKET_NAME)
            case '5':
                s3_manager.upload_file(BUCKET_NAME, file_name=FILE_NAME)
            case _:
                print(f'Huh? ({action})')
        action = input("1: status\t2: create bucket\t3: empty bucket\t4: delete bucket\t5: upload file\nx: to exit\tChoose (1 - 4):\n")

    print('exiting program...')
