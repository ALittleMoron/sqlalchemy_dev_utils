from sqlalchemy import Constraint
from sqlalchemy.sql.base import _NONE_NAME  # type: ignore[reportPrivateUsage]

from sqlalchemy_dev_utils.naming_conventions import auto_constraint_name


def test_auto_constraint_name_no_name() -> None:
    assert auto_constraint_name(Constraint(), None).startswith("sa_autoname_")


def test_auto_constraint_name_unnamed_name() -> None:
    assert auto_constraint_name(Constraint(name="_unnamed_"), None).startswith("sa_autoname_")


def test_auto_constraint_name_regular_name() -> None:
    assert auto_constraint_name(Constraint(name="regular_str"), None) == "regular_str"


def test_auto_constraint_name_no_name_enum() -> None:
    assert auto_constraint_name(Constraint(name=_NONE_NAME), None) == "_unnamed_"
