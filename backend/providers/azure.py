import os
import time
from azure.storage.blob import BlobServiceClient
from providers.base import (
    StorageProvider, UploadResult, DownloadResult,
    DeleteResult, ListResult, MetadataResult,
)


class AzureStorage(StorageProvider):
    name = "Azure"

    def __init__(self):
        self.conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.blob_service_client = BlobServiceClient.from_connection_string(self.conn_str)

    def _blob_client(self, container, blob_name):
        return self.blob_service_client.get_blob_client(container=container, blob=blob_name)

    def upload_file(self, file_path, bucket, object_name) -> UploadResult:
        try:
            blob_client = self._blob_client(bucket, object_name)
            with open(file_path, "rb") as data:
                start = time.perf_counter()
                blob_client.upload_blob(data, overwrite=True)
                elapsed = time.perf_counter() - start
            url = blob_client.url
            return UploadResult(elapsed=elapsed, url=url)
        except Exception as e:
            print(f"  [Azure Upload Error]: {e}")
            return UploadResult(elapsed=-1.0, url=None)

    def download_file(self, bucket, object_name, file_path) -> DownloadResult:
        try:
            blob_client = self._blob_client(bucket, object_name)
            with open(file_path, "wb") as data:
                start = time.perf_counter()
                data.write(blob_client.download_blob().readall())
                elapsed = time.perf_counter() - start
            return DownloadResult(elapsed=elapsed)
        except Exception as e:
            print(f"  [Azure Download Error]: {e}")
            return DownloadResult(elapsed=-1.0)

    def delete_file(self, bucket, object_name) -> DeleteResult:
        try:
            blob_client = self._blob_client(bucket, object_name)
            start = time.perf_counter()
            blob_client.delete_blob()
            elapsed = time.perf_counter() - start
            return DeleteResult(elapsed=elapsed)
        except Exception as e:
            print(f"  [Azure Delete Error]: {e}")
            return DeleteResult(elapsed=-1.0)

    def list_objects(self, bucket, prefix="") -> ListResult:
        try:
            container_client = self.blob_service_client.get_container_client(bucket)
            start = time.perf_counter()
            blobs = list(container_client.list_blobs(name_starts_with=prefix or None))
            elapsed = time.perf_counter() - start
            return ListResult(elapsed=elapsed, object_count=len(blobs))
        except Exception as e:
            print(f"  [Azure List Error]: {e}")
            return ListResult(elapsed=-1.0, object_count=0)

    def get_metadata(self, bucket, object_name) -> MetadataResult:
        try:
            blob_client = self._blob_client(bucket, object_name)
            start = time.perf_counter()
            props = blob_client.get_blob_properties()
            elapsed = time.perf_counter() - start
            meta = {
                "size_bytes": props.size,
                "content_type": props.content_settings.content_type,
                "etag": props.etag,
                "last_modified": str(props.last_modified),
            }
            return MetadataResult(elapsed=elapsed, metadata=meta)
        except Exception as e:
            print(f"  [Azure Metadata Error]: {e}")
            return MetadataResult(elapsed=-1.0, metadata={})
