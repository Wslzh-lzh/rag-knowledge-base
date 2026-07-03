from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.core.config import settings


class StorageBackend(ABC):
    @abstractmethod
    def save(self, key: str, content: bytes) -> str: ...

    @abstractmethod
    def load(self, key: str) -> bytes: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def get_path(self, key: str) -> str: ...


class LocalStorageBackend(StorageBackend):
    def __init__(self, base_dir: str | Path | None = None) -> None:
        self.base_dir = Path(base_dir or settings.local_storage_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        return self.base_dir / key

    def save(self, key: str, content: bytes) -> str:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return str(path)

    def load(self, key: str) -> bytes:
        return self._resolve(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._resolve(key).exists()

    def delete(self, key: str) -> None:
        path = self._resolve(key)
        if path.exists():
            path.unlink()

    def get_path(self, key: str) -> str:
        return str(self._resolve(key))


class MinIOStorageBackend(StorageBackend):
    def __init__(self) -> None:
        try:
            from minio import Minio
        except ImportError as exc:
            raise RuntimeError("minio package not installed") from exc

        from urllib.parse import urlparse

        parsed = urlparse(settings.object_storage_url)
        self.client = Minio(
            parsed.netloc,
            access_key=settings.object_storage_access_key,
            secret_key=settings.object_storage_secret_key,
            secure=parsed.scheme == "https",
        )
        self.bucket = settings.object_storage_bucket
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def save(self, key: str, content: bytes) -> str:
        import io

        self.client.put_object(
            self.bucket,
            key,
            io.BytesIO(content),
            length=len(content),
        )
        return f"s3://{self.bucket}/{key}"

    def load(self, key: str) -> bytes:
        response = self.client.get_object(self.bucket, key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def exists(self, key: str) -> bool:
        try:
            self.client.stat_object(self.bucket, key)
            return True
        except Exception:
            return False

    def delete(self, key: str) -> None:
        self.client.remove_object(self.bucket, key)

    def get_path(self, key: str) -> str:
        return f"s3://{self.bucket}/{key}"


def get_storage_backend() -> StorageBackend:
    if settings.storage_backend == "minio":
        return MinIOStorageBackend()
    return LocalStorageBackend()


def get_storage_dir() -> Path:
    path = Path(settings.local_storage_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_document_key(sha256: str, file_name: str | None) -> str:
    suffix = ""
    if file_name and "." in file_name:
        suffix = "." + file_name.rsplit(".", 1)[-1].lower()
    prefix = sha256[:2]
    return f"documents/{prefix}/{sha256}{suffix}"


def build_document_path(sha256: str, file_name: str | None) -> Path:
    suffix = ""
    if file_name and "." in file_name:
        suffix = "." + file_name.rsplit(".", 1)[-1].lower()
    return get_storage_dir() / f"{sha256}{suffix}"

