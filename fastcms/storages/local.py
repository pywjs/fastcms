# fastcms/storages/local.py

from pathlib import Path
from fastcms.storages.base import Storage
from typing import Union
import aiofiles


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

    async def save(self, name: str | Path, content: bytes) -> str:
        """Save a file and return its name/path."""
        file_path = self._resolve_path(name)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        # Write the content to the file asynchronously
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        return str(file_path)

    async def delete(self, name: str | Path) -> None:
        """Delete a file by its name or path."""
        file_path = self._resolve_path(str(name))
        if file_path.exists():
            file_path.unlink()
