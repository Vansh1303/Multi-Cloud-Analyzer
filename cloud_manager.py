import os
import time
import abc
from dotenv import load_dotenv

# AWS
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

# Azure
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import AzureError

load_dotenv()

class StorageInterface(abc.ABC):
    @abc.abstractmethod
    def upload_file(self, file_path: str, bucket_name: str, object_name: str = None) -> float:
        pass
    
    @abc.abstractmethod
    def download_file(self, bucket_name: str, object_name: str, file_path: str) -> float:
        pass

class AWSStorage(StorageInterface):
    def __init__(self):
        self.region = os.getenv('AWS_REGION', 'ap-southeast-1')
        self.s3_client = boto3.client(
            's3',
            region_name=self.region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )

    def upload_file(self, file_path: str, bucket_name: str, object_name: str = None) -> float:
        if object_name is None: object_name = os.path.basename(file_path)
        try:
            start = time.perf_counter()
            self.s3_client.upload_file(file_path, bucket_name, object_name)
            return time.perf_counter() - start
        except Exception as e:
            print(f"❌ [AWS Upload Error]: {e}")
            return -1.0

    def download_file(self, bucket_name: str, object_name: str, file_path: str) -> float:
        try:
            start = time.perf_counter()
            self.s3_client.download_file(bucket_name, object_name, file_path)
            return time.perf_counter() - start
        except Exception as e:
            print(f"❌ [AWS Download Error]: {e}")
            return -1.0

class AzureStorage(StorageInterface):
    def __init__(self):
        self.conn_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        self.blob_service_client = BlobServiceClient.from_connection_string(self.conn_str)

    def upload_file(self, file_path: str, bucket_name: str, object_name: str = None) -> float:
        if object_name is None: object_name = os.path.basename(file_path)
        try:
            blob_client = self.blob_service_client.get_blob_client(container=bucket_name, blob=object_name)
            with open(file_path, "rb") as data:
                start = time.perf_counter()
                blob_client.upload_blob(data, overwrite=True)
                return time.perf_counter() - start
        except Exception as e:
            print(f"❌ [Azure Upload Error]: {e}")
            return -1.0

    def download_file(self, bucket_name: str, object_name: str, file_path: str) -> float:
        try:
            blob_client = self.blob_service_client.get_blob_client(container=bucket_name, blob=object_name)
            with open(file_path, "wb") as data:
                start = time.perf_counter()
                data.write(blob_client.download_blob().readall())
                return time.perf_counter() - start
        except Exception as e:
            print(f"❌ [Azure Download Error]: {e}")
            return -1.0