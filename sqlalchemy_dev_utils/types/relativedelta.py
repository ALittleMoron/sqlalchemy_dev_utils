import datetime
from typing import TYPE_CHECKING, Any, ClassVar

from dateutil.relativedelta import relativedelta
from dev_utils.guards import all_dict_keys_are_str
from sqlalchemy import JSON as JSON_COLUMN
from sqlalchemy import TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON as JSON_TYPE

if TYPE_CHECKING:
    from sqlalchemy.engine.interfaces import Dialect


class RelativeInterval(TypeDecorator[relativedelta]):
    """Interval with relativedelta implementation.

    By default, Interval SQLAlchemy type represents ``datetime.timedelta`` type in python.
    It is possible to make native interval with relativedelta, but it should be implemented on
    driver level, because ``datetime.timedelta`` objects converts from native Interval type on
    driver level (see https://stackoverflow.com/a/19303883).

    According to this information, RelativeInterval was implemented as
    """

    impl = JSON_TYPE
    cache_ok = True

    attr_keys: ClassVar[dict[type, set[str]]] = {
        datetime.timedelta: {'days', 'seconds', 'microseconds'},
        relativedelta: {
            'years',
            'months',
            'days',
            'leapdays',
            'hours',
            'minutes',
            'seconds',
            'microseconds',
            'year',
            'month',
            'day',
            'hour',
            'minute',
            'second',
            'microsecond',
        },
    }

    def load_dialect_impl(self, dialect: "Dialect"):  # noqa: D102, ANN201
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON_COLUMN())

    def process_bind_param(  # noqa: D102
        self,
        value: datetime.timedelta | relativedelta | None,
        dialect: "Dialect",  # noqa: ARG002
    ) -> dict[str, Any] | None:
        match value:
            case None:
                return value
            case datetime.timedelta() | relativedelta():
                return {key: getattr(value, key) for key in self.attr_keys[type(value)]}
            case _:  # type: ignore[reportUnnecessaryComparison]
                msg = (
                    "Input type for RelativeInterval should be datetime.timedelta or relativedelta "
                    "or None."
                )
                raise TypeError(msg)

    def process_result_value(  # noqa: D102
        self,
        value: Any,  # noqa: ANN401
        dialect: "Dialect",  # noqa: ARG002
    ) -> relativedelta | None:
        if value is None:
            return value
        if not isinstance(value, dict):
            msg = (
                f"Your database contains {type(value)} in your RelativeInterval field, but json "
                "object, that represents dict in python is required. Maybe someone changed "
                "database raw manually."
            )
            raise TypeError(msg)
        if not all_dict_keys_are_str(value):  # type: ignore[reportUnknownArgumentType]
            msg = (
                "Your database contains RelativeInterval json object, that contains not string "
                "key in it. Incorrect RelativeInterval structure! Maybe someone changed database "
                "raw manually."
            )
            raise TypeError(msg)
        if not set(value.keys()).issubset(self.attr_keys[relativedelta]):
            keys = ', '.join(set(value.keys()) - self.attr_keys[relativedelta])
            msg = (
                f"Your database contains RelativeInterval json object ({value}), that contains "
                f"not supported keys ({keys}). It could not be represented as relativedelta "
                "object. Maybe someone changed database raw manually."
            )
            raise TypeError(msg)
        return relativedelta(**value)
