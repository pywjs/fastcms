# fastcms/models/base.py
from sqlmodel import SQLModel
from pydantic import ConfigDict

try:
    from ulid import ULID
except ImportError:
    ULID = None


class _BaseModel(SQLModel):
    """Base for non-table models and shared configuration."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,  # Allow arbitrary types like ULID
        use_enum_values=True,  # Use enum values instead of enum instances
        json_encoders={ULID: str} if ULID else {},  # Encode ULID as string
    )
