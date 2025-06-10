# fastcms/services/db.py

from enum import StrEnum
from typing import TypeVar, Type, Generic, Any, Sequence
from sqlalchemy.sql import Select
from sqlmodel import SQLModel, select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from fastcms.utils.time import current_time
from fastcms.utils.db import parse_filters


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

    # Handle soft delete
    def _soft_delete_clause(self) -> Any:
        """Builds a SQLAlchemy filter expression that enforces the soft delete awareness of the model."""
        if self.delete_mode == DeleteMode.SOFT and hasattr(self.model, "is_deleted"):
            # this creates an SQL clause equivalent to: "WHERE is_deleted = FALSE"
            return not getattr(self.model, "is_deleted")
        from sqlalchemy import true

        return true()

    def _filter_clause(self, **kwargs):
        if not kwargs:
            from sqlalchemy import true

            return true()
        valid_fields = set(self.model.model_fields.keys())
        fields_dict = {}
        for k, v in kwargs.items():
            filed = k.split("__", 1)[0]
            if filed not in valid_fields:
                raise ValueError(
                    f"Invalid field '{filed}' for model '{self.model.__name__}'"
                )
            fields_dict[k] = v
        return parse_filters(self.model, fields_dict)

    async def filter(
        self, limit: int = 100, offset: int = 0, order_by: str | None = None, **kwargs
    ) -> Sequence[T]:
        """Filter instances based on provided filters, limit, offset, and order."""

        stmt: Select = select(self.model)
        if kwargs:
            filter_clause = self._filter_clause(**kwargs)
            stmt = stmt.where(filter_clause)

        # Apply soft delete clause if applicable
        soft_delete_clause = self._soft_delete_clause()
        stmt = stmt.where(soft_delete_clause)

        # Apply ordering if specified
        if order_by:
            descending = order_by.startswith("-")
            field_name = order_by.lstrip("-")
            column = getattr(self.model, field_name, None)
            if column is not None:
                stmt = stmt.order_by(column.desc() if descending else column.asc())

        # Apply limit and offset
        stmt = stmt.limit(limit).offset(offset)
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

    async def one(self, pk: str | None = None, **kwargs) -> T | None:
        """Retrieve a single instance by filters.
        If pk is provided, it will be used to filter the instance.
        Or can be more implicit such as `one(id=pk)` or `one(slug=slug)`.
        """
        filter_clause = self._filter_clause(**kwargs)
        if pk:
            filter_clause = filter_clause & (self.model.id == pk)
        stmt: Select = select(self.model).where(filter_clause)
        result = await self.session.exec(stmt)
        return result.one_or_none()

    async def all(self, **kwargs) -> Sequence[T] | None:
        """Retrieve all instances with optional filters."""
        filter_clause = self._filter_clause(**kwargs)
        stmt: Select = select(self.model).where(filter_clause)
        result = await self.session.exec(stmt)
        return result.all()

    async def dict_to_instance(self, data: dict[str, Any]) -> T:
        """Convert a dictionary to an instance of the model."""
        return self.model(**data)

    async def _create(self, instance: T) -> T:
        """Create a new instance."""
        if self.delete_mode == DeleteMode.SOFT and hasattr(instance, "is_deleted"):
            instance.is_deleted = False
        # If the model has a created_at field, set it to the current time
        if hasattr(instance, "created_at"):
            instance.created_at = current_time()

        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def create(self, data: dict[str, Any]) -> T:
        """Create a new instance from a dictionary."""
        instance = await self.dict_to_instance(data)
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

    async def delete(self, instance: T) -> None:
        """Delete an instance."""
        if self.delete_mode == DeleteMode.SOFT:
            if hasattr(instance, "is_deleted"):
                instance.is_deleted = True
            if hasattr(instance, "deleted_at"):
                instance.deleted_at = current_time()
            self.session.add(instance)
        else:
            await self.session.delete(instance)

        await self.session.commit()
