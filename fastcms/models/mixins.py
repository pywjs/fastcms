# fastcms/models/mixins.py
from sqlmodel import Field, DateTime
from datetime import datetime
from fastcms.utils import current_time
from ulid import ULID

"""
A collection of mixins for SQLModel models in FastCMS.

A mixin is a class that:

- Is not mean to stand on its own
- Adds specific behavior or fields (methods, properties, etc.) to a base model or another mixin
- Is used via multiple inheritance to extend the functionality of a base model
"""


class ULIDPrimaryKeyMixin:
    """Mixin for models with ULID primary keys.
    Fields:
        - id: ULID primary key, stored as a string (CHAR(26)) in the database
    """

    # Stores ULID as a string (CHAR(26)) in the database
    id: str | None = Field(default_factory=lambda: str(ULID()), primary_key=True)


"""
Note: without `type: ignore` PyCharm will complain about the type of `created_at` and `updated_at` fields:
`Expected type 'type | PydanticUndefinedType', got 'DateTime' instead`
"""


class TimeStampMixin:
    """Mixin for models with created_at and updated_at timestamps.
    Fields:
        - created_at: datetime when the record was created
        - updated_at: datetime when the record was last updated
    """

    created_at: datetime = Field(
        default_factory=current_time,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime = Field(
        default_factory=current_time,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class PublishableMixin:
    """Mixin for models with publishable fields.
    Fields:
        - is_published: boolean flag for published content
        - published_at: datetime when the record was published
        - unpublished_at: datetime when the record was unpublished
    """

    is_published: bool = Field(default=False)
    published_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))  # type: ignore
    unpublished_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class SlugMixin:
    """Mixin for models with slug fields.
    Fields:
        - slug: string unique slug for the model
    """

    slug: str = Field(index=True, unique=True)  # Unique slug for the model


class SoftDeleteMixin:
    """Mixin for models with soft delete fields.
    Fields:
        - is_deleted: boolean flag for soft delete
        - deleted_at: datetime when the record was softly deleted
    """

    is_deleted: bool = Field(default=False, index=True)  # Soft delete flag
    deleted_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))  # type: ignore


class CommonFieldsMixin(ULIDPrimaryKeyMixin, TimeStampMixin, SoftDeleteMixin):
    """Mixin for common table fields.
    Fields:
        - id: primary key (ULID)
        - created_at: datetime when the record was created
        - updated_at: datetime when the record was last updated
        - is_deleted: boolean flag for soft delete
        - deleted_at: datetime when the record was softly deleted
    """

    pass
