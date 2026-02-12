import os
from dotenv import load_dotenv

# Force reload of .env file
load_dotenv(override=True)

print("--- DEBUGGING ENVIRONMENT VARIABLES ---")

# 1. Check AWS
aws_key = os.getenv('AWS_ACCESS_KEY_ID')
if aws_key:
    print(f"✅ AWS Key Found: {aws_key[:4]}... (Hidden)")
else:
    print("❌ AWS Key NOT FOUND. Check spelling in .env")

# 2. Check Azure
azure_conn = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
if azure_conn:
    print(f"✅ Azure Connection String Found: {azure_conn[:10]}... (Hidden)")
else:
    print("❌ Azure Connection String NOT FOUND.")
    # Check if the user used the old name
    old_name = os.getenv('AZURE_CONNECTION_STRING')
    if old_name:
        print("   ⚠️  Found 'AZURE_CONNECTION_STRING' instead. Please rename it to 'AZURE_STORAGE_CONNECTION_STRING' in your .env file.")

print("---------------------------------------")