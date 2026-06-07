"""
Tests for the Rule Registry service and repository.

Uses aiosqlite (async SQLite) as the test backend so tests can run
without a separate database instance.

Test coverage:
    - Repository: active rule queries, version tracking, activation
    - Service: cache population, TTL expiry, forced refresh
    - Fail-closed: service raises RuleRegistryError on DB failure
    - Version info and cache stats
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.base import Base
from app.models.rule_registry import RuleRegistry
from app.repositories.rule_registry_repository import RuleRegistryRepository
from app.services.rule_registry_service import (
    RuleRegistryService,
    RuleRegistryError,
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


async def seed_rules(
    session: AsyncSession,
    rules_data: List[Dict[str, Any]],
) -> List[RuleRegistry]:
    """Insert test rule records and return them."""
    created = []
    for data in rules_data:
        rule = RuleRegistry(**data)
        session.add(rule)
        created.append(rule)
    await session.commit()
    # Refresh to get server-defaults (UUID, timestamps)
    for rule in created:
        await session.refresh(rule)
    return created


def _sample_e1_rules() -> List[Dict[str, Any]]:
    """Return sample E1 eligibility rules as a single row per version."""
    return [
        {
            "engine_id": "E1",
            "rule_name": "eligibility_rules",
            "logic_payload": {
                "cibil_threshold": {"min_score": 300, "max_score": 900},
                "income_threshold": {"min_annual_income": 0},
            },
            "version": "1.0.0",
            "is_active": True,
        },
    ]


def _sample_e2_rules() -> List[Dict[str, Any]]:
    """Return sample E2 risk tier rules as a single row per version."""
    return [
        {
            "engine_id": "E2",
            "rule_name": "risk_tier_rules",
            "logic_payload": {
                "p1": {"min_score": 701, "description": "Low Risk"},
                "p2": {"min_score": 669, "max_score": 700, "description": "Moderate Risk"},
                "p3": {"description": "Elevated Risk"},
                "p4": {"max_score": 658, "description": "High Risk"},
            },
            "version": "2.1.0",
            "is_active": True,
        },
    ]


def _sample_e5_rules() -> List[Dict[str, Any]]:
    """Return sample E5 readiness rules as a single row."""
    return [
        {
            "engine_id": "E5",
            "rule_name": "readiness_rules",
            "logic_payload": {
                "floor_breach": {"min_income_expense_ratio": 0.5},
            },
            "version": "1.0.0",
            "is_active": True,
        },
    ]


# ═══════════════════════════════════════════════════════════════════════════
#  Repository tests
# ═══════════════════════════════════════════════════════════════════════════


class TestRuleRegistryRepository:
    """Tests for the RuleRegistryRepository data access layer."""

    @pytest.mark.asyncio
    async def test_get_active_rules_by_engine(self, session: AsyncSession):
        """Should return only active rules for the specified engine."""
        all_rules = _sample_e1_rules() + _sample_e2_rules()
        await seed_rules(session, all_rules)

        repo = RuleRegistryRepository(session)
        e1_rules = await repo.get_active_rules_by_engine("E1")

        assert len(e1_rules) == 1  # one row per engine+version
        assert e1_rules[0].engine_id == "E1"
        assert e1_rules[0].is_active is True

    @pytest.mark.asyncio
    async def test_get_active_rules_excludes_inactive(self, session: AsyncSession):
        """Inactive rules should not appear in results."""
        rules_data = [
            {
                "engine_id": "E1",
                "rule_name": "old_rule",
                "logic_payload": {"key": "old"},
                "version": "0.9.0",
                "is_active": False,
            },
            {
                "engine_id": "E1",
                "rule_name": "current_rule",
                "logic_payload": {"key": "new"},
                "version": "1.0.0",
                "is_active": True,
            },
        ]
        await seed_rules(session, rules_data)

        repo = RuleRegistryRepository(session)
        rules = await repo.get_active_rules_by_engine("E1")

        assert len(rules) == 1
        assert rules[0].rule_name == "current_rule"

    @pytest.mark.asyncio
    async def test_get_active_rule(self, session: AsyncSession):
        """Should find a specific active rule by name."""
        await seed_rules(session, _sample_e1_rules())

        repo = RuleRegistryRepository(session)
        rule = await repo.get_active_rule("E1", "eligibility_rules")

        assert rule is not None
        assert rule.rule_name == "eligibility_rules"
        assert "cibil_threshold" in rule.logic_payload

    @pytest.mark.asyncio
    async def test_get_active_rule_not_found(self, session: AsyncSession):
        """Should return None for a non-existent rule."""
        await seed_rules(session, _sample_e1_rules())
        repo = RuleRegistryRepository(session)
        rule = await repo.get_active_rule("E1", "nonexistent_rule")
        assert rule is None

    @pytest.mark.asyncio
    async def test_get_all_active_rules(self, session: AsyncSession):
        """Should return all active rules across engines."""
        all_rules = _sample_e1_rules() + _sample_e2_rules() + _sample_e5_rules()
        await seed_rules(session, all_rules)

        repo = RuleRegistryRepository(session)
        all_active = await repo.get_all_active_rules()

        assert len(all_active) == 3  # one per engine (E1, E2, E5)

    @pytest.mark.asyncio
    async def test_get_versions(self, session: AsyncSession):
        """Should list all versions for an engine, newest first."""
        rules_data = [
            {
                "engine_id": "E1",
                "rule_name": "cibil_threshold",
                "logic_payload": {},
                "version": "0.9.0",
                "is_active": False,
            },
            {
                "engine_id": "E1",
                "rule_name": "cibil_threshold",
                "logic_payload": {},
                "version": "1.0.0",
                "is_active": True,
            },
        ]
        created = await seed_rules(session, rules_data)

        repo = RuleRegistryRepository(session)
        versions = await repo.get_versions("E1")

        assert sorted(versions) == ["0.9.0", "1.0.0"]

    @pytest.mark.asyncio
    async def test_get_active_version(self, session: AsyncSession):
        """Should return the currently active version string."""
        await seed_rules(session, _sample_e2_rules())

        repo = RuleRegistryRepository(session)
        version = await repo.get_active_version("E2")

        assert version == "2.1.0"

    @pytest.mark.asyncio
    async def test_get_rule_by_version(self, session: AsyncSession):
        """Should retrieve a specific version."""
        rules_data = [
            {
                "engine_id": "E1",
                "rule_name": "cibil_threshold",
                "logic_payload": {"min": 300},
                "version": "0.9.0",
                "is_active": False,
            },
            {
                "engine_id": "E1",
                "rule_name": "cibil_threshold",
                "logic_payload": {"min": 300, "max": 900},
                "version": "1.0.0",
                "is_active": True,
            },
        ]
        await seed_rules(session, rules_data)

        repo = RuleRegistryRepository(session)
        rule = await repo.get_rule_by_version("E1", "0.9.0")

        assert rule is not None
        assert rule.version == "0.9.0"
        assert rule.is_active is False

    @pytest.mark.asyncio
    async def test_get_version_history(self, session: AsyncSession):
        """Version history should return metadata dicts."""
        await seed_rules(session, _sample_e1_rules())
        repo = RuleRegistryRepository(session)
        history = await repo.get_version_history("E1")

        assert len(history) == 1
        assert all("version" in h for h in history)
        assert all("created_at" in h for h in history)

    @pytest.mark.asyncio
    async def test_activate_version(self, session: AsyncSession):
        """Activating a version should deactivate others."""
        rules_data = [
            {
                "engine_id": "E1",
                "rule_name": "cibil_threshold",
                "logic_payload": {"min": 300},
                "version": "0.9.0",
                "is_active": True,
            },
            {
                "engine_id": "E1",
                "rule_name": "cibil_threshold",
                "logic_payload": {"min": 300, "max": 900},
                "version": "1.0.0",
                "is_active": False,
            },
        ]
        created = await seed_rules(session, rules_data)

        # Activate the newer version
        repo = RuleRegistryRepository(session)
        activated = await repo.activate_version(created[1].id)

        assert activated is not None
        assert activated.version == "1.0.0"
        assert activated.is_active is True

        # The old one should now be inactive
        old = await repo.get(created[0].id)
        assert old is not None
        assert old.is_active is False


# ═══════════════════════════════════════════════════════════════════════════
#  Service tests
# ═══════════════════════════════════════════════════════════════════════════


class TestRuleRegistryService:
    """Tests for the cached RuleRegistryService."""

    @pytest.mark.asyncio
    async def test_get_rules_populates_cache(self, session_factory, engine):
        """First call should load from DB and cache."""
        # Seed data via a direct session
        async with session_factory() as session:
            await seed_rules(session, _sample_e1_rules())

        service = RuleRegistryService(session_factory, default_ttl=60)
        rules = await service.get_rules("E1")

        assert len(rules) == 1
        assert rules[0].engine_id == "E1"

        # Verify cache was populated
        assert "E1" in service._cache
        assert service._cache["E1"].is_expired is False

    @pytest.mark.asyncio
    async def test_get_rules_uses_cache(self, session_factory, engine):
        """Second call should use cache, not hit DB."""
        async with session_factory() as session:
            await seed_rules(session, _sample_e1_rules())

        service = RuleRegistryService(session_factory, default_ttl=60)
        rules1 = await service.get_rules("E1")

        # Manually remove from DB to prove we're reading from cache
        async with session_factory() as session:
            repo = RuleRegistryRepository(session)
            for rule in rules1:
                await session.delete(rule)
            await session.commit()

        # This should still work from cache
        rules2 = await service.get_rules("E1")
        assert len(rules2) == 1

    @pytest.mark.asyncio
    async def test_cache_ttl_expiry(self, session_factory, engine):
        """After TTL expires, the cache should reload from DB."""
        async with session_factory() as session:
            await seed_rules(session, _sample_e1_rules())

        service = RuleRegistryService(session_factory, default_ttl=0)  # Expire immediately
        rules = await service.get_rules("E1")
        assert len(rules) == 1

        # Cache entry should already be expired
        assert service._cache["E1"].is_expired is True

    @pytest.mark.asyncio
    async def test_get_rule_lookup(self, session_factory, engine):
        """Should look up a rule by engine and name."""
        async with session_factory() as session:
            await seed_rules(session, _sample_e2_rules())

        service = RuleRegistryService(session_factory, default_ttl=60)
        rule = await service.get_rule("E2", "risk_tier_rules")

        assert rule is not None
        assert rule.rule_name == "risk_tier_rules"
        assert rule.logic_payload["p1"]["min_score"] == 701

    @pytest.mark.asyncio
    async def test_get_rule_not_found(self, session_factory, engine):
        """Should return None for a missing rule."""
        async with session_factory() as session:
            await seed_rules(session, _sample_e1_rules())

        service = RuleRegistryService(session_factory, default_ttl=60)
        rule = await service.get_rule("E1", "nonexistent")
        assert rule is None

    @pytest.mark.asyncio
    async def test_get_logic_payload(self, session_factory, engine):
        """Should return the logic_payload dict directly."""
        async with session_factory() as session:
            await seed_rules(session, _sample_e2_rules())

        service = RuleRegistryService(session_factory, default_ttl=60)
        payload = await service.get_logic_payload("E2", "risk_tier_rules")

        assert payload is not None
        assert payload["p1"] == {"min_score": 701, "description": "Low Risk"}
        assert payload["p2"] == {"min_score": 669, "max_score": 700, "description": "Moderate Risk"}

    @pytest.mark.asyncio
    async def test_get_active_version(self, session_factory, engine):
        """Should return the active version string."""
        async with session_factory() as session:
            await seed_rules(session, _sample_e2_rules())

        service = RuleRegistryService(session_factory, default_ttl=60)
        version = await service.get_active_version("E2")

        assert version == "2.1.0"

    @pytest.mark.asyncio
    async def test_get_version_info(self, session_factory, engine):
        """Version info should include metadata."""
        async with session_factory() as session:
            await seed_rules(session, _sample_e1_rules())

        service = RuleRegistryService(session_factory, default_ttl=60)
        info = await service.get_version_info("E1")

        assert info["engine_id"] == "E1"
        assert info["active_version"] == "1.0.0"
        assert info["rule_count"] == 1
        assert "cache_age_seconds" in info

    @pytest.mark.asyncio
    async def test_forced_refresh(self, session_factory, engine):
        """Refresh should reload rules and update cache."""
        async with session_factory() as session:
            await seed_rules(session, _sample_e1_rules())

        service = RuleRegistryService(session_factory, default_ttl=3600)
        rules = await service.get_rules("E1")
        assert len(rules) == 1

        # Add a new rule version to DB
        async with session_factory() as session:
            new_rule = RuleRegistry(
                engine_id="E1",
                rule_name="eligibility_rules_v2",
                logic_payload={"new": True},
                version="2.0.0",
                is_active=True,
            )
            session.add(new_rule)
            await session.commit()

        # Refresh cache
        await service.refresh("E1")
        rules = await service.get_rules("E1")
        assert len(rules) == 2

    @pytest.mark.asyncio
    async def test_refresh_all(self, session_factory, engine):
        """refresh_all should refresh all known engines."""
        async with session_factory() as session:
            await seed_rules(session, _sample_e1_rules() + _sample_e2_rules())

        service = RuleRegistryService(session_factory, default_ttl=3600)
        await service.get_rules("E1")
        await service.get_rules("E2")

        results = await service.refresh_all()
        assert "E1" in results
        assert "E2" in results

    @pytest.mark.asyncio
    async def test_fail_closed_db_unreachable(self, session_factory):
        """
        Fail-closed: when DB is unreachable, service raises RuleRegistryError.
        Note: We test this by disposing the engine before calling.
        """
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        local_factory = async_sessionmaker(engine, expire_on_commit=False)

        # Don't create tables — query will fail
        service = RuleRegistryService(local_factory, default_ttl=60)

        with pytest.raises(RuleRegistryError) as exc_info:
            await service.get_rules("E1")

        assert "E1" in str(exc_info.value.engine_id) or exc_info.value.engine_id is not None

    @pytest.mark.asyncio
    async def test_get_cache_stats(self, session_factory, engine):
        """Cache stats should return diagnostic info."""
        async with session_factory() as session:
            await seed_rules(session, _sample_e1_rules() + _sample_e2_rules())

        service = RuleRegistryService(session_factory, default_ttl=60)
        await service.get_rules("E1")
        await service.get_rules("E2")

        stats = service.get_cache_stats()
        assert stats["total_engines_cached"] == 2
        assert "E1" in stats["engines"]
        assert "E2" in stats["engines"]

    @pytest.mark.asyncio
    async def test_clear_cache(self, session_factory, engine):
        """Clearing cache should remove all entries."""
        async with session_factory() as session:
            await seed_rules(session, _sample_e1_rules())

        service = RuleRegistryService(session_factory, default_ttl=60)
        await service.get_rules("E1")
        assert len(service._cache) == 1

        service.clear_cache()
        assert len(service._cache) == 0
        assert len(service._known_engines) == 0

    @pytest.mark.asyncio
    async def test_multiple_engines_independent_cache(self, session_factory, engine):
        """Different engines should have independent cache entries."""
        async with session_factory() as session:
            await seed_rules(
                session,
                _sample_e1_rules() + _sample_e2_rules() + _sample_e5_rules(),
            )

        service = RuleRegistryService(session_factory, default_ttl=60)
        e1_rules = await service.get_rules("E1")
        e2_rules = await service.get_rules("E2")
        e5_rules = await service.get_rules("E5")

        assert len(e1_rules) == 1
        assert len(e2_rules) == 1
        assert len(e5_rules) == 1

        assert service._cache["E1"].rules[0].engine_id == "E1"
        assert service._cache["E2"].rules[0].engine_id == "E2"
        assert service._cache["E5"].rules[0].engine_id == "E5"
