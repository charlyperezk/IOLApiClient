from contextlib import contextmanager
import importlib
import os
from typing import Callable, Iterator, Optional

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

_SCHEMA_NAME: Optional[str] = "bi"
_METADATA = MetaData()
Base = declarative_base(metadata=_METADATA)

_DEFAULT_POOL_SIZE = 10

_MODEL_MODULES = (
    "src.seedwork.access_token_repo",
    "src.seedwork.repositories",
    "src.meli.scan_run.repositories",
    "src.meli.items.models",
    "src.meli.sellers.models",
    "src.meli.user_products.models",
    "src.meli.orders.models",
)


def _ensure_model_modules_loaded() -> None:
    for module in _MODEL_MODULES:
        importlib.import_module(module)

DATABASE_URL = os.getenv("DATABASE_URL", "")
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL", DATABASE_URL)


def init_database(engine: Engine) -> None:
    _ensure_schema(engine)
    _ensure_model_modules_loaded()
    try:
        Base.metadata.create_all(bind=engine)
    except (OperationalError, ProgrammingError) as exc:
        message = str(exc).lower()
        if "already exists" in message:
            return
        raise


def create_async_engine_instance(url: str = ASYNC_DATABASE_URL) -> AsyncEngine:
    return create_async_engine(
        url,
        poolclass=NullPool,
        future=True,
    )


def create_async_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
        class_=AsyncSession,
    )


def create_engine_instance(url: str = DATABASE_URL) -> Engine:
    return create_engine(
        url,
        pool_size=_DEFAULT_POOL_SIZE,
        max_overflow=0,
        pool_pre_ping=True,
        future=True,
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
        future=True,
    )


def get_async_session(async_session_factory: async_sessionmaker[AsyncSession]) -> AsyncSession:
    return async_session_factory()


def get_session(session_factory: sessionmaker[Session]) -> Session:
    return session_factory()


def set_schema(schema: Optional[str]) -> None:
    global _SCHEMA_NAME
    _SCHEMA_NAME = schema
    _METADATA.schema = schema


def get_schema() -> Optional[str]:
    return _SCHEMA_NAME


def _ensure_schema(engine: Engine) -> None:
    if not _SCHEMA_NAME:
        return
    if engine.dialect.name == "sqlite":
        return
    schema_safe = _SCHEMA_NAME.replace('"', '""')
    statement = text(f'CREATE SCHEMA IF NOT EXISTS "{schema_safe}"')
    try:
        with engine.connect() as connection:
            connection.execute(statement)
            connection.commit()
    except OperationalError as exc:
        message = str(exc).lower()
        if "already exists" in message:
            return
        raise


@contextmanager
def transactional_session(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    session = get_session(session_factory)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
