import subprocess
import sys

from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session

from sqlalchemy_dev_utils.mixins.audit import AuditMixin
from sqlalchemy_dev_utils.mixins.general import (
    BetterReprMixin,
    DictConverterMixin,
    DifferenceMixin,
    TableNameMixin,
)
from sqlalchemy_dev_utils.mixins.ids import IntegerIDMixin, UUIDMixin


def test_mixin_imports_without_sqlalchemy_deprecations() -> None:
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import warnings; "
            "from sqlalchemy.exc import SADeprecationWarning; "
            "warnings.simplefilter('error', SADeprecationWarning); "
            "import sqlalchemy_dev_utils.mixins.base; "
            "import sqlalchemy_dev_utils.mixins.audit; "
            "import sqlalchemy_dev_utils.mixins.general; "
            "import sqlalchemy_dev_utils.mixins.ids",
        ],
        check=True,
    )


def test_mapped_mixins_preserve_columns_defaults_and_helpers() -> None:
    class Base(DeclarativeBase):
        pass

    class CompatibleModel(
        AuditMixin,
        BetterReprMixin,
        DictConverterMixin,
        DifferenceMixin,
        TableNameMixin,
        IntegerIDMixin,
        Base,
    ):
        name: Mapped[str]

    class UUIDModel(TableNameMixin, UUIDMixin, Base):
        name: Mapped[str]

    engine = create_engine("sqlite://")
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            instance = CompatibleModel(name="first")
            uuid_instance = UUIDModel(name="uuid")
            session.add_all([instance, uuid_instance])
            session.flush()
            original_id = instance.id
            original_created_at = instance.created_at
            original_updated_at = instance.updated_at
            uuid_id = uuid_instance.id
            assert instance.pk == original_id
            assert uuid_instance.pk == uuid_id
            assert uuid_id is not None
            instance.name = "second"
            session.flush()
            session.expire_all()
            loaded = session.scalar(select(CompatibleModel))
            assert loaded is not None
            assert loaded.pk == original_id
            assert loaded.created_at == original_created_at
            assert loaded.updated_at >= original_updated_at
            assert loaded.created_at_isoformat == original_created_at.isoformat()
            assert loaded.as_dict()["name"] == "second"
            assert loaded.is_different_from({"name": "second"}) is False
            assert loaded.is_different_from({"name": "other"}) is True
            assert "name='second'" in repr(loaded)
            loaded_uuid = session.scalar(select(UUIDModel))
            assert loaded_uuid is not None
            assert loaded_uuid.pk == uuid_id
            assert inspect(CompatibleModel).local_table.name == "compatible_model"
    finally:
        engine.dispose()
