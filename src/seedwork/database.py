from contextlib import contextmanager
import importlib
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
from .settings import MODEL_MODULES, DB_SCHEMA, DATABASE_URL, ASYNC_DATABASE_URL

_SCHEMA_NAME: Optional[str] = DB_SCHEMA
_METADATA = MetaData(schema=DB_SCHEMA)
Base = declarative_base(metadata=_METADATA)

def _ensure_model_modules_loaded() -> None:
    for module in MODEL_MODULES:
        try:
            importlib.import_module(module)
        except ModuleNotFoundError as exc:
            if exc.name == module:
                continue
            raise

_SYNC_ENGINE: Optional[Engine] = None
_ASYNC_ENGINE: Optional[AsyncEngine] = None
_SESSION_FACTORY: Optional[sessionmaker[Session]] = None
_ASYNC_SESSION_FACTORY: Optional[async_sessionmaker[AsyncSession]] = None


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


def get_engine() -> Engine:
    global _SYNC_ENGINE
    if _SYNC_ENGINE is None:
        _SYNC_ENGINE = create_engine_instance(DATABASE_URL)
        init_database(_SYNC_ENGINE)
    return _SYNC_ENGINE


def get_async_engine() -> AsyncEngine:
    global _ASYNC_ENGINE
    if _ASYNC_ENGINE is None:
        _ASYNC_ENGINE = create_async_engine_instance(ASYNC_DATABASE_URL)
    return _ASYNC_ENGINE


def get_session_factory() -> sessionmaker[Session]:
    global _SESSION_FACTORY
    if _SESSION_FACTORY is None:
        _SESSION_FACTORY = create_session_factory(get_engine())
    return _SESSION_FACTORY


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    global _ASYNC_SESSION_FACTORY
    if _ASYNC_SESSION_FACTORY is None:
        _ASYNC_SESSION_FACTORY = create_async_session_factory(get_async_engine())
    return _ASYNC_SESSION_FACTORY


async def init_database_async(engine: AsyncEngine) -> None:
    await _ensure_schema_async(engine)
    _ensure_model_modules_loaded()
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
    except (OperationalError, ProgrammingError) as exc:
        message = str(exc).lower()
        if "already exists" in message:
            return
        raise


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


async def _ensure_schema_async(engine: AsyncEngine) -> None:
    if not _SCHEMA_NAME:
        return
    if engine.dialect.name == "sqlite":
        return
    schema_safe = _SCHEMA_NAME.replace('"', '""')
    statement = text(f'CREATE SCHEMA IF NOT EXISTS "{schema_safe}"')
    try:
        async with engine.begin() as connection:
            await connection.execute(statement)
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
