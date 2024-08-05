from sqlalchemy.exc import SQLAlchemyError

"""Module with all sqlalchemy_dev_utils project exceptions.

All exceptions depends on BaseSQLAlchemyDevError. If you work with sqlalchemy_dev_utils and don't
know, what error will be raised, use try-except with BaseDevError.
"""


class BaseSQLAlchemyDevError(SQLAlchemyError):
    """Base exception for all sqlalchemy-dev-utils package exceptions."""


class NoDeclarativeModelError(BaseSQLAlchemyDevError):
    """Exception for Table object, that not mapped to DeclarativeBase model.

    Needs, because non-declarative models are not supported.
    """


class NoModelAttributeError(BaseSQLAlchemyDevError):
    """Exception for incorrect model field name: field not found in given model."""


class NoModelRelationshipError(NoModelAttributeError):
    """Exception for incorrect model relationship name: relationship not found in given model."""
