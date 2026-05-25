import json
import urllib.parse
import boto3

print('Loading function')

BUCKET_NAME = "receipt-pic-upload"

s3 = boto3.client('s3')

def lambda_handler(event, context):
    try:
        bucket = event['Records'][0]['s3']['bucket']['name']
        
        if bucket != BUCKET_NAME:
            print(f"Skipped: Upload detected in '{bucket}', but we only care about '{BUCKET_NAME}'.")
            return {
                'statusCode': 200, # Return 200 so AWS doesn't think the function failed
                'body': json.dumps({'message': f"Ignored upload from bucket: {bucket}"})
            }

        key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
        
        response = s3.get_object(Bucket=bucket, Key=key)
        content_type = response['ContentType']
        
        print(f"S3 Upload Accepted: File '{key}' in bucket '{bucket}' (Type: {content_type})")
        
        print("Hello, World! This is printed to CloudWatch Logs.")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Hello, World! Processed authorized bucket.',
                'uploaded_file': key,
                'bucket': bucket,
                'content_type': content_type
            })
        }
        
    except KeyError as e:
        print(f"Error extracting data from event. Is this a valid S3 event payload? Details: {e}")
        raise e
    except Exception as e:
        print(f"Error: {e}")
        raise e
    