from __future__ import annotations

import logging
from pathlib import Path

from minio import Minio

from app.core.config import Settings

logger = logging.getLogger(__name__)


class StorageService:
    _client: Minio | None = None
    _bucket: str = "ai-life-companion"

    @classmethod
    def configure(cls, settings: Settings) -> None:
        if cls._client:
            return
        try:
            cls._client = Minio(
                settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=False,
            )
            cls._bucket = settings.minio_bucket
            if not cls._client.bucket_exists(cls._bucket):
                cls._client.make_bucket(cls._bucket)
        except Exception as exc:  # pragma: no cover
            logger.warning("Minio unavailable (%s); falling back to local storage", exc)
            cls._client = None
            cls._bucket = settings.minio_bucket

    @classmethod
    def upload_file(cls, file_path: Path, object_name: str) -> str:
        if cls._client is None:
            local_path = Path("data/local") / object_name
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(file_path.read_bytes())
            return str(local_path)
        cls._client.fput_object(cls._bucket, object_name, str(file_path))
        logger.info("Uploaded %s to bucket %s", object_name, cls._bucket)
        return f"{cls._bucket}/{object_name}"

    @classmethod
    async def download_file(cls, storage_path: str, local_path: Path) -> Path:
        """Download file from storage to local path."""
        if cls._client is None:
            # Already local storage
            existing_path = Path(storage_path)
            if existing_path.exists():
                return existing_path
            raise FileNotFoundError(f"File not found: {storage_path}")
        
        # Download from Minio
        local_path.parent.mkdir(parents=True, exist_ok=True)
        if "/" in storage_path:
            bucket, object_name = storage_path.split("/", 1)
        else:
            bucket = cls._bucket
            object_name = storage_path
        cls._client.fget_object(bucket, object_name, str(local_path))
        logger.info("Downloaded %s to %s", storage_path, local_path)
        return local_path

