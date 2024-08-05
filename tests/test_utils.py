import datetime
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

import pytest
from sqlalchemy import delete, func, insert, inspect, select, update
from sqlalchemy.orm import (
    DeclarativeBase,
    Session,
    joinedload,
    load_only,
    selectinload,
    subqueryload,
)

from sqlalchemy_dev_utils import utils
from sqlalchemy_dev_utils.exc import NoModelAttributeError, NoModelRelationshipError
from tests.utils import Base, MyModel, OtherModel

if TYPE_CHECKING:
    from tests.types import SyncFactoryFunctionProtocol


@pytest.mark.parametrize(
    ("obj", "expected_result"),
    [
        (MyModel, True),
        (254, False),
        (MyModel.__table__, False),
    ],
)
def test_is_declarative(
    obj: Any,  # noqa: ANN401
    expected_result: bool,  # noqa: FBT001
) -> None:
    assert utils.is_declarative(obj) == expected_result


def test_get_unloaded_fields(
    db_sync_session: "Session",
    mymodel_sync_factory: "SyncFactoryFunctionProtocol[MyModel]",
) -> None:
    mymodel_sync_factory(db_sync_session)
    selected_with_unload = db_sync_session.scalar(
        select(MyModel).options(load_only(MyModel.bl), selectinload(MyModel.other_models)),
    )
    assert selected_with_unload is not None, "model not found (but should be presented in db)"
    assert utils.get_unloaded_fields(selected_with_unload) == {"name", "other_name", "dt"}


@pytest.mark.parametrize(
    ("exclude", "data", "expected_result"),
    [
        (
            None,
            {
                "id": 1,
                "name": "name",
                "other_name": "other_name",
                "dt": datetime.datetime(2023, 5, 25, 12, 25, 25, tzinfo=datetime.UTC),
                "bl": True,
            },
            {
                "id": 1,
                "name": "name",
                "other_name": "other_name",
                "dt": datetime.datetime(2023, 5, 25, 12, 25, 25, tzinfo=datetime.UTC),
                "bl": True,
            },
        ),
        (
            {"id", "dt", "bl"},
            {
                "id": 1,
                "name": "name",
                "other_name": "other_name",
                "dt": datetime.datetime(2023, 5, 25, 12, 25, 25, tzinfo=datetime.UTC),
                "bl": True,
            },
            {"name": "name", "other_name": "other_name"},
        ),
    ],
)
def test_get_model_instance_data_as_dict(
    exclude: set[str] | None,
    data: dict[str, Any],
    expected_result: dict[str, Any],
    db_sync_session: "Session",
    mymodel_sync_factory: "SyncFactoryFunctionProtocol[MyModel]",
) -> None:
    instance = mymodel_sync_factory(db_sync_session, **data)
    assert (
        utils.get_model_instance_data_as_dict(instance=instance, exclude=exclude) == expected_result
    )


@pytest.mark.parametrize(
    ("field", "only_columns", "expected_result"),
    [  # type: ignore[reportUnknownArgumentType]
        ("id", False, MyModel.id),
        ("id", True, MyModel.id),
        ("name", False, MyModel.name),
        ("name", True, MyModel.name),
        ("full_name", False, MyModel.full_name),  # type: ignore[reportUnknownMemberType]
        ("get_full_name", False, MyModel.get_full_name()),
    ],
)
def test_get_sqlalchemy_attribute(
    field: str,
    only_columns: bool,  # noqa: FBT001
    expected_result: Any,  # noqa: ANN401
) -> None:
    assert str(
        utils.get_sqlalchemy_attribute(MyModel, field, only_columns=only_columns),  # type: ignore[reportCallIssue]
    ) == str(expected_result)


@pytest.mark.parametrize(
    ("field", "only_columns"),
    [
        ('incorrect_field', False),
        ('incorrect_field', True),
    ],
)
def test_get_sqlalchemy_attribute_incorrect(
    field: str,
    only_columns: bool,  # noqa: FBT001
) -> None:
    with pytest.raises(NoModelAttributeError):
        utils.get_sqlalchemy_attribute(MyModel, field, only_columns=only_columns)  # type: ignore[reportCallIssue]


def test_get_registry_class() -> None:
    assert utils.get_registry_class(MyModel) == MyModel.registry._class_registry  # type: ignore[reportPrivateUsage]  # noqa: SLF001


@pytest.mark.parametrize(
    ("stmt", "expected_result"),
    [
        (select(MyModel), [MyModel]),
        (select(MyModel, OtherModel), [MyModel, OtherModel]),
        (select(), []),
        (insert(MyModel), [MyModel]),
        (update(MyModel), [MyModel]),
        (delete(MyModel), [MyModel]),
        (select(func.count()).select_from(MyModel), [MyModel]),
        (select(MyModel.id).select_from(MyModel), [MyModel]),
        (select(func.count()).select_from(select(MyModel).subquery()), []),
    ],
)
def test_get_model_classes_from_statement(
    stmt: utils.Statement,
    expected_result: Sequence[type[Base]],
) -> None:
    assert set(utils.get_model_classes_from_statement(stmt)) == set(expected_result)


