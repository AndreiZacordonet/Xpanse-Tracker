import os
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY = os.getenv("aws_access_key_id")
AWS_SECRET_KEY = os.getenv("aws_secret_access_key")
AWS_SESSION_TOKEN = os.getenv("aws_session_token")

ROLE_ARN = os.getenv("ROLE_ARN")

if __name__ == '__main__':
    print(AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_SESSION_TOKEN)