# fastcms/utils/file.py
import hashlib
import mimetypes
from fastapi import UploadFile
from PIL import Image
from io import BytesIO


async def read_upload_file(file: UploadFile) -> bytes:
    """Read the content of an UploadFile."""
    return await file.read()


def guess_extension(file: UploadFile) -> str:
    """Guess the file extension based on its content type."""
    ext = mimetypes.guess_extension(file.content_type)
    return ext.lstrip(".") if ext else "bin"


def compute_md5(content: bytes) -> str:
    """Compute the MD5 hash of the file content."""
    return hashlib.md5(content).hexdigest()


def is_image(mime_type: str | None) -> bool:
    """Check if the MIME type indicates an image."""
    return mime_type is not None and mime_type.startswith("image/")


def extract_image_dimensions(content: bytes) -> tuple[int, int]:
    try:
        with Image.open(BytesIO(content)) as img:
            return img.width, img.height
    except Exception:
        return 0, 0


def generate_md5_filename(md5: str, ext: str) -> str:
    """Generate a filename based on MD5 hash and extension."""
    return f"{md5}.{ext}"


def get_mimetype(file: UploadFile) -> str:
    """Get the MIME type of the file."""
    return (
        file.content_type
        or mimetypes.guess_type(file.filename)[0]
        or "application/octet-stream"
    )


def get_file_size(file: UploadFile) -> int:
    """Get the size of the file in bytes."""
    return (
        file.spool_max_size
        if hasattr(file, "spool_max_size")
        else len(file.file.read())
    )
