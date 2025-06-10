# fastcms/schemas/db.py

from typing import Type, Any, TypeVar
from sqlmodel import SQLModel
from pydantic import create_model

T = TypeVar("T", bound=SQLModel)


class BaseDBSchema:
    """Base schema generator for an SQLModel model."""

    def __init__(self, model: Type[T], name: str = None, **kwargs: Any):
        self.model = model
        self.name = name or model.__name__
        self.fields = model.model_fields
        self.kwargs = kwargs

        self._exclude: set[str] = set()
        self._overrides: dict[str, type] = {}

        self._base_fields: dict[str, tuple[Any, Any]] = {}
        self._related_fields: dict[str, tuple[Any, Any]] = {}

        self._split_fields()

    def exclude(self, fields: list[str]) -> "BaseDBSchema":
        """Exclude specific fields."""
        self._exclude.update(fields)
        self._split_fields()  # Re-split after excluding
        return self

    def override_types(self, overrides: dict[str, type]) -> "BaseDBSchema":
        """Override field types."""
        self._overrides.update(overrides)
        self._split_fields()  # Re-split after overriding
        return self

    def _split_fields(self) -> None:
        """Split scalar and relationship fields."""
        self._base_fields.clear()
        self._related_fields.clear()

        for field_name, field in self.fields.items():
            if field_name in self._exclude:
                continue

            annotation = self._overrides.get(field_name, field.annotation)
            default = field.default if field.default is not None else ...

            if (
                hasattr(annotation, "__origin__") and annotation.__origin__ is list
            ) or (hasattr(annotation, "__name__") and issubclass(annotation, SQLModel)):
                self._related_fields[field_name] = (annotation, default)
            else:
                self._base_fields[field_name] = (annotation, default)

    def create_schema(self) -> Type[SQLModel]:
        """Schema for creation — no relationships."""
        return create_model(
            f"{self.name}Create",
            **self._base_fields,
            __base__=SQLModel,
        )

    def read_schema(self) -> Type[SQLModel]:
        """Schema for reading — includes relationships."""
        cls = create_model(
            f"{self.name}Read",
            **(self._base_fields | self._related_fields),
            __base__=SQLModel,
        )
        cls.model_config = {"from_attributes": True}
        return cls

    def update_schema(self) -> Type[SQLModel]:
        """Schema for partial updates — all fields optional."""
        optional_fields = {
            key: (typ, None) for key, (typ, _) in self._base_fields.items()
        }
        return create_model(
            f"{self.name}Update",
            **optional_fields,
            __base__=SQLModel,
        )
