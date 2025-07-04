# fastcms/storages/s3.py

import aioboto3
from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict
import mimetypes
from fastcms.storages.base import Storage
from fastcms.storages.exceptions import StorageFileNotExistError, StorageFileExistsError
from io import BytesIO
from posixpath import normpath
from fastcms.utils.logging import get_logger


logger = get_logger(__name__)


class S3Settings(BaseModel):
    """Settings for S3 storage."""

    model_config = ConfigDict(extra="allow")
    access_key: str
    secret_key: str
    bucket_name: str
    region_name: str | None = None
    endpoint_url: str | None = None


class S3Storage(Storage):
    name = "s3"

    def __init__(
        self, settings: S3Settings, public: bool = False, prefix: str | None = None
    ):
        self.public = public
        if prefix is not None:
            self.prefix = prefix.rstrip("/")
        else:
            self.prefix = "public" if public else "private"
        self.settings = settings
        self.s3_client_kwargs = {
            "service_name": "s3",
            "aws_access_key_id": self.settings.access_key,
            "aws_secret_access_key": self.settings.secret_key,
            "endpoint_url": self.settings.endpoint_url,
        }
        if self.settings.region_name:
            self.s3_client_kwargs["region_name"] = self.settings.region_name

        # session
        self.session = aioboto3.Session()

    async def _full_key(self, name: str) -> str:
        """Construct the full key for the S3 object."""
        # strip leading slashes from name just in case
        name = name.lstrip("/")
        full_key = normpath(f"{self.prefix}/{name}") if self.prefix else normpath(name)
        return full_key

    async def save(
        self, name: str, content: bytes | UploadFile, overwrite: bool = False
    ) -> str:
        """Save a file and return its name/path."""
        _extra_args = {"ACL": "public-read"} if self.public else {}
        content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
        # strip leading slashes from name just in case
        full_key = await self._full_key(name)
        if not overwrite and await self.exists(name):
            logger.info(f"File '{name}' already exists, skipping upload.")
            raise StorageFileExistsError(f"File '{name}' already exists.")
        # If content is an UploadFile, read its content
        if isinstance(content, UploadFile):
            body = content.file
        elif isinstance(content, bytes):
            body = BytesIO(content)
        else:
            logger.warning(
                f"unknown content is passed to S3Storage.save: {type(content)}"
            )
            raise ValueError("Content must be bytes or an UploadFile instance.")
        async with self.session.client(**self.s3_client_kwargs) as s3:
            await s3.upload_fileobj(
                Fileobj=body,
                Bucket=self.settings.bucket_name,
                Key=full_key,
                ExtraArgs={"ContentType": content_type, **_extra_args},
            )
        return full_key

    async def delete(self, name: str) -> None:
        """Delete a file by its name."""
        async with self.session.client(**self.s3_client_kwargs) as s3:
            try:
                key = await self._full_key(name)
                await s3.delete_object(Bucket=self.settings.bucket_name, Key=key)
            except s3.exceptions.NoSuchKey:
                raise StorageFileNotExistError(f"File '{name}' does not exist.")

    async def exists(self, name: str) -> bool:
        """Check if a file exists by its name."""
        async with self.session.client(**self.s3_client_kwargs) as s3:
            try:
                key = await self._full_key(name)
                print(
                    f"Checking existence of {key} in bucket {self.settings.bucket_name}"
                )
                await s3.head_object(Bucket=self.settings.bucket_name, Key=key)
                return True
            except s3.exceptions.ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    return False
                raise

    async def url(self, name: str) -> str:
        """Return a URL of a file."""
        key = await self._full_key(name)
        return f"{self.settings.endpoint_url}/{self.settings.bucket_name}/{key}"

    async def signed_url(self, name: str, expires_seconds: int = 3600) -> str:
        """Return a signed temporary URL."""
        key = await self._full_key(name)
        async with self.session.client(**self.s3_client_kwargs) as s3:
            return await s3.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self.settings.bucket_name, "Key": key},
                ExpiresIn=expires_seconds,
            )

    async def size(self, name: str) -> int:
        """Return the size of the file in bytes."""
        key = await self._full_key(name)
        async with self.session.client(**self.s3_client_kwargs) as s3:
            try:
                response = await s3.head_object(
                    Bucket=self.settings.bucket_name, Key=key
                )
                return response["ContentLength"]
            except s3.exceptions.ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    raise StorageFileNotExistError(f"File '{name}' does not exist.")
                raise
