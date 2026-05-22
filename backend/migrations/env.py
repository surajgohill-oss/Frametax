import asyncio
import os
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import Base
from app.models import *  # noqa

target_metadata = Base.metadata

# Allow env vars to override alembic.ini (for local / non-Docker runs).
# The async engine requires postgresql+asyncpg://; the offline sync runner
# requires plain postgresql://. We build both from whatever env var is set.
_env_url = os.getenv("DATABASE_URL") or os.getenv("DATABASE_SYNC_URL")
if _env_url:
    _async_url = _env_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    _sync_url  = _env_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    config.set_main_option("sqlalchemy.url", _async_url)
    config.set_main_option("sqlalchemy.sync_url", _sync_url)
else:
    _async_url = config.get_main_option("sqlalchemy.url")
    _sync_url  = _async_url.replace("postgresql+asyncpg://", "postgresql://", 1)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine
    connectable = create_async_engine(_async_url, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
