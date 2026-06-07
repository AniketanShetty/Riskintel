"""
ModelRegistry service — cached, integrity-checked model metadata resolution.

Provides:
- In-memory cache of active model metadata with configurable TTL
- Automatic cache refresh on expiry
- Active model lookup by engine_id
- Artifact URI retrieval for model loading
- Training data hash retrieval for lineage tracking
- SHA256 integrity validation of local model files against registry
- Version management and reporting
- Fail-closed: raises ModelRegistryError on DB failure

Architecture:
    ModelRegistryService
        ├── get_active_model(engine_id)    → Cached active model record
        ├── get_artifact_uri(engine_id)     → S3 URI for model loading
        ├── get_training_data_hash(engine_id) → SHA256 for lineage
        ├── validate_model_integrity(engine_id, filepath) → bool
        ├── get_active_version(engine_id)   → Active version string
        ├── get_model_by_version(engine_id, version) → Specific version
        ├── refresh(engine_id)              → Force cache refresh
        ├── refresh_all()                   → Refresh all engines
        ├── get_cache_stats()               → Diagnostics
        └── _load_from_db()                 → Fail-closed DB load
"""
from __future__ import annotations

import hashlib
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.models.model_registry import ModelRegistry
from app.repositories.model_registry_repository import ModelRegistryRepository

logger = logging.getLogger(__name__)


# ── Custom exception (fail-closed) ─────────────────────────────────────────


class ModelRegistryError(Exception):
    """
    Raised when the Model Registry service cannot load model metadata.

    This is the fail-closed mechanism: if the database is unreachable or
    returns corrupt data, the service raises instead of returning stale
    or empty results that could cause incorrect assessments.
    """

    def __init__(self, message: str, engine_id: Optional[str] = None) -> None:
        super().__init__(message)
        self.engine_id = engine_id


# ── Integrity validation error ─────────────────────────────────────────────


class ModelIntegrityError(ModelRegistryError):
    """
    Raised when a local model file fails SHA256 integrity validation.
    """

    def __init__(
        self,
        message: str,
        engine_id: str,
        model_version: str,
        expected_hash: str,
        actual_hash: str,
    ) -> None:
        super().__init__(message, engine_id=engine_id)
        self.model_version = model_version
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash


# ── Cache entry ────────────────────────────────────────────────────────────


@dataclass
class CacheEntry:
    """A single cache entry with model metadata and expiry."""

    model: Optional[ModelRegistry]
    loaded_at: float  # time.monotonic()
    ttl_seconds: float

    @property
    def is_expired(self) -> bool:
        """Return True if this cache entry has exceeded its TTL."""
        return (time.monotonic() - self.loaded_at) > self.ttl_seconds


# ── Service ────────────────────────────────────────────────────────────────


