REGION = "us-east-1"

BUCKET_NAME = "receipt-pic-upload"

EXTRACT_TEXT_LAMBDA, GENERATE_PRESIGNED_URL_LAMBDA = {}, {}

EXTRACT_TEXT_LAMBDA['name'] = "trigger-textract-at-bucket-upload"
EXTRACT_TEXT_LAMBDA['file'] = "lambda_function_extract_text.py"
GENERATE_PRESIGNED_URL_LAMBDA['name'] = "generate-presigned-url"
GENERATE_PRESIGNED_URL_LAMBDA['file'] = "lambda_function_generate_url.py"
GET_RECEIPT_DATA_LAMBDA = {
    'name': 'get-receipt-data',
    'file': 'lambda_function_get_receipt_data.py'
}

API_NAME = "ReceiptUploadAPI"

RECEIPT_TEST_FILE = '/Users/admin/Documents/CC/project/receips/receipt.jpeg'

RECEIPT_TABLE = 'Receipt'
