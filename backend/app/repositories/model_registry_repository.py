"""
ModelRegistry repository — data access layer for versioned ML model artifacts.

Extends the generic BaseRepository with domain-specific queries for loading
active models by engine, retrieving specific versions, and version tracking.

Each row represents a unique (engine_id, model_version) pair. Only one
version per engine may be active at a time.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_registry import ModelRegistry
from app.repositories.base import BaseRepository


class ModelRegistryRepository(BaseRepository[ModelRegistry]):
    """
    Repository for ModelRegistry operations.

    Provides:
    - Loading active models by engine_id
    - Retrieving specific model versions
    - Version history tracking
    - Engine-scoped queries
    - Atomic version activation
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ModelRegistry)

    # ── Active model queries ──────────────────────────────────────────────

    async def get_active_models_by_engine(self, engine_id: str) -> List[ModelRegistry]:
        """
        Retrieve all active model records for a given engine.

        Note: Due to the activation mechanism at most one row should be
        active per engine, but this returns a list for consistency with
        the repository pattern.

        Args:
            engine_id: Engine identifier (e.g. "E3", "E4").

        Returns:
            List of active ModelRegistry records for the engine.
        """
        stmt = (
            select(ModelRegistry)
            .where(ModelRegistry.engine_id == engine_id)
            .where(ModelRegistry.is_active.is_(True))
            .order_by(ModelRegistry.deployed_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_model(self, engine_id: str) -> Optional[ModelRegistry]:
        """
        Get the single active model for an engine.

        Args:
            engine_id: Engine identifier.

        Returns:
            The active model record, or None if no active model.
        """
        stmt = (
            select(ModelRegistry)
            .where(ModelRegistry.engine_id == engine_id)
            .where(ModelRegistry.is_active.is_(True))
            .order_by(ModelRegistry.deployed_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_active_models(self) -> List[ModelRegistry]:
        """
        Retrieve ALL active models across every engine.

        Returns:
            List of all active ModelRegistry records.
        """
        stmt = (
            select(ModelRegistry)
            .where(ModelRegistry.is_active.is_(True))
            .order_by(ModelRegistry.engine_id.asc(), ModelRegistry.deployed_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ── Version queries ───────────────────────────────────────────────────

    async def get_model_by_version(
        self, engine_id: str, model_version: str,
    ) -> Optional[ModelRegistry]:
        """
        Retrieve a specific model version for an engine.

        Uses the unique constraint (engine_id, model_version) for lookup.

        Args:
            engine_id: Engine identifier.
            model_version: Version string (e.g. "2.1.0").

        Returns:
            The matching model record, or None.
        """
        stmt = (
            select(ModelRegistry)
            .where(ModelRegistry.engine_id == engine_id)
            .where(ModelRegistry.model_version == model_version)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_versions(self, engine_id: str) -> List[str]:
        """
        List all available model version strings for an engine, newest first.

        Args:
            engine_id: Engine identifier.

        Returns:
            Sorted list of version strings.
        """
        stmt = (
            select(ModelRegistry.model_version)
            .where(ModelRegistry.engine_id == engine_id)
            .order_by(desc(ModelRegistry.deployed_at))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_version(self, engine_id: str) -> Optional[str]:
        """
        Get the currently active model version string for an engine.

        Args:
            engine_id: Engine identifier.

        Returns:
            Version string of the active model, or None.
        """
        stmt = (
            select(ModelRegistry.model_version)
            .where(ModelRegistry.engine_id == engine_id)
            .where(ModelRegistry.is_active.is_(True))
            .order_by(desc(ModelRegistry.deployed_at))
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
            List of dicts with id, model_version, is_active, artifact_s3_uri,
            training_data_hash, deployed_at.
        """
        stmt = (
            select(
                ModelRegistry.id,
                ModelRegistry.model_version,
                ModelRegistry.is_active,
                ModelRegistry.artifact_s3_uri,
                ModelRegistry.training_data_hash,
                ModelRegistry.deployed_at,
            )
            .where(ModelRegistry.engine_id == engine_id)
            .order_by(desc(ModelRegistry.deployed_at))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [
            {
                "id": str(row.id),
                "model_version": row.model_version,
                "is_active": row.is_active,
                "artifact_s3_uri": row.artifact_s3_uri,
                "training_data_hash": row.training_data_hash,
                "deployed_at": row.deployed_at.isoformat() if row.deployed_at else None,
            }
            for row in result.all()
        ]

    # ── Artifact queries ──────────────────────────────────────────────────

    async def get_artifact_uri(self, engine_id: str) -> Optional[str]:
        """
        Get the artifact S3 URI for the active model of an engine.

        Args:
            engine_id: Engine identifier.

        Returns:
            S3 URI string, or None if no active model.
        """
        stmt = (
            select(ModelRegistry.artifact_s3_uri)
            .where(ModelRegistry.engine_id == engine_id)
            .where(ModelRegistry.is_active.is_(True))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_training_data_hash(self, engine_id: str) -> Optional[str]:
        """
        Get the training data SHA256 hash for the active model of an engine.

        Args:
            engine_id: Engine identifier.

        Returns:
            Hash string, or None if no active model.
        """
        stmt = (
            select(ModelRegistry.training_data_hash)
            .where(ModelRegistry.engine_id == engine_id)
            .where(ModelRegistry.is_active.is_(True))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # ── Mutation helpers ──────────────────────────────────────────────────

    async def activate_version(self, version_id: uuid.UUID) -> Optional[ModelRegistry]:
        """
        Activate a specific model version by its ID.

        Deactivates all other models for the same engine, then activates
        the target version. This ensures exactly one active version per engine.

        Args:
            version_id: UUID of the model version to activate.

        Returns:
            The activated model record, or None if not found.
        """
        target = await self.get(version_id)
        if target is None:
            return None

        # Deactivate all other active models for this engine
        deactivate_stmt = (
            select(ModelRegistry)
            .where(ModelRegistry.engine_id == target.engine_id)
            .where(ModelRegistry.is_active.is_(True))
            .where(ModelRegistry.id != version_id)
        )
        result = await self._session.execute(deactivate_stmt)
        for model in result.scalars().all():
            model.is_active = False

        # Activate the target
        target.is_active = True
        await self._session.flush()
        await self._session.refresh(target)
        return target
