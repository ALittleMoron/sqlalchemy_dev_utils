from sqlalchemy.orm import DeclarativeBase

from sqlalchemy_dev_utils.mixins import ids as ids_mixins


class Base(DeclarativeBase): ...  # noqa: D101


def test_ids() -> None:
    class CorrectIntegerIdMixinUseCase(ids_mixins.IntegerIDMixin, Base):  # type: ignore[reportUnusedClass]
        __tablename__ = "correct_abc_1"

    class CorrectUUIDMixinUseCase(ids_mixins.UUIDMixin, Base):  # type: ignore[reportUnusedClass]
        __tablename__ = "correct_abc_2"
