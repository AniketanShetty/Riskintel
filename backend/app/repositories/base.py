"""
Base repository implementing the generic CRUD pattern.

Provides type-safe async CRUD operations for any SQLAlchemy model.
Specialised repositories extend this class with domain-specific queries.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository with common database operations.

    Usage:
        class ApplicantRepository(BaseRepository[Applicant]):
            ...

        repo = ApplicantRepository(db_session, Applicant)
    """

    def __init__(self, session: AsyncSession, model_class: Type[ModelType]) -> None:
        self._session = session
        self._model = model_class

    async def create(self, **kwargs: Any) -> ModelType:
        """Create and return a new record."""
        instance = self._model(**kwargs)
        self._session.add(instance)
        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    async def get(self, id: uuid.UUID) -> Optional[ModelType]:
        """Retrieve a record by primary key UUID."""
        stmt = select(self._model).where(self._model.id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        descending: bool = False,
    ) -> List[ModelType]:
        """
        Retrieve paginated records with optional filters.

        Args:
            skip: Number of records to skip (offset).
            limit: Maximum number of records to return.
            filters: Column=value dict for WHERE clauses.
            order_by: Column name to sort by.
            descending: Sort descending if True.

        Returns:
            List of model instances.
        """
        stmt = select(self._model)

        if filters:
            for column, value in filters.items():
                col_attr = getattr(self._model, column, None)
                if col_attr is not None:
                    stmt = stmt.where(col_attr == value)

        if order_by:
            col_attr = getattr(self._model, order_by, None)
            if col_attr is not None:
                stmt = stmt.order_by(col_attr.desc() if descending else col_attr.asc())

        stmt = stmt.offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filters."""
        stmt = select(func.count(self._model.id))

        if filters:
            for column, value in filters.items():
                col_attr = getattr(self._model, column, None)
                if col_attr is not None:
                    stmt = stmt.where(col_attr == value)

        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def update(
        self, id: uuid.UUID, **kwargs: Any,
    ) -> Optional[ModelType]:
        """
        Partial update of a record by primary key.

        Only the provided fields are updated.
        Returns the updated instance or None if not found.
        """
        instance = await self.get(id)
        if instance is None:
            return None

        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    async def delete(self, id: uuid.UUID) -> bool:
        """Delete a record by primary key. Returns True if deleted."""
        instance = await self.get(id)
        if instance is None:
            return False

        await self._session.delete(instance)
        await self._session.flush()
        return True

    async def exists(self, id: uuid.UUID) -> bool:
        """Check if a record exists by primary key."""
        stmt = select(self._model.id).where(self._model.id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None
