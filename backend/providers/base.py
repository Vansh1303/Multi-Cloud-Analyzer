import abc
from dataclasses import dataclass
from typing import Optional, Dict, Any, List


@dataclass
class UploadResult:
    """Result of an upload operation."""
    elapsed: float          # seconds (-1.0 on failure)
    url: Optional[str]      # public/signed URL of uploaded object


@dataclass
class DownloadResult:
    """Result of a download operation."""
    elapsed: float


@dataclass
class DeleteResult:
    """Result of a delete operation."""
    elapsed: float


@dataclass
class ListResult:
    """Result of a list-objects operation."""
    elapsed: float
    object_count: int


@dataclass
class MetadataResult:
    """Result of a get-metadata / head-object operation."""
    elapsed: float
    metadata: Dict[str, Any]    # size, content_type, etag, last_modified, etc.


class StorageProvider(abc.ABC):
    """Base class for all cloud storage providers."""

    name: str = "Unknown"

    @abc.abstractmethod
    def upload_file(self, file_path: str, bucket: str, object_name: str) -> UploadResult:
        ...

    @abc.abstractmethod
    def download_file(self, bucket: str, object_name: str, file_path: str) -> DownloadResult:
        ...

    @abc.abstractmethod
    def delete_file(self, bucket: str, object_name: str) -> DeleteResult:
        ...

    @abc.abstractmethod
    def list_objects(self, bucket: str, prefix: str = "") -> ListResult:
        ...

    @abc.abstractmethod
    def get_metadata(self, bucket: str, object_name: str) -> MetadataResult:
        ...
