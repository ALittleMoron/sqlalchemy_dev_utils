"""Mixin module with audit columns of model (created_at, updated_at)."""

import datetime
from functools import partial

from sqlalchemy import Cast, Date, Time, cast
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm.decl_api import declarative_mixin, declared_attr

from sqlalchemy_dev_utils.mixins.base import BaseModelMixin
from sqlalchemy_dev_utils.types.datetime import UTCDateTime, Utcnow


@declarative_mixin
class CreatedAtAuditMixin(BaseModelMixin):
    """Audit mixin with created_at column (datetime)."""

    @declared_attr
    def created_at(cls) -> Mapped[datetime.datetime]:
        """Audit created_at column."""
        return mapped_column(
            UTCDateTime,
            default=partial(datetime.datetime.now, tz=datetime.UTC),
            server_default=Utcnow(),
        )

    @hybrid_property
    def created_at_date(self) -> "datetime.date":  # type: ignore[reportRedeclaration]
        """Date value of created_at datetime field."""
        return self.created_at.date()

    @created_at_date.expression
    @classmethod
    def created_at_date(cls) -> Cast[datetime.date]:
        """Date expression of created_at datetime field."""
        return cast(cls.created_at, Date)

    @hybrid_property
    def created_at_time(self) -> datetime.time:  # type: ignore[reportRedeclaration]
        """Time of created_at datetime field."""
        return self.created_at.time()

    @created_at_time.expression
    @classmethod
    def created_at_time(cls) -> Cast[datetime.time]:
        """Time expression of created_at datetime field."""
        return cast(cls.created_at, Time)

    @property
    def created_at_isoformat(self) -> str:
        """ISO string of created_at datetime field."""
        return self.created_at.isoformat()


@declarative_mixin
class UpdatedAtAuditMixin(BaseModelMixin):
    """Audit mixin with created_at column (datetime)."""

    @declared_attr
    def updated_at(cls) -> Mapped[datetime.datetime]:
        """Audit created_at column."""
        return mapped_column(
            UTCDateTime,
            default=partial(datetime.datetime.now, tz=datetime.UTC),
            onupdate=partial(datetime.datetime.now, tz=datetime.UTC),
            server_default=Utcnow(),
            server_onupdate=Utcnow(),  # type: ignore[reportArgumentType]
        )

    @hybrid_property
    def updated_at_date(self) -> "datetime.date":  # type: ignore[reportRedeclaration]
        """Date value of updated_at datetime field."""
        return self.updated_at.date()

    @updated_at_date.expression
    @classmethod
    def updated_at_date(cls) -> Cast[datetime.date]:
        """Date expression of updated_at datetime field."""
        return cast(cls.updated_at, Date)

    @hybrid_property
    def updated_at_time(self) -> datetime.time:  # type: ignore[reportRedeclaration]
        """Time of updated_at datetime field."""
        return self.updated_at.time()

    @updated_at_time.expression
    @classmethod
    def updated_at_time(cls) -> Cast[datetime.time]:
        """Time expression of updated_at datetime field."""
        return cast(cls.updated_at, Time)

    @property
    def updated_at_isoformat(self) -> str:
        """ISO string of updated_at datetime field."""
        return self.updated_at.isoformat()


@declarative_mixin
class AuditMixin(CreatedAtAuditMixin, UpdatedAtAuditMixin):
    """Full audit mixin with created_at and updated_at columns."""


## triggers


def get_updated_at_ddl_statement(  # pragma: no coverage
    column_name: str = "updated_at",
) -> str:
    """Get updated_at DDL statement."""
    return f"""\
    CREATE OR REPLACE FUNCTION set_updated_at_timestamp()
    RETURNS TRIGGER AS $$
    BEGIN
      NEW.{column_name} = NOW() AT TIME ZONE 'utc';
      RETURN NEW;
    END;
    $$ LANGUAGE 'plpgsql';"""


def get_updated_at_trigger_name(  # pragma: no coverage
    table_name: str,
    column_name: str = "updated_at",
) -> str:
    """Get updated_at trigger name."""
    return f'trigger__updated_at_{table_name}_{column_name}'


def get_updated_at_trigger_query(  # pragma: no coverage
    table_name: str,
    column_name: str = "updated_at",
) -> str:
    """Get updated_at trigger query to make trigger in alembic."""
    trigger_name = get_updated_at_trigger_name(table_name, column_name)
    return f"""\
    CREATE TRIGGER {trigger_name}
      BEFORE UPDATE
      ON {table_name}
      FOR EACH ROW
      EXECUTE PROCEDURE set_updated_at_timestamp();"""


def get_drop_update_at_trigger_query(  # pragma: no coverage
    table_name: str,
    column_name: str = "updated_at",
) -> str:
    """Get drop update_at trigger query to make trigger in alembic."""
    trigger_name = get_updated_at_trigger_name(table_name, column_name)
    return f"DROP TRIGGER IF EXISTS {trigger_name} on {table_name};"
