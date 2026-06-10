"""
VendorOS - Alembic Migration Environment
Configures async migrations using SQLAlchemy 2.x + asyncpg.
"""

import asyncio
from logging.config import fileConfig
from typing import Optional

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ── Import all models so Alembic can detect changes ───────────────────────────
# This single import pulls in every ORM model via models/__init__.py
import app.models  # noqa: F401  (side-effect: registers all metadata)
from app.database.connection import Base
from app.core.config import settings

# Alembic Config object
config = context.config

# Override sqlalchemy.url with the value from our Settings (supports .env)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file's logging section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata object for autogenerate support
target_metadata = Base.metadata


# ── Offline migrations (no live DB connection) ────────────────────────────────

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode (generates SQL script without a
    live database connection).
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ── Online migrations (live async DB connection) ──────────────────────────────

def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations against a live async database connection."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online (async) migrations."""
    asyncio.run(run_async_migrations())


# ── Dispatch ──────────────────────────────────────────────────────────────────

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()