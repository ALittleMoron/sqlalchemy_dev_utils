import re
from typing import TYPE_CHECKING, Any, ClassVar, TypeAlias
from warnings import warn

from dev_utils.common import get_object_class_absolute_name
from sqlalchemy.orm.decl_api import declarative_mixin, declared_attr

from sqlalchemy_dev_utils.mixins.base import BaseModelMixin
from sqlalchemy_dev_utils.utils import (
    get_model_instance_data_as_dict,
    get_unloaded_fields,
    get_valid_field_names,
)

if TYPE_CHECKING:
    from sqlalchemy.orm.decl_api import DeclarativeBase

    DictStrAny: TypeAlias = dict[str, Any]


@declarative_mixin
class DictConverterMixin(BaseModelMixin):
    """Mixin for converting models to dict."""

    def _replace(
        self,
        item: dict[str, Any],
        **replace: str,
    ) -> None:
        """Add replace field for item.

        Uses like alias: rename existing fields
        """
        for original, replaced in replace.items():
            value_to_replace = self._get_instance_attr(original)
            item[replaced] = value_to_replace
            item.pop(original, None)

    def as_dict(
        self,
        exclude: set[str] | None = None,
        **replace: str,
    ) -> dict[str, Any]:
        """Convert model instance to dict."""
        valid_fields = get_valid_field_names(self._sa_model_class)
        exclude_fields: set[str] = (exclude or set()).union(
            self._sa_instance_state.unloaded,  # type: ignore[reportUnknownArgumentType]
        )
        available_fields = valid_fields - exclude_fields
        item: dict[str, Any] = {field: self._get_instance_attr(field) for field in available_fields}
        replace = {key: value for key, value in replace.items() if key in item}
        self._replace(item, **replace)
        return item


@declarative_mixin
class DifferenceMixin(BaseModelMixin):
    """Mixin for checking difference between instance and other objects.

    It will not override double underscore methods like __eq__ or other to avoid Incorrect behavior.
    """

    __safe_difference__: ClassVar[bool] = False

    def _is_dict_different_from(
        self,
        item: "DictStrAny",
        exclude: set[str] | None = None,
    ) -> bool:
        """Check is self Declarative instance is different from other dictionary.

        Raises
        ------
        AttributeError
            throw, if there is no attribute in self instance and ``__safe_difference__``
            is not set.
        """
        unloaded_fields = get_unloaded_fields(self)  # type: ignore[reportArgumentType]
        for field, value in item.items():
            if exclude is not None and field in exclude:
                continue
            if field in unloaded_fields:
                cls_path = get_object_class_absolute_name(self)
                msg = f'Field "{field}" is not loaded in {cls_path} instance.'
                if self.__safe_difference__:
                    warn(msg, stacklevel=1)
                    return True
                raise AttributeError(msg)
            if not hasattr(self, field):
                cls_path = get_object_class_absolute_name(self)
                msg = f'Field "{field}" is not present in {cls_path} instance. It may be unloaded.'
                if self.__safe_difference__:
                    warn(msg, stacklevel=1)
                    return True
                raise AttributeError(msg)
            self_field_value = getattr(self, field)
            if self_field_value != value:
                return True
        return False

    def _is_model_different_from(
        self,
        item: "DeclarativeBase",
        exclude: set[str] | None = None,
    ) -> bool:
        """Check is self Declarative instance is different from other Declarative instance.

        Raises
        ------
        AttributeError
            throw, if there is no attribute in self instance and ``__safe_difference__``
            is not set.
        """
        item_dict = get_model_instance_data_as_dict(item)
        return self._is_dict_different_from(item_dict, exclude)

    def is_different_from(
        self,
        item: "DictStrAny | DeclarativeBase",
        exclude: set[str] | None = None,
    ) -> bool:
        """Check is self instance is different from other object (dict or DeclarativeBase).

        Raises
        ------
        TypeError
            throw, if ``item`` param has unsupported type (now only dict and DeclarativeBase
            are supported).
        AttributeError
            throw, if there is no attribute in self instance and ``__safe_difference__``
            is not set.
        """
        self._sa_model_class  # noqa: B018
        if exclude is None:
            exclude = set()
        if isinstance(item, dict):
            return self._is_dict_different_from(item, exclude)
        if self.__class__ == item.__class__:  # type: ignore[reportUnnecessaryComparison]
            return self._is_model_different_from(item, exclude)
        if self.__safe_difference__:
            return True
        msg = f"Incorrect item. Expected: Dict or {self.__class__.__name__}. Got: {type(item)}."
        raise TypeError(msg)


@declarative_mixin
class BetterReprMixin(BaseModelMixin):
    """Mixin with better __repr__ method for SQLAlchemy model instances."""

    __use_full_class_path__: ClassVar[bool] = False
    __max_repr_elements__: ClassVar[int | None] = None
    __repr_include_fields__: ClassVar[set[str] | None] = None

    def __repr__(self) -> str:  # noqa: D105
        fields = get_valid_field_names(self._sa_model_class, only_columns=True)
        unloaded = get_unloaded_fields(self)  # type: ignore[reportArgumentType]
        values_pairs_list: list[str] = []
        # NOTE: id is always loaded, so this if statement part with unloaded is not needed.
        # But I made it for sure.
        if "id" not in unloaded and "id" in fields:
            id_value = repr(self.id)  # type: ignore[reportUnknownArgumentType]
            values_pairs_list.append(f'id={id_value}')
            fields.discard("id")
        for col in fields:
            if col in unloaded:
                values_pairs_list.append(f"{col}=<Not loaded>")
            elif self.__repr_include_fields__ is None or col in self.__repr_include_fields__:
                values_pairs_list.append(f"{col}={getattr(self, col)!r}")
        if self.__max_repr_elements__ is not None:
            values_pairs_list = values_pairs_list[: self.__max_repr_elements__]
        class_name = (
            get_object_class_absolute_name(self)
            if self.__use_full_class_path__
            else self.__class__.__name__
        )
        values_pairs = ", ".join(values_pairs_list)
        return f"{class_name}({values_pairs})"


@declarative_mixin
class TableNameMixin(BaseModelMixin):
    """Mixin for auto-creation of model table name (__tablename__).

    You may pass class-level attribute ``__join_application_prefix__`` to make mixin create
    table names with application prefix. For example, if your model class ``User`` with
    TableNameMixin is located in ``application/models/users.py`` file, your tablename will be
    ``users_user``.
    """

    __join_application_prefix__: ClassVar[bool] = False

    @classmethod
    def _get_model_application_name(cls) -> str:
        """Parse current model file and package context to get app name.

        Analog of django table naming: ``app``_``model``.
        """
        if cls.__module__ == "__main__":
            return ''
        path_parts = cls.__module__.split('.')
        for ele in path_parts[::-1]:
            if ele == "models":
                continue
            return ele
        return ''

    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        """Infer table name from class name."""
        name = cls.__name__
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        name = re.sub('__([A-Z])', r'_\1', name)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
        if cls.__join_application_prefix__ and (
            (application_name := cls._get_model_application_name()) != ""
        ):
            return f'{application_name}_{name.lower()}'
        return name.lower()
