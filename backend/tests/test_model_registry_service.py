"""
Tests for the Model Registry service and repository.

Uses aiosqlite (async SQLite) as the test backend so tests can run
without a separate database instance.

Test coverage:
    - Repository: active model queries, version tracking, activation
    - Service: cache population, TTL expiry, forced refresh
    - Fail-closed: service raises ModelRegistryError on DB failure
    - SHA256 integrity validation against local files
    - Artifact URI retrieval
    - Version info and cache stats
"""
from __future__ import annotations

import hashlib
import os
import tempfile
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.base import Base
from app.models.model_registry import ModelRegistry
from app.repositories.model_registry_repository import ModelRegistryRepository
from app.services.model_registry_service import (
    ModelRegistryService,
    ModelRegistryError,
    ModelIntegrityError,
)

TEST_DATABASE_URL = "sqlite+aiosqlite://"


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide an async session for testing."""
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def session_factory(engine):
    """Provide a session factory for the service."""
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ── Seed helpers ────────────────────────────────────────────────────────────


async def seed_models(
    session: AsyncSession,
    models_data: List[Dict[str, Any]],
) -> List[ModelRegistry]:
    """Insert test model records and return them."""
    created = []
    for data in models_data:
        model = ModelRegistry(**data)
        session.add(model)
        created.append(model)
    await session.commit()
    for model in created:
        await session.refresh(model)
    return created


def _sample_e3_models() -> List[Dict[str, Any]]:
    """Return sample E3 archetype model versions."""
    return [
        {
            "engine_id": "E3",
            "model_version": "2.1.0",
            "artifact_s3_uri": "s3://riskintel-models/e3/archetype_v2.1.0.pkl",
            "training_data_hash": "sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "is_active": True,
        },
    ]


def _sample_e3_model_two_versions() -> List[Dict[str, Any]]:
    """Return two versions of E3 model (one old inactive, one new active)."""
    return [
        {
            "engine_id": "E3",
            "model_version": "1.0.0",
            "artifact_s3_uri": "s3://riskintel-models/e3/archetype_v1.0.0.pkl",
            "training_data_hash": "sha256:old_hash_0000000000000000000000000000000000000000000",
            "is_active": False,
        },
        {
            "engine_id": "E3",
            "model_version": "2.1.0",
            "artifact_s3_uri": "s3://riskintel-models/e3/archetype_v2.1.0.pkl",
            "training_data_hash": "sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "is_active": True,
        },
    ]


def _sample_e4_models() -> List[Dict[str, Any]]:
    """Return sample E4 recommendation model versions."""
    return [
        {
            "engine_id": "E4",
            "model_version": "1.8.0",
            "artifact_s3_uri": "s3://riskintel-models/e4/recommender_v1.8.0.joblib",
            "training_data_hash": "sha256:1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff",
            "is_active": True,
        },
    ]


# ═══════════════════════════════════════════════════════════════════════════
#  Repository tests
# ═══════════════════════════════════════════════════════════════════════════


class TestModelRegistryRepository:
    """Tests for the ModelRegistryRepository data access layer."""

    @pytest.mark.asyncio
    async def test_get_active_models_by_engine(self, session: AsyncSession):
        """Should return only active models for the specified engine."""
        all_models = _sample_e3_models() + _sample_e4_models()
        await seed_models(session, all_models)

        repo = ModelRegistryRepository(session)
        e3_models = await repo.get_active_models_by_engine("E3")

        assert len(e3_models) == 1
        assert e3_models[0].engine_id == "E3"
        assert e3_models[0].is_active is True

    @pytest.mark.asyncio
    async def test_get_active_models_excludes_inactive(self, session: AsyncSession):
        """Inactive models should not appear in results."""
        await seed_models(session, _sample_e3_model_two_versions())

        repo = ModelRegistryRepository(session)
        active = await repo.get_active_models_by_engine("E3")

        assert len(active) == 1
        assert active[0].model_version == "2.1.0"

    @pytest.mark.asyncio
    async def test_get_active_model(self, session: AsyncSession):
        """Should return the single active model for an engine."""
        await seed_models(session, _sample_e3_model_two_versions())

        repo = ModelRegistryRepository(session)
        model = await repo.get_active_model("E3")

        assert model is not None
        assert model.model_version == "2.1.0"
        assert model.is_active is True

    @pytest.mark.asyncio
    async def test_get_active_model_none(self, session: AsyncSession):
        """Should return None when no active model exists."""
        await seed_models(
            session,
            [
                {
                    "engine_id": "E3",
                    "model_version": "1.0.0",
                    "artifact_s3_uri": "s3://bucket/model.pkl",
                    "training_data_hash": "sha256:hash",
                    "is_active": False,
                },
            ],
        )

        repo = ModelRegistryRepository(session)
        model = await repo.get_active_model("E3")
        assert model is None

    @pytest.mark.asyncio
    async def test_get_all_active_models(self, session: AsyncSession):
        """Should return all active models across engines."""
        await seed_models(session, _sample_e3_models() + _sample_e4_models())

        repo = ModelRegistryRepository(session)
        all_active = await repo.get_all_active_models()

        assert len(all_active) == 2  # one per engine (E3, E4)

    @pytest.mark.asyncio
    async def test_get_versions(self, session: AsyncSession):
        """Should list all model versions for an engine."""
        await seed_models(session, _sample_e3_model_two_versions())

        repo = ModelRegistryRepository(session)
        versions = await repo.get_versions("E3")

        assert sorted(versions) == ["1.0.0", "2.1.0"]

    @pytest.mark.asyncio
    async def test_get_active_version(self, session: AsyncSession):
        """Should return the currently active version string."""
        await seed_models(session, _sample_e3_model_two_versions())

        repo = ModelRegistryRepository(session)
        version = await repo.get_active_version("E3")

        assert version == "2.1.0"

    @pytest.mark.asyncio
    async def test_get_model_by_version(self, session: AsyncSession):
        """Should retrieve a specific model version."""
        await seed_models(session, _sample_e3_model_two_versions())

        repo = ModelRegistryRepository(session)
        model = await repo.get_model_by_version("E3", "1.0.0")

        assert model is not None
        assert model.model_version == "1.0.0"
        assert model.is_active is False

    @pytest.mark.asyncio
    async def test_get_version_history(self, session: AsyncSession):
        """Version history should return metadata dicts."""
        await seed_models(session, _sample_e3_models())

        repo = ModelRegistryRepository(session)
        history = await repo.get_version_history("E3")

        assert len(history) == 1
        assert all("model_version" in h for h in history)
        assert all("artifact_s3_uri" in h for h in history)
        assert all("training_data_hash" in h for h in history)

    @pytest.mark.asyncio
    async def test_get_artifact_uri(self, session: AsyncSession):
        """Should return the S3 URI for the active model."""
        await seed_models(session, _sample_e3_models())

        repo = ModelRegistryRepository(session)
        uri = await repo.get_artifact_uri("E3")

        assert uri == "s3://riskintel-models/e3/archetype_v2.1.0.pkl"

    @pytest.mark.asyncio
    async def test_get_artifact_uri_no_active(self, session: AsyncSession):
        """Should return None when no active model exists."""
        repo = ModelRegistryRepository(session)
        uri = await repo.get_artifact_uri("E99")
        assert uri is None

    @pytest.mark.asyncio
    async def test_get_training_data_hash(self, session: AsyncSession):
        """Should return the training data hash for the active model."""
        await seed_models(session, _sample_e3_models())

        repo = ModelRegistryRepository(session)
        hash_val = await repo.get_training_data_hash("E3")

        assert hash_val == "sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

    @pytest.mark.asyncio
    async def test_activate_version(self, session: AsyncSession):
        """Activating a version should deactivate others."""
        await seed_models(session, _sample_e3_model_two_versions())

        repo = ModelRegistryRepository(session)

        # Find the old version and activate it
        old = await repo.get_model_by_version("E3", "1.0.0")
        assert old is not None
        assert old.is_active is False

        activated = await repo.activate_version(old.id)
        assert activated is not None
        assert activated.is_active is True

        # The previously-active version should now be inactive
        prev_active = await repo.get_model_by_version("E3", "2.1.0")
        assert prev_active is not None
        assert prev_active.is_active is False

    @pytest.mark.asyncio
    async def test_activate_version_not_found(self, session: AsyncSession):
        """Activating a non-existent version should return None."""
        repo = ModelRegistryRepository(session)
        result = await repo.activate_version(
            uuid.UUID("00000000-0000-0000-0000-000000000001"),
        )
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════
#  Service tests
# ═══════════════════════════════════════════════════════════════════════════


class TestModelRegistryService:
    """Tests for the cached ModelRegistryService."""

    @pytest.mark.asyncio
    async def test_get_active_model_populates_cache(self, session_factory, engine):
        """First call should load from DB and cache."""
        async with session_factory() as session:
            await seed_models(session, _sample_e3_models())

        service = ModelRegistryService(session_factory, default_ttl=60)
        model = await service.get_active_model("E3")

        assert model is not None
        assert model.model_version == "2.1.0"

        # Verify cache was populated
        assert "E3" in service._cache
        assert service._cache["E3"].is_expired is False

    @pytest.mark.asyncio
    async def test_get_active_model_uses_cache(self, session_factory, engine):
        """Second call should use cache, not hit DB."""
        async with session_factory() as session:
            await seed_models(session, _sample_e3_models())

        service = ModelRegistryService(session_factory, default_ttl=60)
        model1 = await service.get_active_model("E3")

        # Manually remove from DB to prove we're reading from cache
        async with session_factory() as session:
            repo = ModelRegistryRepository(session)
            await repo.delete(model1.id)
            await session.commit()

        # This should still work from cache
        model2 = await service.get_active_model("E3")
        assert model2 is not None
        assert model2.model_version == "2.1.0"

    @pytest.mark.asyncio
    async def test_cache_ttl_expiry(self, session_factory, engine):
        """After TTL expires, the cache should reload from DB."""
        async with session_factory() as session:
            await seed_models(session, _sample_e3_models())

        service = ModelRegistryService(session_factory, default_ttl=0)
        model = await service.get_active_model("E3")
        assert model is not None

        # Cache entry should already be expired
        assert service._cache["E3"].is_expired is True

    @pytest.mark.asyncio
    async def test_get_active_model_no_active(self, session_factory, engine):
        """Should return None when no active model for engine."""
        async with session_factory() as session:
            await seed_models(
                session,
                [
                    {
                        "engine_id": "E3",
                        "model_version": "1.0.0",
                        "artifact_s3_uri": "s3://bucket/model.pkl",
                        "training_data_hash": "sha256:hash",
                        "is_active": False,
                    },
                ],
            )

        service = ModelRegistryService(session_factory, default_ttl=60)
        model = await service.get_active_model("E3")
        assert model is None

    @pytest.mark.asyncio
    async def test_get_artifact_uri(self, session_factory, engine):
        """Should return the S3 URI for the active model."""
        async with session_factory() as session:
            await seed_models(session, _sample_e3_models())

        service = ModelRegistryService(session_factory, default_ttl=60)
        uri = await service.get_artifact_uri("E3")

        assert uri == "s3://riskintel-models/e3/archetype_v2.1.0.pkl"

    @pytest.mark.asyncio
    async def test_get_artifact_uri_no_active(self, session_factory, engine):
        """Should return None when no active model."""
        service = ModelRegistryService(session_factory, default_ttl=60)
        uri = await service.get_artifact_uri("E99")
        assert uri is None

    @pytest.mark.asyncio
    async def test_get_training_data_hash(self, session_factory, engine):
        """Should return the training data hash."""
        async with session_factory() as session:
            await seed_models(session, _sample_e3_models())

        service = ModelRegistryService(session_factory, default_ttl=60)
        hash_val = await service.get_training_data_hash("E3")

        assert hash_val.startswith("sha256:")
        assert len(hash_val) == 71  # "sha256:" + 64 hex chars

    @pytest.mark.asyncio
    async def test_get_active_version(self, session_factory, engine):
        """Should return the active version string."""
        async with session_factory() as session:
            await seed_models(session, _sample_e3_models())

        service = ModelRegistryService(session_factory, default_ttl=60)
        version = await service.get_active_version("E3")

        assert version == "2.1.0"

    @pytest.mark.asyncio
    async def test_get_version_info(self, session_factory, engine):
        """Version info should include complete metadata."""
        async with session_factory() as session:
            await seed_models(session, _sample_e3_models())

        service = ModelRegistryService(session_factory, default_ttl=60)
        info = await service.get_version_info("E3")

        assert info["engine_id"] == "E3"
        assert info["active_version"] == "2.1.0"
        assert info["artifact_uri"] is not None
        assert info["training_data_hash"] is not None
        assert "cache_age_seconds" in info

    @pytest.mark.asyncio
    async def test_get_model_by_version(self, session_factory, engine):
        """Should retrieve a specific non-active version."""
        async with session_factory() as session:
            await seed_models(session, _sample_e3_model_two_versions())

        service = ModelRegistryService(session_factory, default_ttl=60)
        model = await service.get_model_by_version("E3", "1.0.0")

        assert model is not None
        assert model.model_version == "1.0.0"
        assert model.is_active is False

    @pytest.mark.asyncio
    async def test_forced_refresh(self, session_factory, engine):
        """Refresh should reload model and update cache."""
        async with session_factory() as session:
            await seed_models(session, _sample_e3_model_two_versions())

        service = ModelRegistryService(session_factory, default_ttl=3600)
        model = await service.get_active_model("E3")
        assert model.model_version == "2.1.0"

        # Activate the old version in DB
        async with session_factory() as session:
            repo = ModelRegistryRepository(session)
            old = await repo.get_model_by_version("E3", "1.0.0")
            if old:
                await repo.activate_version(old.id)
            await session.commit()

        # Refresh cache
        await service.refresh("E3")
        refreshed = await service.get_active_model("E3")
        assert refreshed.model_version == "1.0.0"

    @pytest.mark.asyncio
    async def test_refresh_all(self, session_factory, engine):
        """refresh_all should refresh all known engines."""
        async with session_factory() as session:
            await seed_models(session, _sample_e3_models() + _sample_e4_models())

        service = ModelRegistryService(session_factory, default_ttl=3600)
        await service.get_active_model("E3")
        await service.get_active_model("E4")

        results = await service.refresh_all()
        assert "E3" in results
        assert "E4" in results

    @pytest.mark.asyncio
    async def test_fail_closed_db_unreachable(self):
        """Fail-closed: when DB is unreachable, service raises."""
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        local_factory = async_sessionmaker(engine, expire_on_commit=False)

        service = ModelRegistryService(local_factory, default_ttl=60)

        with pytest.raises(ModelRegistryError) as exc_info:
            await service.get_active_model("E3")

        assert exc_info.value.engine_id == "E3"

    @pytest.mark.asyncio
    async def test_get_cache_stats(self, session_factory, engine):
        """Cache stats should return diagnostic info."""
        async with session_factory() as session:
            await seed_models(session, _sample_e3_models() + _sample_e4_models())

        service = ModelRegistryService(session_factory, default_ttl=60)
        await service.get_active_model("E3")
        await service.get_active_model("E4")

        stats = service.get_cache_stats()
        assert stats["total_engines_cached"] == 2
        assert "E3" in stats["engines"]
        assert "E4" in stats["engines"]

    @pytest.mark.asyncio
    async def test_clear_cache(self, session_factory, engine):
        """Clearing cache should remove all entries."""
        async with session_factory() as session:
            await seed_models(session, _sample_e3_models())

        service = ModelRegistryService(session_factory, default_ttl=60)
        await service.get_active_model("E3")
        assert len(service._cache) == 1

        service.clear_cache()
        assert len(service._cache) == 0
        assert len(service._known_engines) == 0

    @pytest.mark.asyncio
    async def test_multiple_engines_independent_cache(self, session_factory, engine):
        """Different engines should have independent cache entries."""
        async with session_factory() as session:
            await seed_models(session, _sample_e3_models() + _sample_e4_models())

        service = ModelRegistryService(session_factory, default_ttl=60)
        e3_model = await service.get_active_model("E3")
        e4_model = await service.get_active_model("E4")

        assert e3_model.engine_id == "E3"
        assert e4_model.engine_id == "E4"
        assert e3_model.model_version == "2.1.0"
        assert e4_model.model_version == "1.8.0"


# ═══════════════════════════════════════════════════════════════════════════
#  Integrity validation tests
# ═══════════════════════════════════════════════════════════════════════════


class TestModelIntegrityValidation:
    """Tests for SHA256 integrity validation."""

    @pytest.mark.asyncio
    async def test_validate_integrity_matching(self, session_factory, engine):
        """Should pass when local file hash matches registry."""
        # Create a temp file and compute its hash
        content = b"mock model artifact data"
        expected_hash = "sha256:" + hashlib.sha256(content).hexdigest()

        async with session_factory() as session:
            await seed_models(
                session,
                [
                    {
                        "engine_id": "E3",
                        "model_version": "2.1.0",
                        "artifact_s3_uri": "s3://bucket/model.pkl",
                        "training_data_hash": expected_hash,
                        "is_active": True,
                    },
                ],
            )

        # Write the file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl") as f:
            f.write(content)
            fpath = f.name

        try:
            service = ModelRegistryService(session_factory, default_ttl=60)
            result = await service.validate_model_integrity("E3", fpath)
            assert result is True
        finally:
            os.unlink(fpath)

    @pytest.mark.asyncio
    async def test_validate_integrity_mismatch(self, session_factory, engine):
        """Should raise when local file hash does not match registry."""
        async with session_factory() as session:
            await seed_models(
                session,
                [
                    {
                        "engine_id": "E3",
                        "model_version": "2.1.0",
                        "artifact_s3_uri": "s3://bucket/model.pkl",
                        "training_data_hash": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                        "is_active": True,
                    },
                ],
            )

        # Create a file with DIFFERENT content
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl") as f:
            f.write(b"different content that produces a different hash")
            fpath = f.name

        try:
            service = ModelRegistryService(session_factory, default_ttl=60)
            with pytest.raises(ModelIntegrityError) as exc_info:
                await service.validate_model_integrity("E3", fpath)

            assert exc_info.value.engine_id == "E3"
            assert exc_info.value.model_version == "2.1.0"
            assert exc_info.value.expected_hash != exc_info.value.actual_hash
        finally:
            os.unlink(fpath)

    @pytest.mark.asyncio
    async def test_validate_integrity_file_not_found(self, session_factory, engine):
        """Should raise when local file does not exist."""
        async with session_factory() as session:
            await seed_models(
                session,
                [
                    {
                        "engine_id": "E3",
                        "model_version": "2.1.0",
                        "artifact_s3_uri": "s3://bucket/model.pkl",
                        "training_data_hash": "sha256:hash",
                        "is_active": True,
                    },
                ],
            )

        service = ModelRegistryService(session_factory, default_ttl=60)
        with pytest.raises(ModelIntegrityError) as exc_info:
            await service.validate_model_integrity("E3", "/nonexistent/path.pkl")

        assert exc_info.value.actual_hash == "file_not_found"

    @pytest.mark.asyncio
    async def test_validate_integrity_no_active_model(self, session_factory, engine):
        """Should raise when no active model in registry."""
        service = ModelRegistryService(session_factory, default_ttl=60)
        with pytest.raises(ModelRegistryError) as exc_info:
            await service.validate_model_integrity("E99", "dummy.pkl")

        assert exc_info.value.engine_id == "E99"
