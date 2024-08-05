"""Module with naming conventions."""

import uuid
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy import Constraint


def auto_constraint_name(constraint: "Constraint", _: Any) -> str:  # noqa: ANN401
    """Autogenerate constraint name function."""
    if constraint.name is None or constraint.name == "_unnamed_":
        return f"sa_autoname_{str(uuid.uuid4())[0:5]}"
    if isinstance(constraint.name, str):
        return constraint.name
    return '_unnamed_'


GENERAL_NAMING_CONVENTION: dict[str, Any] = {
    "auto_constraint_name": auto_constraint_name,
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(auto_constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
"""Naming convention for MetaData object.

General convention, that you can find in any tutorials or in alembic documentation:

https://alembic.sqlalchemy.org/en/latest/naming.html

Usage
-----

as separate metadata:
```
from sqlalchemy import MetaData
from sqlalchemy_dev_utils.naming_conventions import GENERAL_NAMING_CONVENTION

metadata = MetaData(naming_convention=GENERAL_NAMING_CONVENTION)
```

as DeclarativeBase metadata:
```
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy_dev_utils.naming_conventions import GENERAL_NAMING_CONVENTION

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=GENERAL_NAMING_CONVENTION)
```
"""
