import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def extract_text_with_textract(image_bytes: bytes) -> str:
    """
    Extracts raw text deterministically from an image using AWS Textract.
    Requires AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_DEFAULT_REGION in the environment (or .env).
    """
    try:
        # Explicitly pass credentials from .env to boto3
        client = boto3.client(
            'textract',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        )
        
        print(f"[Textract] Image size: {len(image_bytes)} bytes")
        print(f"[Textract] Region: {os.getenv('AWS_DEFAULT_REGION', 'us-east-1')}")
        print(f"[Textract] Key present: {bool(os.getenv('AWS_ACCESS_KEY_ID'))}")
        
        # Call the synchronous detect_document_text API
        response = client.detect_document_text(
            Document={'Bytes': image_bytes}
        )
        
        # Log the full response metadata for debugging
        blocks = response.get('Blocks', [])
        print(f"[Textract] Total blocks returned: {len(blocks)}")
        
        extracted_text = ""
        for block in blocks:
            if block.get('BlockType') == 'LINE':
                if 'Text' in block:
                    extracted_text += block['Text'] + "\n"
                    
        print(f"[Textract] Extracted text length: {len(extracted_text)}")
        return extracted_text.strip()
        
    except Exception as e:
        import traceback
        print(f"[Textract] ERROR: {e}")
        traceback.print_exc()
        return ""
