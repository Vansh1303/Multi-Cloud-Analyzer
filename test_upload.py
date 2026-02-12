import os
from dotenv import load_dotenv
from cloud_manager import AWSStorage, AzureStorage

# Load the bucket names from .env
load_dotenv()
AWS_BUCKET = os.getenv('AWS_BUCKET_NAME')
AZURE_CONTAINER = os.getenv('AZURE_CONTAINER_NAME')

def create_dummy_file(filename="test_file.txt", size_kb=1):
    with open(filename, "wb") as f:
        f.write(os.urandom(size_kb * 1024))
    return filename

def run_test():
    filename = create_dummy_file()
    print(f"🚀 Created dummy file: {filename}")
    print(f"📋 Target AWS Bucket: {AWS_BUCKET}")
    print(f"📋 Target Azure Container: {AZURE_CONTAINER}")

    # --- Test AWS ---
    try:
        print("\nTesting AWS Upload...")
        aws = AWSStorage()
        # FIX: We now pass the correct AWS_BUCKET variable
        time_taken = aws.upload_file(filename, AWS_BUCKET, filename)
        
        if time_taken != -1:
            print(f"✅ [AWS] Success! Time: {time_taken:.4f} seconds")
        else:
            print(f"❌ [AWS] Failed (Check logs above)")
            
    except Exception as e:
        print(f"❌ [AWS] Crashed: {e}")

    # --- Test Azure ---
    try:
        print("\nTesting Azure Upload...")
        azure = AzureStorage()
        # FIX: We now pass the correct AZURE_CONTAINER variable
        time_taken = azure.upload_file(filename, AZURE_CONTAINER, filename)
        
        if time_taken != -1:
            print(f"✅ [Azure] Success! Time: {time_taken:.4f} seconds")
        else:
            print(f"❌ [Azure] Failed (Check logs above)")

    except Exception as e:
        print(f"❌ [Azure] Crashed: {e}")

    # Clean up local file
    if os.path.exists(filename):
        os.remove(filename)

if __name__ == "__main__":
    run_test()