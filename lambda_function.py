import json
import urllib.parse
import boto3
import re
from decimal import Decimal

print('Loading function')

BUCKET_NAME = "receipt-pic-upload"
TABLE_NAME = "Receipt"

s3 = boto3.client('s3')
textract = boto3.client('textract')
dynamodb = boto3.resource('dynamodb')


def parse_float(val_str):
    """Converts comma-separated European decimals to Decimal for DynamoDB compatibility."""
    return Decimal(val_str.replace(',', '.'))


def parse_receipt_to_dict(text_lines):
    # Initialize the base structure with Decimals instead of floats
    receipt_data = {
        "store_name": text_lines[0].strip() if text_lines else "Unknown Store",
        "date": None,
        "time": None,
        "products": [],
        "total_no_discount": Decimal('0.0'),
        "total_discount": Decimal('0.0'),
        "total": Decimal('0.0'),
        "payment_method": "cash" # Default fallback
    }

    # 1. Extract Date, Time, and Payment Method
    for line in text_lines:
        # Match 'DATA:18/05/2026 ORA:21-13-00'
        dt_match = re.search(r'DATA:\s*(\d{2}/\d{2}/\d{4})\s*ORA:\s*(\d{2}[-:]\d{2}[-:]\d{2})', line, re.IGNORECASE)
        if dt_match:
            receipt_data["date"] = dt_match.group(1)
            receipt_data["time"] = dt_match.group(2).replace('-', ':')
            
        # Determine payment method
        if "CARD" in line.upper():
            receipt_data["payment_method"] = "card"
        elif "NUMERAR" in line.upper() or "CASH" in line.upper():
            receipt_data["payment_method"] = "cash"

    # 2. Extract Products, Prices, and Discounts
    i = 0
    while i < len(text_lines):
        line = text_lines[i]
        
        # Look for the Quantity x Price pattern (e.g., "2.000 BUC X 6,59")
        qty_match = re.match(r'(\d+[.,]\d+)\s*(?:BUC|KG)\s*[Xx]\s*(\d+[.,]\d+)', line, re.IGNORECASE)
        
        if qty_match:
            qty = parse_float(qty_match.group(1))
            price = parse_float(qty_match.group(2))
            
            # The next line is usually the product name
            name = text_lines[i + 1].strip() if i + 1 < len(text_lines) else "Unknown"
            
            # The line after the name is the subtotal (e.g., "13,18 B")
            subtotal = qty * price # Fallback
            if i + 2 < len(text_lines):
                sub_match = re.search(r'(\d+[.,]\d+)', text_lines[i + 2])
                if sub_match:
                    subtotal = parse_float(sub_match.group(1))
                    
            i += 2 # Fast-forward past name and subtotal

            # Look ahead for discount blocks (e.g., "Reducere", "DISCOUNT", "8,00-B")
            discount = Decimal('0.0')
            while i + 1 < len(text_lines):
                next_line = text_lines[i + 1]
                upper_next = next_line.upper()
                
                # If it's a discount label, skip over it
                if "REDUCERE" in upper_next or "DISCOUNT" in upper_next:
                    i += 1
                    continue
                    
                # Look for the negative discount value (e.g., "8,00-B" or "-8,00")
                disc_match = re.search(r'(\d+[.,]\d+)\s*-[A-Z]?|-\s*(\d+[.,]\d+)', next_line)
                if disc_match:
                    val = disc_match.group(1) if disc_match.group(1) else disc_match.group(2)
                    discount += parse_float(val)
                    i += 1
                    continue
                
                # If we don't match a label or a discount value, the discount block is over
                break
            
            # Compile the specific product
            receipt_data["products"].append({
                "name": name,
                "price": price,
                "quantity": qty,
                "subtotal": round(subtotal, 2),
                "discount": round(discount, 2),
                "total": round(subtotal - discount, 2)
            })
            
        i += 1

    # 3. Calculate Final Totals based on extracted items
    for p in receipt_data["products"]:
        receipt_data["total_no_discount"] += p["subtotal"]
        receipt_data["total_discount"] += p["discount"]

    receipt_data["total"] = receipt_data["total_no_discount"] - receipt_data["total_discount"]

    # Round totals
    receipt_data["total_no_discount"] = round(receipt_data["total_no_discount"], 2)
    receipt_data["total_discount"] = round(receipt_data["total_discount"], 2)
    receipt_data["total"] = round(receipt_data["total"], 2)

    return receipt_data


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

        formated_receipt_data = parse_receipt_to_dict(extracted_lines)
        formated_receipt_data['id'] = key

        # Save to DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(Item=formated_receipt_data)

        print(f"Successfully saved receipt '{key}' to DynamoDB table '{TABLE_NAME}'.")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed document with Textract.',
                'uploaded_file': key,
                'bucket': bucket,
                'content_type': content_type,
                'extracted_text': extracted_lines 
            }, default=float, ensure_ascii=False)
        }
        
    except KeyError as e:
        print(f"Error extracting data from event. Is this a valid S3 event payload? Details: {e}")
        raise e
    except Exception as e:
        print(f"Error: {e}")
        raise e
    