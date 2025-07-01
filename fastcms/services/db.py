# fastcms/services/db.py

from enum import StrEnum
from typing import TypeVar, Type, Generic, Any, Sequence

from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select
from sqlmodel import SQLModel, select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from fastcms.utils.time import current_time
from fastcms.utils.db import parse_filters
from sqlalchemy.inspection import inspect
from sqlalchemy.exc import IntegrityError
from fastcms.services.exceptions import DBServiceIntegrityError
from fastcms.utils.db import parse_table_field_from_error_msg

T = TypeVar("T", bound=SQLModel)


class DeleteMode(StrEnum):
    SOFT = "soft"
    HARD = "hard"


class BaseDBService(Generic[T]):
    def __init__(
        self,
        model: Type[T],
        session: AsyncSession,
        delete_mode: DeleteMode = DeleteMode.SOFT,
    ):
        self.session = session
        self.model = model
        self.delete_mode = delete_mode

        # Computed properties for the model
        self.model_mapper = inspect(model)
        self.model_columns = {col.key for col in self.model_mapper.columns}
        self.model_relationships = {
            rel.key: rel for rel in self.model_mapper.relationships
        }
        self.model_fields = set(self.model.model_fields.keys())

    # Handle soft delete
    def _soft_delete_clause(self) -> Any:
        """Builds a SQLAlchemy filter expression that enforces the soft delete awareness of the model."""
        from sqlalchemy import true, false

        if self.delete_mode == DeleteMode.SOFT and hasattr(self.model, "is_deleted"):
            # this creates an SQL clause equivalent to: "WHERE is_deleted = FALSE"
            return getattr(self.model, "is_deleted") == false()
        return true()

    def _filter_clause(self, **kwargs):
        if not kwargs:
            from sqlalchemy import true

            return true()
        fields_dict = {}
        for k, v in kwargs.items():
            filed = k.split("__", 1)[0]
            if filed not in self.model_fields:
                raise ValueError(
                    f"Invalid field '{filed}' for model '{self.model.__name__}'"
                )
            fields_dict[k] = v
        return parse_filters(self.model, fields_dict)

    def _prefetch_clause(
        self, stmt: Select, prefetch_fields: Sequence[str] | None = None
    ) -> Select:
        """Prefetch related models to avoid N+1 queries."""
        if prefetch_fields is not None:
            for rel in prefetch_fields:
                if rel in self.model_relationships:
                    stmt = stmt.options(selectinload(getattr(self.model, rel)))
                else:
                    raise ValueError(
                        f"Invalid prefetch field '{rel}' for model '{self.model.__name__}'"
                    )
        return stmt

    async def filter(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: str | None = None,
        prefetch_fields: list[str] | None = None,
        **kwargs,
    ) -> Sequence[T]:
        """Filter instances based on provided filters, limit, offset, and order."""

        stmt: Select = select(self.model)
        if kwargs:
            filter_clause = self._filter_clause(**kwargs)
            stmt = stmt.where(filter_clause)

        # Apply soft delete clause if applicable
        stmt = stmt.where(self._soft_delete_clause())

        # Apply ordering if specified
        if order_by:
            descending = order_by.startswith("-")
            field_name = order_by.lstrip("-")
            column = getattr(self.model, field_name, None)
            if column is not None:
                stmt = stmt.order_by(column.desc() if descending else column.asc())

        # Apply limit and offset
        stmt = stmt.limit(limit).offset(offset)
        # Run the prefetch clause if prefetch_fields are provided
        stmt = self._prefetch_clause(stmt, prefetch_fields)
        # Execute the statement
        result = await self.session.exec(stmt)
        return result.all()

    async def count(self, stmt: Select | None = None) -> int:
        """Count the number of instances matching the provided statement."""
        if stmt is None:
            stmt = select(func.count()).select_from(self.model)

        # Apply soft delete clause if applicable
        soft_delete_clause = self._soft_delete_clause()
        stmt = stmt.where(soft_delete_clause)

        result = await self.session.exec(stmt)
        return result.scalar_one() if result else 0

    async def get(self, pk: str) -> T | None:
        """Retrieve a single instance by primary key.
        This method is used to get an instance by its primary key, it does not apply any filters,
        meaning it will return the instance regardless of its state (deleted or not).
        Should be used with caution, especially in soft delete scenarios,
        for example, when you want to retrieve an instance that has been soft-deleted.
        """
        return await self.session.get(self.model, pk)

    async def one(
        self, pk: str | None = None, prefetch_fields: list[str] | None = None, **kwargs
    ) -> T | None:
        """Retrieve a single instance by filters.
        If pk is provided, it will be used to filter the instance.
        Or can be more implicit such as `one(id=pk)` or `one(slug=slug)`.
        """
        # TODO: when using `one`, it should raise an exception if more than one instance is found.
        filter_clause = self._filter_clause(**kwargs)
        if pk:
            filter_clause = filter_clause & (self.model.id == pk)  # noqa
        stmt: Select = select(self.model).where(filter_clause)
        stmt = self._prefetch_clause(stmt, prefetch_fields)
        stmt = stmt.where(self._soft_delete_clause())

        result = await self.session.exec(stmt)
        return result.one_or_none()

    async def one_by_stmt(self, stmt: Select) -> T | None:
        """Retrieve a single instance by a custom SQLAlchemy statement."""
        # Apply soft delete clause if applicable
        soft_delete_clause = self._soft_delete_clause()
        stmt = stmt.where(soft_delete_clause)

        result = await self.session.exec(stmt)
        return result.one_or_none()

    async def one_by_slug(self, slug: str) -> T | None:
        """Retrieve a single instance by slug."""
        if not hasattr(self.model, "slug"):
            raise ValueError(f"{self.model.__name__} does not have a slug field.")

        return await self.one(slug=slug)

    async def all(
        self, prefetch_fields: list[str] | None = None, **kwargs
    ) -> Sequence[T] | None:
        """Retrieve all instances with optional filters."""
        filter_clause = self._filter_clause(**kwargs)
        stmt: Select = select(self.model).where(filter_clause)

        # Apply soft delete clause if applicable
        soft_delete_clause = self._soft_delete_clause()
        stmt = stmt.where(soft_delete_clause)

        stmt = self._prefetch_clause(stmt, prefetch_fields)

        result = await self.session.exec(stmt)
        return result.all()

    async def all_by_stmt(self, stmt: Select) -> Sequence[T] | None:
        """Retrieve all instances by a custom SQLAlchemy statement."""
        # Apply soft delete clause if applicable
        soft_delete_clause = self._soft_delete_clause()
        stmt = stmt.where(soft_delete_clause)

        result = await self.session.exec(stmt)
        return result.all()

    async def _build_instance_from_data(self, data: dict[str, Any]) -> T:
        """Recursively convert a dict with nested relations into a SQLModel instance."""
        instance_data = {}

        for key, value in data.items():
            if key in self.model_columns:
                instance_data[key] = value
            elif key in self.model_relationships:
                related_model = self.model_relationships[key].mapper.class_
                if isinstance(value, list):
                    instance_data[key] = [
                        related_model(**v) if isinstance(v, dict) else v for v in value
                    ]
                elif isinstance(value, dict):
                    instance_data[key] = related_model(**value)
                else:
                    instance_data[key] = value
        return self.model(**instance_data)

    async def _create(self, instance: T) -> T:
        """Create a new instance."""
        if self.delete_mode == DeleteMode.SOFT and hasattr(instance, "is_deleted"):
            instance.is_deleted = False
        # If the model has a created_at field, set it to the current time
        if hasattr(instance, "created_at"):
            instance.created_at = current_time()

        try:
            self.session.add(instance)
            await self.session.commit()
            await self.session.refresh(instance)
        except IntegrityError as e:
            await self.session.rollback()
            orig_msg = str(e.orig) if hasattr(e, "orig") else str(e)
            field = parse_table_field_from_error_msg(orig_msg)
            if field:
                raise DBServiceIntegrityError(
                    f"{field.capitalize()} already exists.", field=field
                )
            else:
                raise DBServiceIntegrityError(f"Integrity error: {orig_msg}") from e
        return instance

    async def create(self, data: dict[str, Any]) -> T:
        """Create a new instance from a dictionary, supporting nested relationships."""
        instance = await self._build_instance_from_data(data)
        return await self._create(instance)

    async def update(self, instance: T, data: dict[str, Any]) -> T:
        """Update an existing instance. [PARTIAL UPDATE]"""
        for key, value in data.items():
            setattr(instance, key, value)

        # Update the updated_at field if it exists
        if hasattr(instance, "updated_at"):
            instance.updated_at = current_time()

        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: T, force: bool = False) -> None:
        """Delete an instance. If force=True, perform hard delete even if SOFT mode."""
        if force or self.delete_mode == DeleteMode.HARD:
            await self.session.delete(instance)
        elif self.delete_mode == DeleteMode.SOFT:
            if hasattr(instance, "is_deleted"):
                instance.is_deleted = True
            if hasattr(instance, "deleted_at"):
                instance.deleted_at = current_time()
            self.session.add(instance)
        await self.session.commit()
