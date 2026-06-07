"""
Database session management.

Provides the async SQLAlchemy engine and session factory used
throughout the application.  The engine is created once at startup
and disposed during shutdown via the FastAPI lifespan hook.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    echo=settings.DB_ECHO,
    future=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Convenience async context manager for database sessions.
    Prefer using the FastAPI dependency `get_db_session` in route handlers.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
