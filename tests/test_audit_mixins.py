from datetime import UTC, datetime

from sqlalchemy import Date, Time, cast
from sqlalchemy.orm import DeclarativeBase

from sqlalchemy_dev_utils.mixins import audit as audit_mixins
from sqlalchemy_dev_utils.mixins import ids as ids_mixins


class Base(DeclarativeBase): ...  # noqa: D101


class AuditedModel(audit_mixins.AuditMixin, ids_mixins.IntegerIDMixin, Base):  # noqa: D101
    __tablename__ = "audit_model"


now = datetime.now(tz=UTC)


def test_audit_fields() -> None:
    assert str(AuditedModel.created_at_date == 1) == str(cast(AuditedModel.created_at, Date) == 1)
    assert str(AuditedModel.created_at_time == 1) == str(cast(AuditedModel.created_at, Time) == 1)
    assert str(AuditedModel.updated_at_date == 1) == str(cast(AuditedModel.updated_at, Date) == 1)
    assert str(AuditedModel.updated_at_time == 1) == str(cast(AuditedModel.updated_at, Time) == 1)
    instance = AuditedModel(id=1, created_at=now, updated_at=now)
    assert instance.created_at_date == now.date()
    assert instance.updated_at_date == now.date()
    assert instance.created_at_time == now.time()
    assert instance.updated_at_time == now.time()
    assert instance.created_at_isoformat == now.isoformat()
    assert instance.updated_at_isoformat == now.isoformat()
