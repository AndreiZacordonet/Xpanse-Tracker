import boto3
import json
import uuid
from botocore.exceptions import ClientError
from time import time_ns

s3_client = boto3.client('s3')
BUCKET_NAME = "receipt-pic-upload"

def lambda_handler(event, context):
    try:
        receipt_id = str(uuid.uuid4())
        object_key = str(time_ns())
        
        # generate presigned URL
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': object_key,
                # TODO: Force the client to upload a specific content type
                # 'ContentType': 'image/jpeg' 
            },
            ExpiresIn=300 # URL expires in 5 minutes
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*' 
            },
            'body': json.dumps({
                'message': 'Presigned URL generated successfully',
                'upload_url': presigned_url,
                'receipt_id': receipt_id,
                's3_key': object_key
            })
        }
        
    except ClientError as e:
        print(f"Boto3 Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to generate upload URL'})
        }