@pytest.mark.parametrize(
    ("name", "expected_result"),
    [
        ("MyModel", MyModel),
        ("OtherModel", OtherModel),
        ("NoModel", None),
    ],
)
def test_get_model_class_by_name(
    name: str,
    expected_result: type[Base] | None,
) -> None:
    register = utils.get_registry_class(MyModel)
    assert utils.get_model_class_by_name(register, name) == expected_result


@pytest.mark.parametrize(
    ("name", "expected_result"),
    [
        ("my_model", MyModel),
        ("other_model", OtherModel),
        ("no_model", None),
    ],
)
def test_get_model_class_by_tablename(
    name: str,
    expected_result: type[Base] | None,
) -> None:
    register = utils.get_registry_class(MyModel)
    assert utils.get_model_class_by_tablename(register, name) == expected_result


def test_get_valid_model_class_names() -> None:
    register = utils.get_registry_class(MyModel)
    assert utils.get_valid_model_class_names(register) == {
        "MyModel",
        "OtherModel",
        "TableWithUTCDT",
    }


@pytest.mark.parametrize(
    ("model", "expected_result"),
    [
        (MyModel, [OtherModel]),
        (OtherModel, [MyModel]),
    ],
)
def test_get_related_models(
    model: type[DeclarativeBase],
    expected_result: list[type[DeclarativeBase]],
) -> None:
    assert utils.get_related_models(model) == expected_result


def test_get_valid_field_names() -> None:
    assert utils.get_valid_field_names(MyModel) == {
        "id",
        "name",
        "other_name",
        "dt",
        "bl",
        "full_name",
        "get_full_name",
    }


def test_get_valid_field_names_only_columns() -> None:
    assert utils.get_valid_field_names(MyModel, only_columns=True) == {
        "id",
        "name",
        "other_name",
        "dt",
        "bl",
    }


@pytest.mark.parametrize(
    ("field", "expected_result"),
    [
        ("id", False),
        ("name", False),
        ("other_name", False),
        ("full_name", True),
        ("get_full_name", False),
    ],
)
def test_is_hybrid_property(
    field: str,
    expected_result: bool,  # noqa: FBT001
) -> None:
    insp = inspect(MyModel).all_orm_descriptors  # type: ignore[reportUnknownMemberType]
    assert utils.is_hybrid_property(insp[field]) == expected_result  # type: ignore[reportUnknownMemberType]


@pytest.mark.parametrize(
    ("field", "expected_result"),
    [
        ("id", False),
        ("name", False),
        ("other_name", False),
        ("full_name", False),
        ("get_full_name", True),
    ],
)
def test_is_hybrid_method(
    field: str,
    expected_result: bool,  # noqa: FBT001
) -> None:
    insp = inspect(MyModel).all_orm_descriptors  # type: ignore[reportUnknownMemberType]
    assert utils.is_hybrid_method(insp[field]) == expected_result  # type: ignore[reportUnknownMemberType]


@pytest.mark.parametrize(
    ("stmt", "relationship_names", "load_strategy", "expected_result"),
    [
        (
            select(MyModel),
            ("other_models",),
            joinedload,
            select(MyModel).options(joinedload(MyModel.other_models)),
        ),
        (
            select(MyModel),
            ("other_models",),
            selectinload,
            select(MyModel).options(selectinload(MyModel.other_models)),
        ),
        (
            select(MyModel),
            ("other_models",),
            subqueryload,
            select(MyModel).options(subqueryload(MyModel.other_models)),
        ),
    ],
)
def test_apply_loads(
    stmt: Any,  # noqa: ANN401
    relationship_names: tuple[str, ...],
    load_strategy: Any,  # noqa: ANN401
    expected_result: Any,  # noqa: ANN401
) -> None:
    assert str(
        utils.apply_loads(
            stmt,
            *relationship_names,
            load_strategy=load_strategy,
        ),
    ) == str(
        expected_result,
    )


def test_apply_incorrect_loads() -> None:
    with pytest.raises(NoModelRelationshipError):
        utils.apply_loads(select(MyModel), "no_model_rel")


@pytest.mark.parametrize(
    ("stmt", "relationship_names", "left_outer_join", "full_join", "expected_result"),
    [
        (
            select(MyModel),
            ("other_models",),
            False,
            False,
            select(MyModel).join(MyModel.other_models),
        ),
        (
            select(MyModel),
            ("other_models",),
            True,
            False,
            select(MyModel).join(MyModel.other_models, isouter=True),
        ),
        (
            select(MyModel),
            ("other_models",),
            False,
            True,
            select(MyModel).join(MyModel.other_models, full=True),
        ),
    ],
)
def test_apply_joins(
    stmt: Any,  # noqa: ANN401
    relationship_names: tuple[str, ...],
    left_outer_join: bool,  # noqa: FBT001
    full_join: bool,  # noqa: FBT001
    expected_result: Any,  # noqa: ANN401
) -> None:
    assert str(
        utils.apply_joins(
            stmt,
            *relationship_names,
            left_outer_join=left_outer_join,
            full_join=full_join,
        ),
    ) == str(
        expected_result,
    )


def test_apply_incorrect_joins() -> None:
    with pytest.raises(NoModelRelationshipError):
        utils.apply_joins(select(MyModel), "no_model_rel")
