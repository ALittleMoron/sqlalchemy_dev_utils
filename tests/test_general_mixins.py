from typing import TYPE_CHECKING

import pytest
from sqlalchemy import select
from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy.orm import DeclarativeBase, Mapped, load_only

from sqlalchemy_dev_utils.mixins import general as general_mixins
from sqlalchemy_dev_utils.mixins import ids as ids_mixins
from tests.utils import MyModel

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from tests.types import SyncFactoryFunctionProtocol


class Base(DeclarativeBase): ...  # noqa: D101


class DictConvertModel(  # noqa: D101
    general_mixins.DictConverterMixin,
    ids_mixins.IntegerIDMixin,
    Base,
):
    __tablename__ = "dct_convert"

    some_other_attr: Mapped[str]

    @hybrid_method
    def some_hybrid_method(self) -> Mapped[int]:  # noqa: D102
        return self.id  # type: ignore[reportReturnType]


class DifferenceModel(  # noqa: D101
    general_mixins.DifferenceMixin,
    ids_mixins.IntegerIDMixin,
    Base,
):
    __tablename__ = "diff_model"

    some_other_attr: Mapped[str]


class BetterReprModel(  # noqa: D101
    general_mixins.BetterReprMixin,
    ids_mixins.IntegerIDMixin,
    Base,
):
    __tablename__ = "table_with_good_repr"

    some_other_attr: Mapped[str]


def test_dict_convert() -> None:
    instance = DictConvertModel(id=1, some_other_attr="aboba")
    assert instance.as_dict() == {"id": 1, "some_other_attr": "aboba", "some_hybrid_method": 1}
    assert instance.as_dict(exclude={"some_other_attr", "some_hybrid_method"}) == {"id": 1}
    assert instance.as_dict(exclude={"some_other_attr", "some_hybrid_method"}, id="other_id") == {
        "other_id": 1,
    }
    assert instance.as_dict(exclude={"some_other_attr", "id"}, some_hybrid_method="other") == {
        "other": 1,
    }


def test_difference() -> None:
    DifferenceModel.__safe_difference__ = True
    instance = DifferenceModel(id=1, some_other_attr="bib")
    same = DifferenceModel(id=1, some_other_attr="bib")
    different = DifferenceModel(id=2, some_other_attr="bob")
    same_id = DifferenceModel(id=1, some_other_attr="bobob")
    other = DictConvertModel(id=1, some_other_attr="aboba")
    assert instance.is_different_from({"id": 2, "some_other_attr": "bob"}) is True
    assert instance.is_different_from(same) is False
    assert instance.is_different_from(different) is True
    assert instance.is_different_from({"id": 1, "some_other_attr": "bib"}) is False
    assert instance.is_different_from({"some_other_attr": "bib"}) is False
    assert instance.is_different_from({"id": 1}) is False
    assert instance.is_different_from({"incorrect_attribute": 255}) is True
    assert instance.is_different_from(same_id, exclude={"some_other_attr"}) is False
    assert (
        instance.is_different_from(
            {"id": 1, "some_other_attr": "bobobo"},
            exclude={"some_other_attr"},
        )
        is False
    )
    assert instance.is_different_from(other) is True
    DifferenceModel.__safe_difference__ = False


def test_difference_with_unloaded_fields(
    db_sync_session: "Session",
    mymodel_sync_factory: "SyncFactoryFunctionProtocol[MyModel]",
) -> None:
    orig_value = mymodel_sync_factory(db_sync_session)
    assert orig_value.name is not None, "incorrect MyModel create in factory."
    assert orig_value.other_name is not None, "incorrect MyModel create in factory."
    my_model_instance = MyModel(
        id=orig_value.id + 1,
        name=orig_value.name + "abc",
        other_name=orig_value.other_name + "abc",
    )
    db_sync_session.expire(orig_value)
    MyModel.__safe_difference__ = True
    selected_with_unload = db_sync_session.scalar(
        select(MyModel).options(load_only(MyModel.id, raiseload=True)),
    )
    assert selected_with_unload is not None, "selected MyModel not found (but must be in DB)"
    assert selected_with_unload.is_different_from({"name": "abc"}) is True
    assert selected_with_unload.is_different_from(my_model_instance) is True
    MyModel.__safe_difference__ = False


