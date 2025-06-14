# fastcms/storages/services.py

import hashlib
import mimetypes
from pathlib import Path
from typing import Any, Dict
from fastapi import UploadFile, HTTPException
from fastcms.storages.base import Storage
from PIL import Image
from io import BytesIO
from fastcms.storages.exceptions import StorageFileExistsError


class BaseStorageService:
    """Base class for storage services."""

    def __init__(self, storage: Storage):
        self.storage = storage

    @staticmethod
    def _guess_extension(file: UploadFile) -> str:
        ext = mimetypes.guess_extension(file.content_type)
        return ext.lstrip(".") if ext else "bin"

    @staticmethod
    def _is_image(mime_type: str | None) -> bool:
        return mime_type and mime_type.startswith("image/")

    @staticmethod
    def _extract_image_dimensions(content: bytes) -> tuple[int, int]:
        try:
            with Image.open(BytesIO(content)) as img:
                return img.width, img.height
        except Exception:
            return 0, 0

    async def save(self, file: UploadFile, folder: str = "") -> Dict[str, Any]:
        """Save a file and return its metadata."""
        content = await file.read()
        # MD5 hash to deduplicate files
        md5 = hashlib.md5(content).hexdigest()
        ext = Path(file.filename).suffix.lstrip(".") or self._guess_extension(file)
        filename = f"{md5}.{ext}"
        key = str(Path(folder) / filename) if folder else filename

        # Save to the storage backend
        try:
            await self.storage.save(key, content)
        except StorageFileExistsError:
            raise HTTPException(
                status_code=409,
                detail=f"File with key '{key}' already exists.",
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {str(e)}",
            )

        # Metadata for the file
        metadata: Dict[str, Any] = {
            "key": key,
            "title": Path(file.filename).stem,
            "size": len(content),
            "md5": md5,
            "mime_type": mimetypes.guess_type(file.filename)[0] or file.content_type,
        }

        # Optional: enrich metadata with image dimensions
        if self._is_image(metadata["mime_type"]):
            width, height = self._extract_image_dimensions(content)
            metadata.update({"width": width, "height": height})

        return metadata

    async def delete(self, key: str) -> None:
        try:
            await self.storage.delete(key)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="File not found")
