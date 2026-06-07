"""
FastAPI dependency injection.

Provides reusable dependencies for route handlers, including
database sessions and repository injections.
"""
from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an async database session.

    Usage:
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db_session)):
            ...

    The session is automatically closed when the request completes.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
