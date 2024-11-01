"""Utils module of sqlalchemy dev package.

Contains functions, which inspect models, apply joins, apply options and wrap some sqlalchemy
functionality.
"""

import types
from inspect import isclass
from typing import TYPE_CHECKING, Any, Literal, TypeGuard, TypeVar, overload
from warnings import warn

from sqlalchemy import Delete, Insert, Select, Table, Update, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.hybrid import HybridExtensionType
from sqlalchemy.orm import DeclarativeBase, joinedload

from sqlalchemy_dev_utils.exc import (
    NoDeclarativeModelError,
    NoModelAttributeError,
    NoModelRelationshipError,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from sqlalchemy.orm import InstrumentedAttribute, Mapper, QueryableAttribute
    from sqlalchemy.orm.base import InspectionAttr
    from sqlalchemy.orm.clsregistry import _ClsRegistryType  # type: ignore[reportPrivateUsage]
    from sqlalchemy.orm.strategy_options import _AbstractLoad  # type: ignore[reportPrivateUsage]

    T = TypeVar("T", bound=Select[Any])

Statement = (
    Select[tuple["DeclarativeBase"]]
    | Update["DeclarativeBase"]
    | Delete["DeclarativeBase"]
    | Insert["DeclarativeBase"]
)


def is_declarative_entity(model: Any) -> TypeGuard["DeclarativeBase"]:  # noqa: ANN401
    """Check given value to be DeclarativeBase entity/instance or not.

    Args
    ----
    model : Any object.

    Returns
    -------
    Type guard result of DeclarativeBase class.
    """
    try:
        mapper: "Mapper[Any]" = inspect(model)
    except SQLAlchemyError:
        return False
    else:
        if not hasattr(mapper, "is_mapper"):
            return False
        return not isclass(model) and not mapper.is_mapper


def is_declarative_class(model: Any) -> TypeGuard["type[DeclarativeBase]"]:  # noqa: ANN401
    """Check given value to be DeclarativeBase class or not.

    Args
    ----
    model : Any object.

    Returns
    -------
    Type guard result of DeclarativeBase class.
    """
    try:
        mapper: "Mapper[Any]" = inspect(model)
    except SQLAlchemyError:
        return False
    else:
        if not hasattr(mapper, "is_mapper"):
            return False
        return isclass(model) and mapper.is_mapper


def get_unloaded_fields(instance: "DeclarativeBase") -> set[str]:
    """Get unloaded fields from instance.

    Args
    ----
    instance : DeclarativeBase
        SQLAlchemy declarative model instance.

    Returns
    -------
    set[str]
        set of instance fields, which were not loaded.
    """
    inspector = inspect(instance)
    return inspector.unloaded


def get_model_instance_data_as_dict(
    instance: "DeclarativeBase",
    exclude: set[str] | None = None,
) -> dict[str, Any]:
    """Get SQLAlchemy model instance data as dict.

    Args
    ----
    instance : DeclarativeBase
        SQLAlchemy declarative model instance.
    exclude : set[str] | None (default None)
        set of string fields, which must be excluded from return result.

    Returns
    -------
    dict[str, Any]
        dict of instance fields with values, but without fields, which were not loaded or excluded.
    """
    if exclude is None:
        exclude = set()
    exclude = exclude.union(get_unloaded_fields(instance))
    return {
        col.name: getattr(instance, col.name)
        for col in instance.__table__.columns
        if col.name not in exclude
    }


@overload
def get_sqlalchemy_attribute(
    model: type["DeclarativeBase"],
    field_name: str,
    *,
    only_columns: Literal[True],
) -> "InstrumentedAttribute[Any]": ...


@overload
def get_sqlalchemy_attribute(
    model: type["DeclarativeBase"],
    field_name: str,
    *,
    only_columns: Literal[False] = False,
) -> "QueryableAttribute[Any]": ...


def get_sqlalchemy_attribute(
    model: type["DeclarativeBase"],
    field_name: str,
    *,
    only_columns: bool = False,
) -> "QueryableAttribute[Any]":
    """Get sqlalchemy field (column) or relationship object from given model.

    Args
    ----
    model : type[DeclarativeBase]
        SQLAlchemy declarative model.
    field_name : str
        name of field to find in model.
    only_columns: bool
        get attribute only from columns.

    Returns
    -------
    QueryableAttribute[Any]
        any attribute from model, that can be used in queries.
    """
    if only_columns:
        valid_attributes = get_valid_field_names(model)
    else:
        valid_attributes = get_all_valid_queryable_attributes(model)
    if field_name not in valid_attributes:
        valid_field = ", ".join(valid_attributes)
        msg = (
            f'No sqlalchemy attribute "{field_name}" was found in model "{model}". '
            f"Valid attributes for {model}: {valid_field}"
        )
        raise NoModelAttributeError(msg)
    sqlalchemy_field = getattr(model, field_name)
    if isinstance(sqlalchemy_field, types.MethodType):
        sqlalchemy_field = sqlalchemy_field()
    return sqlalchemy_field


def get_model_classes_from_statement(stmt: Statement) -> "Sequence[type[DeclarativeBase]]":
    """Get sqlalchemy model classes from given statement.

    Args
    ----
    stmt : Statement
        SQLAlchemy statement (select, update, delete, insert).

    Returns
    -------
    Sequence['DeclarativeBase']
        sequence of model classes.
    """
    if isinstance(stmt, Select):
        model_classes = [
            col_desc["entity"] for col_desc in stmt.column_descriptions if col_desc["entity"]
        ]
        for _from_clause in stmt._from_obj:  # type: ignore[reportPrivateUsage]  # noqa: SLF001
            if not isinstance(_from_clause, Table):
                msg = "From clause without table binding was found and skipped for statement."
                warn(msg, stacklevel=1)
                continue
            if not is_declarative_class(_from_clause.entity_namespace):  # pragma: no cover
                msg = (
                    f'Table with name "{_from_clause.name}" without Declarative model mapped '
                    "class was found and skipped. Use declarative models."
                )
                warn(msg, stacklevel=1)
                raise NoDeclarativeModelError(msg)
            model_classes.append(_from_clause.entity_namespace)
        return list(set(model_classes))
    return [stmt.entity_description["entity"]]


def get_registry_class(model: type["DeclarativeBase"]) -> "_ClsRegistryType":
    """Get sqlalchemy registry class from any model.

    Args
    ----
    model : type[DeclarativeBase]
        SQLAlchemy declarative model.

    Returns
    -------
    _ClsRegistryType
        SQLAlchemy registry of all models and other specific objects.
    """
    return model.registry._class_registry  # type: ignore[reportPrivateUsage]  # noqa: SLF001


def get_model_class_by_tablename(
    registry: "_ClsRegistryType",
    tablename: str,
) -> type["DeclarativeBase"] | None:
    """Return class reference mapped to table.

    Args
    ----
    registry : _ClsRegistryType
        SQLAlchemy registry of all models and other specific objects.
    name : str
        name of model to find in registry.

    Returns
    -------
    Class reference or None.
    """
    for c in registry.values():
        if getattr(c, "__tablename__", None) == tablename:
            return c  # type: ignore[reportReturnType]
    return None


def get_model_class_by_name(
    registry: "_ClsRegistryType",
    name: str,
) -> type["DeclarativeBase"] | None:
    """Return the model class matching `name` in the given `registry`.

    Args
    ----
    registry : _ClsRegistryType
        SQLAlchemy registry of all models and other specific objects.
    name : str
        name of model to find in registry.

    Returns
    -------
    type['DeclarativeBase'] | None
        Optional model class.
    """
    for cls in registry.values():
        if getattr(cls, "__name__", None) == name:
            return cls  # type: ignore[reportReturnType]
    return None


def get_valid_model_class_names(registry: "_ClsRegistryType") -> set[str]:
    """Get sqlalchemy model names as strings from given registry.

    Args
    ----
    registry : _ClsRegistryType
        SQLAlchemy registry of all models and other specific objects.

    Returns
    -------
    set[str]
        set of model names as strings.
    """
    return set(
        filter(
            None,
            (getattr(ele, "__name__", None) for ele in registry.values()),
        ),
    )


def get_valid_relationships_names(model: type["DeclarativeBase"]) -> set[str]:
    """Get sqlalchemy relationship names as strings from given model.

    Args
    ----
    model : type[DeclarativeBase]
        SQLAlchemy declarative model.

    Returns
    -------
    set[str]
        set of model relationships as strings.
    """
    return set(inspect(model).relationships.keys())


def get_valid_field_names(
    model: type["DeclarativeBase"],
    *,
    only_columns: bool = False,
) -> set[str]:
    """Get sqlalchemy field names as strings from given model.

    It includes hybrid properties and hybrid methods, because they can be used in queries.

    Args
    ----
    model : type[DeclarativeBase]
        SQLAlchemy declarative model.
    only_columns : bool (Default False)

    Returns
    -------
    set[str]
        set of model fields as strings.
    """
    inspect_mapper: "Mapper[Any]" = inspect(model)
    columns = inspect_mapper.columns
    orm_descriptors = inspect_mapper.all_orm_descriptors

    column_names = columns.keys()
    if only_columns:
        return set(column_names)
    hybrid_names = [
        key
        for key, item in orm_descriptors.items()
        if is_hybrid_property(item) or is_hybrid_method(item)
    ]

    return set(column_names) | set(hybrid_names)


def get_all_valid_queryable_attributes(model: type["DeclarativeBase"]) -> set[str]:
    """Get sqlalchemy field names and relationships as strings from given model.

    It includes hybrid properties and hybrid methods, because they can be used in queries.

    Args
    ----
    model : type[DeclarativeBase]
        SQLAlchemy declarative model.

    Returns
    -------
    set[str]
        set of model fields and relationships as strings.
    """
    return get_valid_relationships_names(model) | get_valid_field_names(model)


def get_related_models(model: type["DeclarativeBase"]) -> list[type["DeclarativeBase"]]:
    """Get sqlalchemy models from model relationships.

    Args
    ----
    model : type[DeclarativeBase]
        SQLAlchemy declarative model.

    Returns
    -------
    list[DeclarativeBase]
        list of related models.
    """
    inspect_mapper: "Mapper[Any]" = inspect(model)
    return [_relationship.mapper.class_ for _relationship in inspect_mapper.relationships]


def is_hybrid_property(orm_descriptor: "InspectionAttr") -> bool:
    """Check, if given field inspected object is hybrid property or not.

    Args
    ----
    orm_descriptor: InspectionAttr
        SQLAlchemy field inspected object.

    Returns
    -------
    bool
        is field a hybrid property or not?
    """
    return orm_descriptor.extension_type == HybridExtensionType.HYBRID_PROPERTY


def is_hybrid_method(orm_descriptor: "InspectionAttr") -> bool:
    """Check, if given field inspected object is hybrid method or not.

    Args
    ----
    orm_descriptor: InspectionAttr
        SQLAlchemy field inspected object.

    Returns
    -------
    bool
        is field a hybrid method or not?
    """
    return orm_descriptor.extension_type == HybridExtensionType.HYBRID_METHOD


def apply_loads(
    stmt: "T",
    *relationship_names: str,
    load_strategy: "Callable[[Any], _AbstractLoad]" = joinedload,
) -> "T":
    """Apply loads from string.

    String joins should represent relations, not model classes.

    Args
    ----
    stmt : TypeVar (Statement)
        select statement instance.
    *relationship_names : str
        any relationship names of model.
    load_strategy : Callable
        any callable, that will return Load object.

    Returns
    -------
    stmt : TypeVar (Statement)
        select statement instance with applied joins.
    """
    model_classes = get_model_classes_from_statement(stmt)
    loaders: list["_AbstractLoad"] = []
    for relationship_ in relationship_names:
        sqlalchemy_relationship = None
        for model_ in model_classes:
            if relationship_ in get_valid_relationships_names(model_):
                sqlalchemy_relationship = get_sqlalchemy_attribute(model_, relationship_)
        if not sqlalchemy_relationship:
            msg = (
                f'SQLAlchemy relationship "{relationship_}" was not found in {model_classes}. '
                "Maybe you passed incorrect relationship name or passed model name."
            )
            warn(msg, stacklevel=1)
            # TODO: add all available relationships or nearest (fuzzy search) in message.  # noqa: E501, FIX002, TD002, TD003
            raise NoModelRelationshipError(msg)
        load = load_strategy(sqlalchemy_relationship)
        loaders.append(load)
    return stmt.options(*loaders)


def apply_joins(
    stmt: "T",
    *relationship_names: str,
    left_outer_join: bool = False,
    full_join: bool = False,
) -> "T":
    """Apply joins from string.

    String joins should represent relations, not model classes.

    Args
    ----
    stmt : TypeVar (Statement)
        select statement instance.
    *relationship_names : str
        any relationship names of model.
    left_outer_join : bool (False)
        use LEFT OUTER JOIN.
    full_join : bool (False)
        use FULL JOIN.

    Returns
    -------
    stmt : TypeVar (Statement)
        select statement instance with applied joins.
    """
    model_classes = get_model_classes_from_statement(stmt)
    model_to_valid_relationship_names = {
        model_: get_valid_relationships_names(model_) for model_ in model_classes
    }
    for relationship_ in relationship_names:
        sqlalchemy_relationship = None
        for model_ in model_classes:
            valid_relationships_names = model_to_valid_relationship_names[model_]
            if relationship_ in valid_relationships_names:
                sqlalchemy_relationship = get_sqlalchemy_attribute(model_, relationship_)
        if not sqlalchemy_relationship:
            msg = (
                f'SQLAlchemy relationship "{relationship_}" was not found in {model_classes}. '
                "Maybe you passed incorrect relationship name or passed model name."
            )
            warn(msg, stacklevel=1)
            # TODO: add all available relationships or nearest (fuzzy search) in message.  # noqa: E501, FIX002, TD002, TD003
            raise NoModelRelationshipError(msg)
        stmt = stmt.join(
            sqlalchemy_relationship,
            isouter=left_outer_join,
            full=full_join,
        )
    return stmt
