REGION = "us-east-1"

BUCKET_NAME = "receipt-pic-upload"

EXTRACT_TEXT_LAMBDA, GENERATE_PRESIGNED_URL_LAMBDA = {}, {}

EXTRACT_TEXT_LAMBDA['name'] = "trigger-textract-at-bucket-upload"
EXTRACT_TEXT_LAMBDA['file'] = "lambda_function_extract_text.py"
GENERATE_PRESIGNED_URL_LAMBDA['name'] = "generate-presigned-url"
GENERATE_PRESIGNED_URL_LAMBDA['file'] = "lambda_function_generate_url.py"

RECEIPT_TEST_FILE = '/Users/admin/Documents/CC/project/receips/receipt.jpeg'

RECEIPT_TABLE = 'Receipt'
