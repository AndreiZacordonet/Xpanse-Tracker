def lambda_handler(event, context):
    """
    This is the entry point for the AWS Lambda function.
    """
    print("Hello, World! This is printed to CloudWatch Logs.")
    
    # It is best practice for Lambda functions to return a response payload
    return {
        'statusCode': 200,
        'body': 'Hello, World!'
    }
