"""Type module with datetime types for columns."""

import datetime
import zoneinfo
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, TypeDecorator
from sqlalchemy.ext.compiler import compiles  # type: ignore[reportUnknownVariableType]
from sqlalchemy.sql import expression

if TYPE_CHECKING:
    from sqlalchemy.engine.interfaces import Dialect


UTC = zoneinfo.ZoneInfo("UTC")


class Utcnow(expression.FunctionElement[datetime.datetime]):
    """Alias for DateTime type for new mapping.

    Needs to avoid incorrect type mapping (use only Utcnow type, not all DateTime columns).
    """

    type = DateTime()


class UTCDateTime(TypeDecorator[datetime.datetime]):
    """Type decorator for DateTime with UTC."""

    impl = DateTime(timezone=True)
    cache_ok = True

    @property
    def python_type(self) -> type[datetime.datetime]:  # noqa: D102  # pragma: no coverage
        return datetime.datetime

    def process_result_value(  # noqa: D102
        self: "UTCDateTime",
        value: "datetime.datetime | None",
        dialect: "Dialect",  # noqa: ARG002
    ) -> "datetime.datetime | None":
        if value is None:
            return value
        if value.tzinfo is None:
            return value.replace(tzinfo=datetime.UTC)
        return value

    def process_bind_param(  # noqa: D102
        self: "UTCDateTime",
        value: "datetime.datetime | None",
        dialect: "Dialect",  # noqa: ARG002
    ) -> "datetime.datetime | None":
        if value is None:
            return value
        if value.tzinfo is None:
            msg = (
                f'UTCDateTime type requires the tzinfo param to be set in datetime field. '
                f'{type(value)} was passed.'
            )
            raise TypeError(msg)
        return value.astimezone(datetime.UTC)


@compiles(Utcnow, "postgresql")
def pg_utcnow(
    type_: Any,  # noqa: ANN401, ARG001, F841, RUF100
    compiler: Any,  # noqa: ANN401, ARG001, F841, RUF100
    **kwargs: Any,  # noqa: ANN401, ARG001, F841, RUF100
) -> str:
    """Mapping for Utcnow on postgresql current time func with timezone."""  # noqa: D401
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"


@compiles(Utcnow, "sqlite")
def sqlite_utcnow(
    type_: Any,  # noqa: ANN401, ARG001, F841, RUF100
    compiler: Any,  # noqa: ANN401, ARG001, F841, RUF100
    **kwargs: Any,  # noqa: ANN401, ARG001, F841, RUF100
) -> str:
    """Mapping for Utcnow on sqlite current time func with timezone."""  # noqa: D401
    return "DATETIME('now')"


@compiles(Utcnow, "mysql")
def mysql_utcnow(
    type_: Any,  # noqa: ANN401, ARG001, F841, RUF100
    compiler: Any,  # noqa: ANN401, ARG001, F841, RUF100
    **kwargs: Any,  # noqa: ANN401, ARG001, F841, RUF100
) -> str:
    """Mapping for Utcnow on mysql current time func with timezone."""  # noqa: D401
    return "UTC_TIMESTAMP()"
