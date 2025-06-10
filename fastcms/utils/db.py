# fastcms/utils/db.py

from typing import Any

from sqlmodel import SQLModel
from sqlalchemy import and_, true
from sqlalchemy.sql.elements import BinaryExpression, ClauseElement

OPERATORS = {
    "eq": lambda f, v: f == v,
    "ne": lambda f, v: f != v,
    "lt": lambda f, v: f < v,
    "lte": lambda f, v: f <= v,
    "gt": lambda f, v: f > v,
    "gte": lambda f, v: f >= v,
    "like": lambda f, v: f.like(v),
    "ilike": lambda f, v: f.ilike(v),
    "in": lambda f, v: f.in_(v if isinstance(v, list) else [v]),
    "notin": lambda f, v: ~f.in_(v if isinstance(v, list) else [v]),
    "isnull": lambda f, v: f.is_(None) if v else f.is_not(None),
}


def parse_filters(model: type[SQLModel], filters: dict[str, Any]) -> ClauseElement:
    """
    Parses dict of filters like {'age__gt': 30, 'name__ilike': '%azat%'} into SQLAlchemy expressions.

    :param model: The SQLModel class to filter.
    :param filters: A dictionary where keys are field names and values are filter criteria.
    :return: A SQLAlchemy expression for filtering.
    """
    expressions: list[BinaryExpression] = []

    for field, value in filters.items():
        if "__" in field:
            field_name, operator = field.rsplit("__", 1)
        else:
            field_name, operator = field, "eq"

        if hasattr(model, field_name):
            column = getattr(model, field_name)
            if operator in OPERATORS:
                expressions.append(OPERATORS[operator](column, value))

    return and_(*expressions) if expressions else true()
