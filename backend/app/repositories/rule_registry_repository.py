"""
RuleRegistry repository — data access layer for versioned rule configurations.

Extends the generic BaseRepository with domain-specific queries for loading
active rules by engine, retrieving specific versions, and version tracking.

All methods are async and designed to work with the async SQLAlchemy session.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rule_registry import RuleRegistry
from app.repositories.base import BaseRepository


class RuleRegistryRepository(BaseRepository[RuleRegistry]):
    """
    Repository for RuleRegistry operations.

    Provides:
    - Loading active rules by engine_id
    - Retrieving specific rule versions
    - Version history tracking
    - Engine-scoped queries
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, RuleRegistry)

    # ── Active rule queries ───────────────────────────────────────────────

    async def get_active_rules_by_engine(self, engine_id: str) -> List[RuleRegistry]:
        """
        Retrieve all active rules for a given engine.

        Args:
            engine_id: Engine identifier (e.g. "E1", "E2", "E5").

        Returns:
            List of active RuleRegistry records for the engine.

        Raises:
            sqlalchemy.exc.DBAPIError: On database connectivity failure
            (fail-closed — caller must handle).
        """
        stmt = (
            select(RuleRegistry)
            .where(RuleRegistry.engine_id == engine_id)
            .where(RuleRegistry.is_active.is_(True))
            .order_by(RuleRegistry.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_rule(
        self, engine_id: str, rule_name: str,
    ) -> Optional[RuleRegistry]:
        """
        Get a specific active rule by engine_id and rule_name.

        Args:
            engine_id: Engine identifier.
            rule_name: Name of the rule within the engine.

        Returns:
            The active rule record, or None if no active rule matches.
        """
        stmt = (
            select(RuleRegistry)
            .where(RuleRegistry.engine_id == engine_id)
            .where(RuleRegistry.rule_name == rule_name)
            .where(RuleRegistry.is_active.is_(True))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_active_rules(self) -> List[RuleRegistry]:
        """
        Retrieve ALL active rules across every engine.

        Returns:
            List of all active RuleRegistry records.
        """
        stmt = (
            select(RuleRegistry)
            .where(RuleRegistry.is_active.is_(True))
            .order_by(RuleRegistry.engine_id.asc(), RuleRegistry.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ── Version queries ───────────────────────────────────────────────────

    async def get_rule_by_version(
        self, engine_id: str, version: str,
    ) -> Optional[RuleRegistry]:
        """
        Retrieve a specific version of a rule for an engine.

        Uses the unique constraint (engine_id, version) for lookup.

        Args:
            engine_id: Engine identifier.
            version: Semantic version string (e.g. "1.0.0").

        Returns:
            The matching rule record, or None.
        """
        stmt = (
            select(RuleRegistry)
            .where(RuleRegistry.engine_id == engine_id)
            .where(RuleRegistry.version == version)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_versions(self, engine_id: str) -> List[str]:
        """
        List all available version strings for an engine, newest first.

        Args:
            engine_id: Engine identifier.

        Returns:
            Sorted list of version strings.
        """
        stmt = (
            select(RuleRegistry.version)
            .where(RuleRegistry.engine_id == engine_id)
            .order_by(desc(RuleRegistry.created_at))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_version(self, engine_id: str) -> Optional[str]:
        """
        Get the currently active version string for an engine.

        Args:
            engine_id: Engine identifier.

        Returns:
            Version string of the active rule, or None.
        """
        stmt = (
            select(RuleRegistry.version)
            .where(RuleRegistry.engine_id == engine_id)
            .where(RuleRegistry.is_active.is_(True))
            .order_by(desc(RuleRegistry.created_at))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_version_history(
        self, engine_id: str, limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get version history with metadata for an engine.

        Args:
            engine_id: Engine identifier.
            limit: Maximum number of history entries.

        Returns:
            List of dicts with id, version, rule_name, is_active, created_at.
        """
        stmt = (
            select(
                RuleRegistry.id,
                RuleRegistry.version,
                RuleRegistry.rule_name,
                RuleRegistry.is_active,
                RuleRegistry.created_at,
            )
            .where(RuleRegistry.engine_id == engine_id)
            .order_by(desc(RuleRegistry.created_at))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [
            {
                "id": str(row.id),
                "version": row.version,
                "rule_name": row.rule_name,
                "is_active": row.is_active,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in result.all()
        ]

    # ── Mutation helpers ──────────────────────────────────────────────────

    async def activate_version(self, version_id: uuid.UUID) -> Optional[RuleRegistry]:
        """
        Activate a specific rule version by its ID.
        Deactivates all other rules for the same engine.

        Args:
            version_id: UUID of the rule to activate.

        Returns:
            The activated rule record, or None if not found.
        """
        target = await self.get(version_id)
        if target is None:
            return None

        # Deactivate all other active rules for this engine
        deactivate_stmt = (
            select(RuleRegistry)
            .where(RuleRegistry.engine_id == target.engine_id)
            .where(RuleRegistry.is_active.is_(True))
            .where(RuleRegistry.id != version_id)
        )
        result = await self._session.execute(deactivate_stmt)
        for rule in result.scalars().all():
            rule.is_active = False

        # Activate the target
        target.is_active = True
        await self._session.flush()
        await self._session.refresh(target)
        return target
