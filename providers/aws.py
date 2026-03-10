import os
import time
import boto3
from providers.base import (
    StorageProvider, UploadResult, DownloadResult,
    DeleteResult, ListResult, MetadataResult,
)


class AWSStorage(StorageProvider):
    name = "AWS"

    def __init__(self):
        self.region = os.getenv("AWS_REGION", "ap-southeast-1")
        self.s3_client = boto3.client(
            "s3",
            region_name=self.region,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )

    def upload_file(self, file_path, bucket, object_name) -> UploadResult:
        try:
            start = time.perf_counter()
            self.s3_client.upload_file(file_path, bucket, object_name)
            elapsed = time.perf_counter() - start
            url = f"https://{bucket}.s3.{self.region}.amazonaws.com/{object_name}"
            return UploadResult(elapsed=elapsed, url=url)
        except Exception as e:
            print(f"  [AWS Upload Error]: {e}")
            return UploadResult(elapsed=-1.0, url=None)

    def download_file(self, bucket, object_name, file_path) -> DownloadResult:
        try:
            start = time.perf_counter()
            self.s3_client.download_file(bucket, object_name, file_path)
            return DownloadResult(elapsed=time.perf_counter() - start)
        except Exception as e:
            print(f"  [AWS Download Error]: {e}")
            return DownloadResult(elapsed=-1.0)

    def delete_file(self, bucket, object_name) -> DeleteResult:
        try:
            start = time.perf_counter()
            self.s3_client.delete_object(Bucket=bucket, Key=object_name)
            return DeleteResult(elapsed=time.perf_counter() - start)
        except Exception as e:
            print(f"  [AWS Delete Error]: {e}")
            return DeleteResult(elapsed=-1.0)

    def list_objects(self, bucket, prefix="") -> ListResult:
        try:
            start = time.perf_counter()
            response = self.s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
            elapsed = time.perf_counter() - start
            count = response.get("KeyCount", 0)
            return ListResult(elapsed=elapsed, object_count=count)
        except Exception as e:
            print(f"  [AWS List Error]: {e}")
            return ListResult(elapsed=-1.0, object_count=0)

    def get_metadata(self, bucket, object_name) -> MetadataResult:
        try:
            start = time.perf_counter()
            resp = self.s3_client.head_object(Bucket=bucket, Key=object_name)
            elapsed = time.perf_counter() - start
            meta = {
                "size_bytes": resp.get("ContentLength"),
                "content_type": resp.get("ContentType"),
                "etag": resp.get("ETag"),
                "last_modified": str(resp.get("LastModified", "")),
            }
            return MetadataResult(elapsed=elapsed, metadata=meta)
        except Exception as e:
            print(f"  [AWS Metadata Error]: {e}")
            return MetadataResult(elapsed=-1.0, metadata={})
