import datetime
from typing import TYPE_CHECKING, Any

import pytest
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel
from sqlalchemy.exc import StatementError

from tests.utils import (
    PydanticTestSchema,
    TableWithUTCDT,
    create_db_item_sync,
    generate_datetime_list,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from tests.types import SyncFactoryFunctionProtocol


class OtherPydanticTestSchema(BaseModel):  # noqa: D101
    a: int
    b: int
    c: int


@pytest.fixture()
def table_create() -> "SyncFactoryFunctionProtocol[TableWithUTCDT]":
    def _create(
        session: "Session",
        *,
        commit: bool = False,
        **kwargs: Any,  # noqa: ANN401
    ) -> TableWithUTCDT:
        return create_db_item_sync(session, TableWithUTCDT, kwargs, commit=commit)

    return _create


@pytest.mark.parametrize(
    "dt",
    [*generate_datetime_list(n=5, tz=datetime.UTC), None],
)
def test_dt_field(
    dt: datetime.datetime,
    db_sync_session: "Session",
    table_create: "SyncFactoryFunctionProtocol[TableWithUTCDT]",
) -> None:
    item = table_create(db_sync_session, dt_field=dt, commit=True)
    if item.dt_field is None:
        pytest.skip("dt_field is None (Not unexpected value).")
    assert item.dt_field.tzinfo is not None
    assert item.dt_field.tzinfo == datetime.UTC


@pytest.mark.parametrize(
    "dt",
    generate_datetime_list(n=5),
)
def test_dt_field_type_error(
    dt: datetime.datetime,
    db_sync_session: "Session",
    table_create: "SyncFactoryFunctionProtocol[TableWithUTCDT]",
) -> None:
    with pytest.raises(StatementError):
        table_create(db_sync_session, dt_field=dt, commit=True)


@pytest.mark.parametrize(
    "schema",
    [PydanticTestSchema(a=1, b=2, c=3), PydanticTestSchema(a=4, b=5, c=6), None],
)
def test_pydantic_type(
    schema: PydanticTestSchema | None,
    db_sync_session: "Session",
    table_create: "SyncFactoryFunctionProtocol[TableWithUTCDT]",
) -> None:
    item = table_create(db_sync_session, pydantic_type=schema, commit=True)
    if item.pydantic_type is None:
        pytest.skip("pydantic_type is None (Not unexpected value).")
    assert isinstance(item.pydantic_type, PydanticTestSchema)


@pytest.mark.parametrize(
    "item",
    [
        "string",
        25,
        25.0,
        {"a": 1, "b": 2, "c": 3},
        [1, 2, 3],
        [{"a": 1, "b": 2, "c": 3}],
    ],
)
def test_pydantic_field_type_error(
    item: Any,  # noqa: ANN401
    db_sync_session: "Session",
    table_create: "SyncFactoryFunctionProtocol[TableWithUTCDT]",
) -> None:
    with pytest.raises(StatementError):
        table_create(db_sync_session, pydantic_type=item, commit=True)


@pytest.mark.parametrize(
    "schema",
    [
        [PydanticTestSchema(a=1, b=2, c=3)],
        [PydanticTestSchema(a=1, b=2, c=3), PydanticTestSchema(a=4, b=5, c=6)],
        None,
    ],
)
def test_pydantic_list_type(
    schema: list[PydanticTestSchema] | None,
    db_sync_session: "Session",
    table_create: "SyncFactoryFunctionProtocol[TableWithUTCDT]",
) -> None:
    item = table_create(db_sync_session, pydantic_list_type=schema, commit=True)
    if item.pydantic_list_type is None:
        pytest.skip("pydantic_list_type is None (Not unexpected value).")
    assert isinstance(item.pydantic_list_type, list)
    for ele in item.pydantic_list_type:
        assert isinstance(ele, PydanticTestSchema)


@pytest.mark.parametrize(
    "item",
    [
        "string",
        25,
        25.0,
        {"a": 1, "b": 2, "c": 3},
        [1, 2, 3],
        [{"a": 1, "b": 2, "c": 3}],
    ],
)
def test_pydantic_list_field_type_error(
    item: Any,  # noqa: ANN401
    db_sync_session: "Session",
    table_create: "SyncFactoryFunctionProtocol[TableWithUTCDT]",
) -> None:
    with pytest.raises(StatementError):
        table_create(db_sync_session, pydantic_type=item, commit=True)


@pytest.mark.parametrize(
    "schema",
    [
        [OtherPydanticTestSchema(a=1, b=2, c=3)],
        [OtherPydanticTestSchema(a=1, b=2, c=3), OtherPydanticTestSchema(a=4, b=5, c=6)],
    ],
)
def test_pydantic_list_field_other_schema(
    schema: Any,  # noqa: ANN401
    db_sync_session: "Session",
    table_create: "SyncFactoryFunctionProtocol[TableWithUTCDT]",
) -> None:
    with pytest.raises(StatementError):
        table_create(db_sync_session, pydantic_type=schema, commit=True)


@pytest.mark.parametrize(
    ("interval", "expected_value"),
    [
        (None, None),
        (datetime.timedelta(days=25), relativedelta(days=25)),
        (datetime.timedelta(days=25, seconds=100), relativedelta(days=25, seconds=100)),
        (
            datetime.timedelta(days=25, seconds=100, microseconds=100),
            relativedelta(days=25, seconds=100, microseconds=100),
        ),
        (relativedelta(days=25), relativedelta(days=25)),
        (relativedelta(days=25, seconds=100), relativedelta(days=25, seconds=100)),
        (
            relativedelta(days=25, seconds=100, microseconds=100),
            relativedelta(days=25, seconds=100, microseconds=100),
        ),
        (
            relativedelta(years=10, days=25, seconds=100, microseconds=100),
            relativedelta(years=10, days=25, seconds=100, microseconds=100),
        ),
        (
            relativedelta(years=10, months=10, days=25, seconds=100, microseconds=100),
            relativedelta(years=10, months=10, days=25, seconds=100, microseconds=100),
        ),
        (
            relativedelta(years=10, months=10, weeks=10, days=25, seconds=100, microseconds=100),
            relativedelta(years=10, months=10, weeks=10, days=25, seconds=100, microseconds=100),
        ),
        (
            relativedelta(
                years=10,
                months=10,
                weeks=10,
                days=25,
                hours=10,
                seconds=100,
                microseconds=100,
            ),
            relativedelta(
                years=10,
                months=10,
                weeks=10,
                days=25,
                hours=10,
                seconds=100,
                microseconds=100,
            ),
        ),
    ],
)
def test_relative_interval(
    interval: Any,  # noqa: ANN401
    expected_value: Any,  # noqa: ANN401
    db_sync_session: "Session",
    table_create: "SyncFactoryFunctionProtocol[TableWithUTCDT]",
) -> None:
    item = table_create(db_sync_session, relative_interval=interval, commit=True)
    db_sync_session.refresh(item)
    if expected_value is not None:
        assert isinstance(item.relative_interval, relativedelta)
    assert item.relative_interval == expected_value
