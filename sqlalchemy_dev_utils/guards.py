from typing import Any, TypeGuard

from sqlalchemy.orm.attributes import QueryableAttribute


def is_queryable_attribute(value: Any) -> "TypeGuard[QueryableAttribute[Any]]":  # noqa: ANN401
    """TypeGuard, that check if object is QueryableAttribute."""
    return isinstance(value, QueryableAttribute)