def test_difference_with_unloaded_fields_unsafe(
    db_sync_session: "Session",
    mymodel_sync_factory: "SyncFactoryFunctionProtocol[MyModel]",
) -> None:
    mymodel_sync_factory(db_sync_session)
    MyModel.__safe_difference__ = False
    selected_with_unload = db_sync_session.scalar(
        select(MyModel).options(load_only(MyModel.id, raiseload=True)),
    )
    assert selected_with_unload is not None, "selected MyModel not found (but must be in DB)"
    with pytest.raises(AttributeError):
        selected_with_unload.is_different_from({"name": "abc"})


def test_difference_incorrect_type() -> None:
    instance = DifferenceModel(id=1, some_other_attr="bib")
    other = DictConvertModel(id=1, some_other_attr="aboba")
    with pytest.raises(TypeError):
        instance.is_different_from(other)


def test_difference_unsafe() -> None:
    instance = DifferenceModel(id=1, some_other_attr="bib")
    with pytest.raises(AttributeError):
        instance.is_different_from({"incorrect_attribute": 255})


def test_default_better_repr() -> None:

    instance = BetterReprModel(id=1, some_other_attr="some")
    instance_repr = repr(instance)
    assert instance_repr.startswith('BetterReprModel')
    assert "id=1" in instance_repr
    assert "some_other_attr='some'" in instance_repr


def test_full_class_path_in_repr() -> None:
    class OtherBetterReprModel(
        general_mixins.BetterReprMixin,
        ids_mixins.IntegerIDMixin,
        Base,
    ):
        __tablename__ = "other_table_with_good_repr"

        __use_full_class_path__ = True

        some_other_attr: Mapped[str]

    instance = OtherBetterReprModel(id=1, some_other_attr="some")
    instance_repr = repr(instance)
    assert instance_repr.startswith(
        'tests.test_general_mixins.test_full_class_path_in_repr.<locals>.OtherBetterReprModel',
    )


def test_repr_include_fields() -> None:
    class OtherOtherBetterReprModel(
        general_mixins.BetterReprMixin,
        ids_mixins.IntegerIDMixin,
        Base,
    ):
        __tablename__ = "other_other_table_with_good_repr"
        __repr_include_fields__ = {"id"}  # noqa: RUF012

        some_other_attr: Mapped[str]

    instance = OtherOtherBetterReprModel(id=1, some_other_attr="some")
    instance_repr = repr(instance)
    assert instance_repr == 'OtherOtherBetterReprModel(id=1)'


def test_max_repr_elements() -> None:
    class MaxReprOtherBetterReprModel(
        general_mixins.BetterReprMixin,
        ids_mixins.IntegerIDMixin,
        Base,
    ):
        __tablename__ = "max_repr_other_table_with_good_repr"

        __max_repr_elements__ = 1

        some_other_attr: Mapped[str]

    instance = MaxReprOtherBetterReprModel(id=1, some_other_attr="some")
    instance_repr = repr(instance)
    assert instance_repr == 'MaxReprOtherBetterReprModel(id=1)'


async def test_unload_fields_in_repr(
    db_sync_session: "Session",
    mymodel_sync_factory: "SyncFactoryFunctionProtocol[MyModel]",
) -> None:
    orig_value = mymodel_sync_factory(db_sync_session)
    db_sync_session.expire(orig_value)
    MyModel.__safe_difference__ = True
    selected_with_unload = db_sync_session.scalar(
        select(MyModel).options(load_only(MyModel.id, raiseload=True)),
    )
    assert selected_with_unload, "MyModel instance not found (but it must be in DB)"
    selected_with_unload_repr = repr(selected_with_unload)
    assert "<Not loaded>" in selected_with_unload_repr


def test_table_name_auto() -> None:
    class TableNameModel(
        general_mixins.TableNameMixin,
        ids_mixins.IntegerIDMixin,
        Base,
    ):
        some_other_attr: Mapped[str]

    assert TableNameModel.__tablename__ == "table_name_model"


def test_table_name_with_app_name_auto() -> None:
    class TableNameWithAppNameModel(
        general_mixins.TableNameMixin,
        ids_mixins.IntegerIDMixin,
        Base,
    ):
        __join_application_prefix__ = True
        some_other_attr: Mapped[str]

    assert (
        TableNameWithAppNameModel.__tablename__
        == "test_general_mixins_table_name_with_app_name_model"
    )
    TableNameWithAppNameModel.__module__ = '__main__'
    assert TableNameWithAppNameModel.__tablename__ == "table_name_with_app_name_model"
    TableNameWithAppNameModel.__module__ = 'models'
    assert TableNameWithAppNameModel.__tablename__ == "table_name_with_app_name_model"
    TableNameWithAppNameModel.__module__ = 'users.models'
    assert TableNameWithAppNameModel.__tablename__ == "users_table_name_with_app_name_model"
