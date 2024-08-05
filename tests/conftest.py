import asyncio
import os
from contextlib import suppress
from typing import TYPE_CHECKING, Any

import pytest
from mimesis import Datetime, Locale, Text
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import scoped_session, sessionmaker

from sqlalchemy_dev_utils.types.pydantic import json_serializer
from tests.utils import (
    Base,
    MyModel,
    coin_flip,
    create_db,
    create_db_item_sync,
    destroy_db,
)

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy import Engine
    from sqlalchemy.orm import Session

    from tests.types import SyncFactoryFunctionProtocol


true_stmt = {"y", "Y", "yes", "Yes", "t", "true", "True", "1"}
IS_DOCKER_TEST = os.environ.get("IS_DOCKER_TEST", "false") in true_stmt


@pytest.fixture(scope="session")
def event_loop() -> "Generator[asyncio.AbstractEventLoop, None, None]":
    """Event loop fixture."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def db_name() -> str:
    """Db name as fixture."""
    return "sqlalchemy_dev_utils_test_db"


@pytest.fixture(scope="session")
def db_user() -> str:
    """DB user as fixture."""
    return "postgres"


@pytest.fixture(scope="session")
def db_password() -> str:
    """DB password as fixture."""
    return "postgres"


@pytest.fixture(scope="session")
def db_host() -> str:
    """DB host as fixture."""
    return "db" if IS_DOCKER_TEST else "localhost"


@pytest.fixture(scope="session")
def db_port() -> int:
    """DB port as fixture."""
    return 5432


@pytest.fixture(scope="session")
def db_domain(db_name: str, db_user: str, db_password: str, db_host: str, db_port: int) -> str:
    """Domain for test db without specified driver."""
    return f"{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


@pytest.fixture(scope="session")
def db_sync_url(db_domain: str) -> str:
    """URL for test db (will be created in db_engine): sync driver."""
    return f"postgresql://{db_domain}"


@pytest.fixture(scope="session")
def db_async_url(db_domain: str) -> str:
    """URL for test db (will be created in db_engine): async driver."""
    return f"postgresql+asyncpg://{db_domain}"


@pytest.fixture(scope="session", autouse=True)
def db_sync_engine(db_sync_url: str) -> "Generator[Engine, None, None]":
    """SQLAlchemy engine session-based fixture."""
    with suppress(SQLAlchemyError):
        create_db(db_sync_url)
    engine = create_engine(
        db_sync_url,
        echo=False,
        pool_pre_ping=True,
        json_serializer=json_serializer,
    )
    try:
        yield engine
    finally:
        engine.dispose()
        with suppress(SQLAlchemyError):
            destroy_db(db_sync_url)


@pytest.fixture(scope="session")
def db_sync_session_factory(db_sync_engine: "Engine") -> "scoped_session[Session]":
    """SQLAlchemy session factory session-based fixture."""
    return scoped_session(
        sessionmaker(
            bind=db_sync_engine,
            autoflush=False,
            expire_on_commit=False,
        ),
    )


@pytest.fixture()
def db_sync_session(
    db_sync_engine: "Engine",
    db_sync_session_factory: "scoped_session[Session]",
) -> "Generator[Session, None, None]":
    """SQLAlchemy session fixture."""
    Base.metadata.drop_all(db_sync_engine)
    Base.metadata.create_all(db_sync_engine)
    with db_sync_session_factory() as session:
        yield session


@pytest.fixture()
def text_faker() -> Text:
    return Text(locale=Locale.EN)


@pytest.fixture()
def dt_faker() -> Datetime:
    return Datetime(locale=Locale.EN)


@pytest.fixture()
def mymodel_sync_factory(
    dt_faker: Datetime,
    text_faker: Text,
) -> "SyncFactoryFunctionProtocol[MyModel]":
    """Function-factory, that create MyModel instances."""

    def _create(
        session: "Session",
        *,
        commit: bool = False,
        **kwargs: Any,  # noqa: ANN401
    ) -> MyModel:
        params: dict[str, Any] = {
            "name": text_faker.sentence(),
            "other_name": text_faker.sentence(),
            "dt": dt_faker.datetime(),
            "bl": coin_flip(),
        }
        params.update(kwargs)
        return create_db_item_sync(session, MyModel, params, commit=commit)

    return _create
