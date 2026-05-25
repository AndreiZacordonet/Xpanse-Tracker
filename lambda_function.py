import json
import urllib.parse
import boto3

print('Loading function')

BUCKET_NAME = "receipt-pic-upload"

s3 = boto3.client('s3')
textract = boto3.client('textract')

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
        print("Sending to AWS Textract for analysis...")

        textract_response = textract.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            }
        )
        
        extracted_lines = []
        for block in textract_response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                extracted_lines.append(block['Text'])
                
        print(f"Successfully extracted {len(extracted_lines)} lines of text.")
        # print(extracted_lines)
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed document with Textract.',
                'uploaded_file': key,
                'bucket': bucket,
                'content_type': content_type,
                'extracted_text': extracted_lines 
            })
        }
        
    except KeyError as e:
        print(f"Error extracting data from event. Is this a valid S3 event payload? Details: {e}")
        raise e
    except Exception as e:
        print(f"Error: {e}")
        raise e
    