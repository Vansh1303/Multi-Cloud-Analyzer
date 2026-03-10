import os
import time
from pathlib import Path
from google.cloud import storage as gcs_storage
from providers.base import (
    StorageProvider, UploadResult, DownloadResult,
    DeleteResult, ListResult, MetadataResult,
)

GCS_KEY_PATH = Path(__file__).parent.parent / "gcp-key.json"


class GCPStorage(StorageProvider):
    name = "GCP"

    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        key_path = os.getenv("GCP_KEY_PATH", str(GCS_KEY_PATH))
        if os.path.exists(key_path):
            self.client = gcs_storage.Client.from_service_account_json(
                key_path, project=self.project_id
            )
        else:
            self.client = gcs_storage.Client(project=self.project_id)

    def upload_file(self, file_path, bucket, object_name) -> UploadResult:
        try:
            bkt = self.client.bucket(bucket)
            blob = bkt.blob(object_name)
            start = time.perf_counter()
            blob.upload_from_filename(file_path)
            elapsed = time.perf_counter() - start
            url = f"https://storage.googleapis.com/{bucket}/{object_name}"
            return UploadResult(elapsed=elapsed, url=url)
        except Exception as e:
            print(f"  [GCP Upload Error]: {e}")
            return UploadResult(elapsed=-1.0, url=None)

    def download_file(self, bucket, object_name, file_path) -> DownloadResult:
        try:
            bkt = self.client.bucket(bucket)
            blob = bkt.blob(object_name)
            start = time.perf_counter()
            blob.download_to_filename(file_path)
            elapsed = time.perf_counter() - start
            return DownloadResult(elapsed=elapsed)
        except Exception as e:
            print(f"  [GCP Download Error]: {e}")
            return DownloadResult(elapsed=-1.0)

    def delete_file(self, bucket, object_name) -> DeleteResult:
        try:
            bkt = self.client.bucket(bucket)
            blob = bkt.blob(object_name)
            start = time.perf_counter()
            blob.delete()
            elapsed = time.perf_counter() - start
            return DeleteResult(elapsed=elapsed)
        except Exception as e:
            print(f"  [GCP Delete Error]: {e}")
            return DeleteResult(elapsed=-1.0)

    def list_objects(self, bucket, prefix="") -> ListResult:
        try:
            bkt = self.client.bucket(bucket)
            start = time.perf_counter()
            blobs = list(bkt.list_blobs(prefix=prefix or None))
            elapsed = time.perf_counter() - start
            return ListResult(elapsed=elapsed, object_count=len(blobs))
        except Exception as e:
            print(f"  [GCP List Error]: {e}")
            return ListResult(elapsed=-1.0, object_count=0)

    def get_metadata(self, bucket, object_name) -> MetadataResult:
        try:
            bkt = self.client.bucket(bucket)
            blob = bkt.blob(object_name)
            start = time.perf_counter()
            blob.reload()   # fetches metadata from server (HEAD request)
            elapsed = time.perf_counter() - start
            meta = {
                "size_bytes": blob.size,
                "content_type": blob.content_type,
                "etag": blob.etag,
                "last_modified": str(blob.updated),
            }
            return MetadataResult(elapsed=elapsed, metadata=meta)
        except Exception as e:
            print(f"  [GCP Metadata Error]: {e}")
            return MetadataResult(elapsed=-1.0, metadata={})
