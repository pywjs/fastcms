from typing import Protocol, runtime_checkable
from pathlib import Path


@runtime_checkable
class Storage(Protocol):
    """Protocol for pluggable storage backends."""

    name: str

    async def save(self, name: str, content: bytes, overwrite: bool = False) -> str:
        """Save a file and return its name/path."""
        ...

    async def delete(self, name: str | Path) -> None:
        """Delete a file by its name or path."""
        ...

    async def exists(self, name: str) -> bool:
        """Check if a file exists by its name."""
        ...

    async def url(self, name: str) -> str:
        """Return public URL of a file."""
        ...

    async def signed_url(self, name: str, expires_seconds: int = 3600) -> str:
        """
        Return a signed temporary URL.
        Fallback to `url()` if not supported.
        """
        ...

    async def size(self, name: str) -> int:
        """Return the size of the file in bytes."""
        ...
