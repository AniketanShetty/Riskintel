"""
Alembic environment configuration — synchronous migration support.

This env.py is configured for the canonical V1 backend (SQLite, sync
SQLAlchemy). For online mode it uses a sync engine against the same
sqlite:// URL that the app's settings expose; offline mode emits
SQL to stdout.

Usage:
    cd backend/
    alembic upgrade head         # Apply migrations
    alembic autogenerate -m "description"   # Generate new migration
"""
from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Use the sync sqlite3 driver; aiosqlite is for the runtime async engine only.
# Imports below are unchanged in spirit; we just remove the now-unused
# async helpers and switch to a sync engine.

# Alembic Config object
config = context.config

# Set up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import the declarative base metadata for autogenerate support
from app.db.base import Base

# Import all models so they are registered with the metadata
from app.models import (  # noqa: F401
    Applicant,
    Assessment,
    RuleRegistry,
    ModelRegistry,
    ArchetypeResult,
    RecommendationResult,
    EligibilityResult,
    RiskTierResult,
    ReadinessResult,
    AuditLog,
)

target_metadata = Base.metadata

# Override sqlalchemy.url from the application settings
from app.core.config import settings

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL_SYNC)


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well.  By skipping the Engine
    creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Helper to run migrations within a connection context.

    `render_as_batch=True` is required for SQLite because ALTER TABLE
    support is limited — Alembic's batch mode recreates the table under
    the hood for any column-add/drop/rename change.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using a synchronous SQLite engine.

    The V1 backend uses a synchronous sqlite3 connection for Alembic. The
    async engine (aiosqlite) is reserved for the FastAPI runtime path
    only — it is not needed during migration.
    """
    configuration = config.get_section(config.config_ini_section, {})
    # Override with the sync URL from settings (sqlite:///...).
    configuration["sqlalchemy.url"] = settings.DATABASE_URL_SYNC

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
