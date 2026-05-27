import boto3
import json
import time

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Receipt')

def lambda_handler(event, context):
    # ID from apigw path
    item_id = event.get('pathParameters', {}).get('id')
    
    if not item_id:
        return {"statusCode": 400, "body": json.dumps({"error": "Missing id"})}

    max_retries = 4
    base_delay = 1 # seconds

    for attempt in range(max_retries):
        response = table.get_item(Key={'id': item_id})
        
        if 'Item' in response:
            return {
                "statusCode": 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT'
                },
                "body": json.dumps(response['Item'], default=str) # default=str handles Decimal types
            }
        
        # exponential backoff
        if attempt < max_retries - 1:
            time.sleep(base_delay * (2 ** attempt))

    return {
        "statusCode": 404,
        "body": json.dumps({"error": "Item not found"})
    }