class ModelRegistryService:
    """
    Cached, fail-closed model registry service with integrity validation.

    Usage:
        service = ModelRegistryService(session_factory, default_ttl=300)
        model = await service.get_active_model("E3")
        uri = await service.get_artifact_uri("E3")
        ok = await service.validate_model_integrity("E3", "/path/to/model.pkl")

    The service caches the active model per engine in memory. On cache miss
    or TTL expiry, it reloads from the database. If the database call fails,
    it raises ``ModelRegistryError`` rather than returning stale data.
    """

    def __init__(
        self,
        session_factory: Any,
        default_ttl: float = 300.0,
    ) -> None:
        """
        Args:
            session_factory: Callable that returns an AsyncSession.
                Typically ``async_session_factory`` from ``app.db.session``.
            default_ttl: Cache TTL in seconds (default 5 minutes).
        """
        self._session_factory = session_factory
        self._default_ttl = default_ttl

        # engine_id -> CacheEntry
        self._cache: Dict[str, CacheEntry] = {}

        # Track which engine_ids have been seen (for refresh_all)
        self._known_engines: set = set()

    # ── Public API ─────────────────────────────────────────────────────────

    async def get_active_model(self, engine_id: str) -> Optional[ModelRegistry]:
        """
        Retrieve the active model for an engine, using cache if fresh.

        Args:
            engine_id: Engine identifier (e.g. "E3", "E4").

        Returns:
            The active ModelRegistry record, or None if none active.

        Raises:
            ModelRegistryError: If the database is unreachable (fail-closed).
        """
        entry = await self._get_or_load(engine_id)
        return entry.model

    async def get_artifact_uri(self, engine_id: str) -> Optional[str]:
        """
        Get the artifact S3 URI for the active model of an engine.

        This is the primary method used by engine loaders to locate
        the model file for deserialization.

        Args:
            engine_id: Engine identifier.

        Returns:
            S3 URI string, or None if no active model.
        """
        model = await self.get_active_model(engine_id)
        return model.artifact_s3_uri if model is not None else None

    async def get_training_data_hash(self, engine_id: str) -> Optional[str]:
        """
        Get the training data SHA256 hash for the active model.

        This hash links a deployed model back to the exact training
        dataset version used, satisfying audit lineage requirements.

        Args:
            engine_id: Engine identifier.

        Returns:
            Hash string, or None if no active model.
        """
        model = await self.get_active_model(engine_id)
        return model.training_data_hash if model is not None else None

    async def get_active_version(self, engine_id: str) -> Optional[str]:
        """
        Get the currently active model version string for an engine.

        Args:
            engine_id: Engine identifier.

        Returns:
            Version string (e.g. "2.1.0"), or None if no active model.
        """
        model = await self.get_active_model(engine_id)
        return model.model_version if model is not None else None

    async def get_model_by_version(
        self, engine_id: str, model_version: str,
    ) -> Optional[ModelRegistry]:
        """
        Retrieve a specific model version (bypassing cache).

        Unlike get_active_model, this does not use the cache because
        the requested version may differ from the active one.

        Args:
            engine_id: Engine identifier.
            model_version: Version string.

        Returns:
            The matching model record, or None.
        """
        try:
            async with self._session_factory() as session:
                repo = ModelRegistryRepository(session)
                return await repo.get_model_by_version(engine_id, model_version)
        except Exception as exc:
            logger.error(
                "Fail-closed: failed to load model version %s for engine '%s': %s",
                model_version, engine_id, exc,
            )
            raise ModelRegistryError(
                f"Failed to load model version '{model_version}' for "
                f"engine '{engine_id}': {exc}",
                engine_id=engine_id,
            ) from exc

    # ── Integrity validation ──────────────────────────────────────────────

    async def validate_model_integrity(
        self, engine_id: str, filepath: str,
    ) -> bool:
        """
        Validate the SHA256 hash of a local model file against the registry.

        This is called BEFORE loading a model into memory to ensure the
        artifact on disk matches what the registry expects. If the file
        is missing, corrupted, or tampered with, the validation fails and
        a ``ModelIntegrityError`` is raised.

        Args:
            engine_id: Engine identifier.
            filepath: Path to the local model artifact file.

        Returns:
            True if the hash matches.

        Raises:
            ModelIntegrityError: If the file is missing or hash mismatch.
            ModelRegistryError: If the active model cannot be loaded from DB.
        """
        model = await self.get_active_model(engine_id)

        if model is None:
            raise ModelRegistryError(
                f"No active model found for engine '{engine_id}'. "
                f"Cannot validate integrity.",
                engine_id=engine_id,
            )

        expected_hash = model.training_data_hash

        # Compute SHA256 of the local file
        if not os.path.exists(filepath):
            raise ModelIntegrityError(
                f"Model file not found at '{filepath}' for engine '{engine_id}'.",
                engine_id=engine_id,
                model_version=model.model_version,
                expected_hash=expected_hash,
                actual_hash="file_not_found",
            )

        try:
            sha256 = hashlib.sha256()
            with open(filepath, "rb") as f:
                while chunk := f.read(65536):  # 64KB chunks
                    sha256.update(chunk)
            actual_hash = f"sha256:{sha256.hexdigest()}"
        except Exception as exc:
            raise ModelIntegrityError(
                f"Failed to compute SHA256 for '{filepath}': {exc}",
                engine_id=engine_id,
                model_version=model.model_version,
                expected_hash=expected_hash,
                actual_hash="computation_error",
            ) from exc

        if actual_hash != expected_hash:
            raise ModelIntegrityError(
                f"SHA256 mismatch for engine '{engine_id}' version "
                f"{model.model_version}. Expected {expected_hash}, "
                f"got {actual_hash}. The model file may be corrupted "
                f"or tampered with.",
                engine_id=engine_id,
                model_version=model.model_version,
                expected_hash=expected_hash,
                actual_hash=actual_hash,
            )

        logger.info(
            "Integrity check passed for engine '%s' version %s — %s",
            engine_id, model.model_version, filepath,
        )
        return True

    # ── Version info ──────────────────────────────────────────────────────

    async def get_version_info(
        self, engine_id: str,
    ) -> Dict[str, Any]:
        """
        Get detailed version info for an engine.

        Returns:
            Dict with:
                engine_id
                active_version
                artifact_uri
                training_data_hash
                cached (bool)
                cache_age_seconds (float)
        """
        entry = self._cache.get(engine_id)
        cached = entry is not None and not entry.is_expired

        if cached and entry is not None and entry.model is not None:
            model = entry.model
            cache_age = time.monotonic() - entry.loaded_at
        else:
            # Load fresh from DB (bypass cache)
            try:
                async with self._session_factory() as session:
                    repo = ModelRegistryRepository(session)
                    model = await repo.get_active_model(engine_id)
            except Exception:
                model = None
            cache_age = 0.0

        return {
            "engine_id": engine_id,
            "active_version": model.model_version if model else None,
            "artifact_uri": model.artifact_s3_uri if model else None,
            "training_data_hash": model.training_data_hash if model else None,
            "cached": cached,
            "cache_age_seconds": round(cache_age, 2),
        }

    # ── Cache management ──────────────────────────────────────────────────

    async def refresh(self, engine_id: str) -> None:
        """
        Force a cache refresh for a specific engine.

        This is called explicitly when models are updated (e.g. after
        a deployment) to avoid waiting for TTL expiry.

        Raises:
            ModelRegistryError: If DB unreachable.
        """
        model = await self._load_from_db(engine_id)
        self._set_cache(engine_id, model)
        version = model.model_version if model else None
        logger.info(
            "Cache refreshed for engine '%s' — version %s.",
            engine_id, version,
        )

    async def refresh_all(self) -> Dict[str, Optional[str]]:
        """
        Refresh the cache for all known engines.

        Returns:
            Dict of engine_id -> active_version for refreshed engines.
        """
        results: Dict[str, Optional[str]] = {}
        for engine_id in list(self._known_engines):
            try:
                await self.refresh(engine_id)
                entry = self._cache.get(engine_id)
                results[engine_id] = (
                    entry.model.model_version if entry and entry.model else None
                )
            except ModelRegistryError:
                logger.warning(
                    "refresh_all: engine '%s' unreachable, skipping.", engine_id,
                )
        return results

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get diagnostic cache statistics.

        Returns:
            Dict with total_engines, engines list, and per-engine stats.
        """
        engines = {}
        for engine_id, entry in self._cache.items():
            engines[engine_id] = {
                "active_version": (
                    entry.model.model_version if entry.model else None
                ),
                "age_seconds": round(time.monotonic() - entry.loaded_at, 2),
                "expired": entry.is_expired,
                "ttl_seconds": entry.ttl_seconds,
            }

        return {
            "total_engines_cached": len(self._cache),
            "known_engines": sorted(self._known_engines),
            "engines": engines,
        }

    def clear_cache(self) -> None:
        """Clear the entire in-memory cache (for testing or admin)."""
        self._cache.clear()
        self._known_engines.clear()
        logger.info("Model registry cache cleared.")

    # ── Internal helpers ──────────────────────────────────────────────────

    async def _get_or_load(self, engine_id: str) -> CacheEntry:
        """Return cached entry if fresh, otherwise load from DB."""
        entry = self._cache.get(engine_id)

        if entry is not None and not entry.is_expired:
            return entry

        # Cache miss or expired — load from DB (fail-closed on error)
        model = await self._load_from_db(engine_id)
        self._set_cache(engine_id, model)
        return self._cache[engine_id]

    async def _load_from_db(self, engine_id: str) -> Optional[ModelRegistry]:
        """
        Load the active model from SQLite.

        Fail-closed: if the database raises, we convert to
        ModelRegistryError rather than returning None.

        Raises:
            ModelRegistryError: On any database error.
        """
        try:
            async with self._session_factory() as session:
                repo = ModelRegistryRepository(session)
                return await repo.get_active_model(engine_id)
        except Exception as exc:
            logger.error(
                "Fail-closed: failed to load active model for engine '%s': %s",
                engine_id, exc,
            )
            raise ModelRegistryError(
                f"Failed to load active model for engine '{engine_id}': {exc}",
                engine_id=engine_id,
            ) from exc

    def _set_cache(
        self, engine_id: str, model: Optional[ModelRegistry],
    ) -> None:
        """Build a cache entry from the loaded model."""
        entry = CacheEntry(
            model=model,
            loaded_at=time.monotonic(),
            ttl_seconds=self._default_ttl,
        )
        self._cache[engine_id] = entry
        self._known_engines.add(engine_id)
