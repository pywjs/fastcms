# fastcms/storages/local.py
import urllib
from pathlib import Path
from fastcms.storages.base import Storage
from typing import Union
import aiofiles

from fastcms.storages.exceptions import (
    StorageFileNotExistError,
)


class LocalStorage(Storage):
    name: str = "local"

    def __init__(self, base_path: Union[str, Path], base_url: str = "/media/"):
        """Initialize the LocalStorage with a base path and optional base URL."""
        self.base_path = Path(base_path).resolve()
        self.base_url = base_url.rstrip("/") + "/"
        # Ensure the base path exists
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, name: str | Path) -> Path:
        return self.base_path / name

    async def save(
        self, name: str | Path, content: bytes, overwrite: bool = False
    ) -> str:
        """Save a file and return its name/path."""
        file_path = self._resolve_path(name)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        # Write the content to the file asynchronously
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        return str(file_path.relative_to(self.base_path))

    async def delete(self, name: str | Path) -> None:
        """Delete a file by its name or path."""
        file_path = self._resolve_path(str(name))
        if file_path.exists():
            file_path.unlink()
        else:
            raise StorageFileNotExistError

    async def exists(self, name: str | Path) -> bool:
        """Check if a file exists by its name."""
        file_path = self._resolve_path(str(name))
        return file_path.exists()

    async def url(self, name: str | Path) -> str:
        """Return a URL of a file."""
        return urllib.parse.urljoin(self.base_url, str(name))

    async def signed_url(self, name: str | Path, expires_seconds: int = 3600) -> str:
        """For local storage, we can return the URL directly as signed URLs are not applicable."""
        return await self.url(name)

    async def size(self, name: str | Path) -> int:
        """Return the size of the file in bytes."""
        file_path = self._resolve_path(str(name))
        if not file_path.exists():
            raise StorageFileNotExistError(f"File '{name}' does not exist.")
        return file_path.stat().st_size
