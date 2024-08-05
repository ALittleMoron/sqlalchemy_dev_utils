import uuid

from sqlalchemy import UUID, BigInteger, Integer
from sqlalchemy.orm import Mapped, mapped_column, synonym
from sqlalchemy.orm.decl_api import declarative_mixin, declared_attr

from sqlalchemy_dev_utils.mixins.base import BaseModelMixin


@declarative_mixin
class IntegerIDMixin(BaseModelMixin):
    """Integer primary key field (id) mixin."""

    @declared_attr
    def id(cls) -> Mapped[int]:
        """Id field."""
        return mapped_column(
            BigInteger().with_variant(Integer, "sqlite"),
            nullable=False,
            unique=True,
            primary_key=True,
            autoincrement=True,
        )

    @declared_attr
    def pk(cls) -> Mapped[int]:
        """Synonym for id field."""
        return synonym("id")


@declarative_mixin
class UUIDMixin(BaseModelMixin):
    """UUID primary key field (id) mixin."""

    @declared_attr
    def id(cls) -> Mapped[uuid.UUID]:
        """Id field."""
        return mapped_column(
            UUID(as_uuid=True),
            nullable=False,
            primary_key=True,
            default=uuid.uuid4,
        )

    @declared_attr
    def pk(cls) -> Mapped[uuid.UUID]:
        """Synonym for id field."""
        return synonym("id")
