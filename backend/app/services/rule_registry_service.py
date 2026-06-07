"""
RuleRegistry service — cached, version-aware rule resolution.

Provides:
- In-memory cache of active rules with configurable TTL
- Automatic cache refresh on expiry
- Rule lookup by engine_id and rule_name
- Version tracking and reporting
- Fail-closed: raises RuleRegistryError on DB failure

Architecture:
    RuleRegistryService
        ├── get_rules(engine_id)      → Cached list of rules
        ├── get_rule(engine_id, name) → Single rule lookup
        ├── get_version(engine_id)    → Active version string
        ├── refresh(engine_id)         → Force cache refresh
        ├── refresh_all()              → Refresh all engines
        ├── get_cache_stats()          → Diagnostics
        └── _load_from_db()            → Fallback-to-DB
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rule_registry import RuleRegistry
from app.repositories.rule_registry_repository import RuleRegistryRepository

logger = logging.getLogger(__name__)


# ── Custom exception (fail-closed) ─────────────────────────────────────────


class RuleRegistryError(Exception):
    """
    Raised when the Rule Registry service cannot load rules.

    This is the fail-closed mechanism: if the database is unreachable or
    returns corrupt data, the service raises instead of returning stale
    or empty results that could silently cause incorrect assessments.
    """

    def __init__(self, message: str, engine_id: Optional[str] = None) -> None:
        super().__init__(message)
        self.engine_id = engine_id


# ── Cache entry ────────────────────────────────────────────────────────────


@dataclass
class CacheEntry:
    """A single cache entry with payload and expiry metadata."""

    rules: List[RuleRegistry]
    version_map: Dict[str, RuleRegistry]  # rule_name -> rule
    loaded_at: float  # time.monotonic()
    ttl_seconds: float

    @property
    def is_expired(self) -> bool:
        """Return True if this cache entry has exceeded its TTL."""
        return (time.monotonic() - self.loaded_at) > self.ttl_seconds


# ── Service ────────────────────────────────────────────────────────────────


class RuleRegistryService:
    """
    Cached, fail-closed rule registry service.

    Usage:
        service = RuleRegistryService(session_factory, default_ttl=300)
        rules = await service.get_rules("E1")

    The service caches active rules per engine in memory. On cache miss
    or TTL expiry, it reloads from the database. If the database call
    fails, it raises ``RuleRegistryError`` rather than returning stale data.
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

    async def get_rules(self, engine_id: str) -> List[RuleRegistry]:
        """
        Retrieve all active rules for an engine, using cache if fresh.

        Args:
            engine_id: Engine identifier (e.g. "E1", "E2", "E5").

        Returns:
            List of active RuleRegistry records.

        Raises:
            RuleRegistryError: If the database is unreachable (fail-closed).
        """
        entry = await self._get_or_load(engine_id)
        return entry.rules

    async def get_rule(
        self, engine_id: str, rule_name: str,
    ) -> Optional[RuleRegistry]:
        """
        Look up a specific active rule by engine and rule name.

        Args:
            engine_id: Engine identifier.
            rule_name: Name of the rule.

        Returns:
            The matching RuleRegistry record, or None.
        """
        entry = await self._get_or_load(engine_id)
        return entry.version_map.get(rule_name)

    async def get_logic_payload(
        self, engine_id: str, rule_name: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get the logic_payload for a specific rule.

        This is the most common access pattern — engine code calls
        this to retrieve the thresholds/conditions it needs.

        Args:
            engine_id: Engine identifier.
            rule_name: Name of the rule.

        Returns:
            The logic_payload dict, or None.
        """
        rule = await self.get_rule(engine_id, rule_name)
        return rule.logic_payload if rule is not None else None

    async def get_active_version(self, engine_id: str) -> Optional[str]:
        """
        Get the currently active version string for an engine.

        Args:
            engine_id: Engine identifier.

        Returns:
            Version string (e.g. "1.0.0"), or None if no active rule.
        """
        entry = await self._get_or_load(engine_id)
        if not entry.rules:
            return None
        # All active rules for an engine share the same version due to
        # the activate_version mechanism. Return the first one's version.
        return entry.rules[0].version

    async def get_version_info(
        self, engine_id: str,
    ) -> Dict[str, Any]:
        """
        Get detailed version info for an engine.

        Returns:
            Dict with:
                engine_id
                active_version
                rule_count
                cached (bool)
                cache_age_seconds (float)
        """
        entry = self._cache.get(engine_id)
        cached = entry is not None and not entry.is_expired

        if cached and entry is not None:
            rules = entry.rules
            cache_age = time.monotonic() - entry.loaded_at
        else:
            # Load fresh but don't cache — this is an info call
            rules = await self._load_rules_from_db(engine_id)
            cache_age = 0.0

        version = rules[0].version if rules else None

        return {
            "engine_id": engine_id,
            "active_version": version,
            "rule_count": len(rules),
            "cached": cached,
            "cache_age_seconds": round(cache_age, 2),
        }

    async def refresh(self, engine_id: str) -> None:
        """
        Force a cache refresh for a specific engine.

        This is called explicitly when rules are updated (e.g. after
        a deployment or admin action) to avoid waiting for TTL expiry.

        Raises:
            RuleRegistryError: If DB unreachable.
        """
        rules = await self._load_rules_from_db(engine_id)
        self._set_cache(engine_id, rules)
        logger.info("Cache refreshed for engine '%s' — %d rules loaded.", engine_id, len(rules))

    async def refresh_all(self) -> Dict[str, int]:
        """
        Refresh the cache for all known engines.

        Returns:
            Dict of engine_id -> rule_count for successfully refreshed engines.
        """
        results: Dict[str, int] = {}
        for engine_id in list(self._known_engines):
            try:
                await self.refresh(engine_id)
                results[engine_id] = len(self._cache[engine_id].rules)
            except RuleRegistryError:
                logger.warning("refresh_all: engine '%s' unreachable, skipping.", engine_id)
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
                "rule_count": len(entry.rules),
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
        logger.info("Rule registry cache cleared.")

    # ── Internal helpers ──────────────────────────────────────────────────

    async def _get_or_load(self, engine_id: str) -> CacheEntry:
        """Return cached entry if fresh, otherwise load from DB."""
        entry = self._cache.get(engine_id)

        if entry is not None and not entry.is_expired:
            return entry

        # Cache miss or expired — load from DB (fail-closed on error)
        rules = await self._load_rules_from_db(engine_id)
        self._set_cache(engine_id, rules)
        return self._cache[engine_id]

    async def _load_rules_from_db(self, engine_id: str) -> List[RuleRegistry]:
        """
        Load active rules from SQLite.

        Fail-closed: if the database raises, we convert to RuleRegistryError
        rather than returning empty/stale data.

        Raises:
            RuleRegistryError: On any database error.
        """
        try:
            async with self._session_factory() as session:
                repo = RuleRegistryRepository(session)
                rules = await repo.get_active_rules_by_engine(engine_id)
                return rules
        except Exception as exc:
            logger.error(
                "Fail-closed: failed to load rules for engine '%s': %s",
                engine_id, exc,
            )
            raise RuleRegistryError(
                f"Failed to load rules for engine '{engine_id}': {exc}",
                engine_id=engine_id,
            ) from exc

    def _set_cache(self, engine_id: str, rules: List[RuleRegistry]) -> None:
        """Build a cache entry from loaded rules."""
        version_map = {rule.rule_name: rule for rule in rules}

        # Use the default TTL — callers can vary this per engine in the future
        entry = CacheEntry(
            rules=rules,
            version_map=version_map,
            loaded_at=time.monotonic(),
            ttl_seconds=self._default_ttl,
        )
        self._cache[engine_id] = entry
        self._known_engines.add(engine_id)
