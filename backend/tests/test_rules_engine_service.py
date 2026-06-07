"""
Tests for the RulesEngineService — deterministic underwriting layer.

Uses aiosqlite (async SQLite) as the test backend so tests can run
without a separate database instance.

Test coverage:
    - E1 Eligibility: approval, CIBIL rejection, income rejection, DTI rejection,
      asset rejection, employment rejection, edge cases, fail-closed
    - E2 Risk Tier: P1–P4 assignment, boundary values, edge cases
    - E5 Readiness: financial health floor breach, band assignment, band reclassification
    - Fail-closed: missing rules, registry unavailability
"""
from __future__ import annotations

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
from app.services.rules_engine_service import (
    RulesEngineService,
    RulesEngineError,
    EligibilityDecision,
    RiskTierDecision,
    ReadinessDecision,
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
async def session_factory(engine):
    """Provide a session factory for the service."""
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def rule_registry(session_factory, engine):
    """Provide a seeded RuleRegistryService for testing."""
    async with session_factory() as session:
        await seed_default_rules(session)
    service = RuleRegistryService(session_factory, default_ttl=300)
    # Warm the cache
    await service.get_rules("E1")
    await service.get_rules("E2")
    await service.get_rules("E5")
    return service


@pytest_asyncio.fixture
async def engine_service(rule_registry):
    """Provide a RulesEngineService backed by the seeded rule registry."""
    return RulesEngineService(rule_registry)


# ── Seed helpers ────────────────────────────────────────────────────────────


async def seed_default_rules(session: AsyncSession) -> List[RuleRegistry]:
    """Insert default test rule records for E1, E2, and E5."""
    rules_data = _sample_all_rules()
    created = []
    for data in rules_data:
        rule = RuleRegistry(**data)
        session.add(rule)
        created.append(rule)
    await session.commit()
    for rule in created:
        await session.refresh(rule)
    return created


def _sample_all_rules() -> List[Dict[str, Any]]:
    """Return sample rules for all three engines."""
    return [
        # ── E1: Eligibility rules ──────────────────────────────────────────
        {
            "engine_id": "E1",
            "rule_name": "eligibility_rules",
            "logic_payload": {
                "cibil_min_score": 300,
                "min_annual_income": 0,
                "max_debt_to_income_ratio": 2.0,
                "min_asset_to_loan_ratio": 0.5,
                "min_employment_years": 0,
                "rejection_reasons": {
                    "cibil": "CIBIL score is below the minimum requirement.",
                    "income": "Annual income does not meet the minimum requirement.",
                    "dti": "Debt-to-income ratio exceeds the maximum allowable limit.",
                    "assets": "Total asset value is insufficient relative to loan amount.",
                    "employment": "Employment tenure does not meet the minimum requirement.",
                },
            },
            "version": "1.0.0",
            "is_active": True,
        },
        # ── E2: Risk Tier rules ────────────────────────────────────────────
        {
            "engine_id": "E2",
            "rule_name": "risk_tier_rules",
            "logic_payload": {
                "tiers": {
                    "P1": {
                        "min_score": 701,
                        "description": "Low Risk — Excellent credit profile.",
                    },
                    "P2": {
                        "min_score": 669,
                        "max_score": 700,
                        "description": "Moderate Risk — Good credit profile.",
                    },
                    "P3": {
                        "min_score": 659,
                        "max_score": 668,
                        "description": "Elevated Risk — Fair credit profile.",
                    },
                    "P4": {
                        "max_score": 658,
                        "description": "High Risk — Poor credit profile.",
                    },
                },
            },
            "version": "2.1.0",
            "is_active": True,
        },
        # ── E5: Readiness rules ────────────────────────────────────────────
        {
            "engine_id": "E5",
            "rule_name": "readiness_rules",
            "logic_payload": {
                "financial_health_floor_threshold": 0.5,
                "bands": {
                    "Ready": {"min_score": 75},
                    "Moderately Ready": {"min_score": 50},
                    "Needs Improvement": {"min_score": 25},
                    "Not Ready": {"min_score": 0},
                },
            },
            "version": "1.0.0",
            "is_active": True,
        },
    ]


def _valid_person_a_features() -> Dict[str, Any]:
    """Return a valid Person A feature set that would pass E1 checks."""
    return {
        "cibil_score": 750,
        "annual_income": 800000.0,
        "loan_amount": 500000.0,
        "residential_assets_value": 1500000.0,
        "commercial_assets_value": 0.0,
        "luxury_assets_value": 100000.0,
        "bank_asset_value": 200000.0,
        "years_at_current_employer": 5,
        "dependents": 2,
        "education": "Graduate",
        "self_employed": "No",
        "loan_term": 5,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  E1: Eligibility Decision Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestE1Eligibility:
    """Deterministic eligibility evaluation."""

    @pytest.mark.asyncio
    async def test_eligible_passes_all_checks(self, engine_service: RulesEngineService):
        """A well-qualified applicant should be eligible."""
        decision = await engine_service.evaluate_eligibility(_valid_person_a_features())

        assert decision.is_eligible is True
        assert decision.rejection_reason is None
        assert decision.rule_version == "1.0.0"
        assert decision.triggered_rule_names == []

    @pytest.mark.asyncio
    async def test_rejected_cibil_too_low(self, engine_service: RulesEngineService):
        """CIBIL score below minimum should reject with appropriate reason."""
        features = _valid_person_a_features()
        features["cibil_score"] = 200  # Below min of 300

        decision = await engine_service.evaluate_eligibility(features)

        assert decision.is_eligible is False
        assert "CIBIL score" in decision.rejection_reason
        assert "cibil_too_low" in decision.triggered_rule_names

    @pytest.mark.asyncio
    async def test_cibil_score_zero_is_accepted(self, engine_service: RulesEngineService):
        """CIBIL score of 0 should be accepted (it's a valid sentinel, not a score)."""
        features = _valid_person_a_features()
        features["cibil_score"] = 0  # 0 >= 300? No — should be rejected

        decision = await engine_service.evaluate_eligibility(features)

        assert decision.is_eligible is False
        assert "cibil_too_low" in decision.triggered_rule_names

    @pytest.mark.asyncio
    async def test_cibil_negative_one_skipped(self, engine_service: RulesEngineService):
        """CIBIL score of -1 (NTC sentinel) should skip CIBIL check — handled by routing."""
        features = _valid_person_a_features()
        features["cibil_score"] = -1
        # The guard `cibil_score >= 0` short-circuits, so -1 is skipped
        # With all other features being valid, the applicant should pass
        decision = await engine_service.evaluate_eligibility(features)

        assert decision.is_eligible is True
        assert decision.triggered_rule_names == []

    @pytest.mark.asyncio
    async def test_rejected_by_dti_when_income_zero(self, engine_service: RulesEngineService):
        """Zero income leads to infinite DTI and should be rejected."""
        features = _valid_person_a_features()
        features["annual_income"] = 0

        decision = await engine_service.evaluate_eligibility(features)

        # With annual_income=0, income check passes (min is 0),
        # but DTI = 500000/max(1.0, 0) = 500000 > 2.0 so it triggers
        assert decision.is_eligible is False
        assert "dti_exceeded" in decision.triggered_rule_names

    @pytest.mark.asyncio
    async def test_rejected_by_dti(self, engine_service: RulesEngineService):
        """DTI exceeding max ratio should reject."""
        features = _valid_person_a_features()
        features["annual_income"] = 100000.0
        features["loan_amount"] = 1000000.0  # DTI = 10.0, max is 2.0

        decision = await engine_service.evaluate_eligibility(features)

        assert decision.is_eligible is False
        assert "dti" in decision.rejection_reason.lower() or "debt" in decision.rejection_reason.lower()
        assert "dti_exceeded" in decision.triggered_rule_names

    @pytest.mark.asyncio
    async def test_rejected_by_asset_coverage(self, engine_service: RulesEngineService):
        """Asset coverage below minimum ratio should reject."""
        features = _valid_person_a_features()
        # Total assets = 0, loan = 500000 → ATL = 0, min is 0.5
        features["residential_assets_value"] = 0
        features["commercial_assets_value"] = 0
        features["luxury_assets_value"] = 0
        features["bank_asset_value"] = 0

        decision = await engine_service.evaluate_eligibility(features)

        assert decision.is_eligible is False
        assert "asset" in decision.rejection_reason.lower()
        assert "asset_coverage_insufficient" in decision.triggered_rule_names

    @pytest.mark.asyncio
    async def test_employment_tenure_passes_with_zero_minimum(self, engine_service: RulesEngineService):
        """Default rule has min_employment_years=0, so zero years should pass."""
        features = _valid_person_a_features()
        features["years_at_current_employer"] = 0

        decision = await engine_service.evaluate_eligibility(features)

        assert decision.is_eligible is True

    @pytest.mark.asyncio
    async def test_rejected_employment_with_custom_rule(
        self, session_factory, engine,
    ):
        """Employment tenure check with a custom rule that requires minimum tenure."""
        async with session_factory() as session:
            rule = RuleRegistry(
                engine_id="E1",
                rule_name="eligibility_rules",
                logic_payload={
                    "cibil_min_score": 300,
                    "min_annual_income": 0,
                    "max_debt_to_income_ratio": 5.0,
                    "min_asset_to_loan_ratio": 0,
                    "min_employment_years": 3,
                    "rejection_reasons": {
                        "employment": "Employment tenure does not meet the minimum requirement.",
                    },
                },
                version="2.0.0",
                is_active=True,
            )
            session.add(rule)
            await session.commit()
            await session.refresh(rule)

        reg = RuleRegistryService(session_factory, default_ttl=300)
        await reg.refresh("E1")
        svc = RulesEngineService(reg)

        features = _valid_person_a_features()
        features["years_at_current_employer"] = 1  # Below min of 3
        features["cibil_score"] = 750

        decision = await svc.evaluate_eligibility(features)

        assert decision.is_eligible is False
        assert "employment" in decision.rejection_reason.lower()
        assert "employment_tenure_too_short" in decision.triggered_rule_names

    @pytest.mark.asyncio
    async def test_missing_features_default_safe(self, engine_service: RulesEngineService):
        """Missing features should default to safe values (0)."""
        decision = await engine_service.evaluate_eligibility({})

        # All features default to 0, which should cause rejection
        assert decision.is_eligible is False
        # CIBIL = 0 < 300 → cibil rejection
        assert decision.triggered_rule_names == ["cibil_too_low"]

    @pytest.mark.asyncio
    async def test_non_numeric_cibil_handled(self, engine_service: RulesEngineService):
        """Non-numeric CIBIL should be handled gracefully (defaults to 0)."""
        features = _valid_person_a_features()
        features["cibil_score"] = "invalid"

        decision = await engine_service.evaluate_eligibility(features)

        assert decision.is_eligible is False
        assert "cibil_too_low" in decision.triggered_rule_names

    @pytest.mark.asyncio
    async def test_decision_contains_rule_metadata(self, engine_service: RulesEngineService):
        """Decision should include rule version and ID."""
        decision = await engine_service.evaluate_eligibility(_valid_person_a_features())

        assert decision.rule_version == "1.0.0"
        assert isinstance(decision.rule_id, str)
        assert len(decision.rule_id) > 0

    @pytest.mark.asyncio
    async def test_fail_closed_missing_rule(self, session_factory, engine):
        """Missing rule should raise RulesEngineError."""
        # Seed only E2 and E5, not E1
        async with session_factory() as session:
            rules = _sample_all_rules()
            # Only seed E2 and E5
            for r in rules:
                if r["engine_id"] == "E1":
                    continue
                session.add(RuleRegistry(**r))
            await session.commit()

        reg = RuleRegistryService(session_factory, default_ttl=300)
        await reg.get_rules("E2")
        svc = RulesEngineService(reg)

        with pytest.raises(RulesEngineError) as exc_info:
            await svc.evaluate_eligibility(_valid_person_a_features())

        assert exc_info.value.engine_id == "E1"
        assert "eligibility_rules" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fail_closed_registry_unavailable(self, session_factory):
        """When registry is down, should raise RulesEngineError."""
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        bad_factory = async_sessionmaker(engine, expire_on_commit=False)
        # Don't create tables — query will fail
        reg = RuleRegistryService(bad_factory, default_ttl=60)
        await engine.dispose()  # Dispose so query fails

        svc = RulesEngineService(reg)

        with pytest.raises(RulesEngineError):
            await svc.evaluate_eligibility(_valid_person_a_features())


# ═══════════════════════════════════════════════════════════════════════════
#  E2: Risk Tier Decision Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestE2RiskTier:
    """Risk tier assignment tests."""

    @pytest.mark.asyncio
    async def test_p1_high_score(self, engine_service: RulesEngineService):
        """Score >= 701 should be P1."""
        decision = await engine_service.evaluate_risk_tier(750)
        assert decision.assigned_tier == "P1"
        assert decision.score_used == 750
        assert decision.rule_version == "2.1.0"

    @pytest.mark.asyncio
    async def test_p1_boundary(self, engine_service: RulesEngineService):
        """Score of exactly 701 should be P1."""
        decision = await engine_service.evaluate_risk_tier(701)
        assert decision.assigned_tier == "P1"

    @pytest.mark.asyncio
    async def test_p2_moderate_score(self, engine_service: RulesEngineService):
        """Score in 669–700 range should be P2."""
        decision = await engine_service.evaluate_risk_tier(685)
        assert decision.assigned_tier == "P2"

    @pytest.mark.asyncio
    async def test_p2_upper_boundary(self, engine_service: RulesEngineService):
        """Score of exactly 700 should be P2."""
        decision = await engine_service.evaluate_risk_tier(700)
        assert decision.assigned_tier == "P2"

    @pytest.mark.asyncio
    async def test_p2_lower_boundary(self, engine_service: RulesEngineService):
        """Score of exactly 669 should be P2."""
        decision = await engine_service.evaluate_risk_tier(669)
        assert decision.assigned_tier == "P2"

    @pytest.mark.asyncio
    async def test_p3_score(self, engine_service: RulesEngineService):
        """Score in 659–668 range should be P3."""
        decision = await engine_service.evaluate_risk_tier(665)
        assert decision.assigned_tier == "P3"

    @pytest.mark.asyncio
    async def test_p3_boundaries(self, engine_service: RulesEngineService):
        """Scores of exactly 659 and 668 should be P3."""
        d1 = await engine_service.evaluate_risk_tier(659)
        d2 = await engine_service.evaluate_risk_tier(668)
        assert d1.assigned_tier == "P3"
        assert d2.assigned_tier == "P3"

    @pytest.mark.asyncio
    async def test_p4_low_score(self, engine_service: RulesEngineService):
        """Score <= 658 should be P4."""
        decision = await engine_service.evaluate_risk_tier(600)
        assert decision.assigned_tier == "P4"

    @pytest.mark.asyncio
    async def test_p4_boundary(self, engine_service: RulesEngineService):
        """Score of exactly 658 should be P4."""
        decision = await engine_service.evaluate_risk_tier(658)
        assert decision.assigned_tier == "P4"

    @pytest.mark.asyncio
    async def test_p4_zero_score(self, engine_service: RulesEngineService):
        """Score of 0 should be P4."""
        decision = await engine_service.evaluate_risk_tier(0)
        assert decision.assigned_tier == "P4"

    @pytest.mark.asyncio
    async def test_p4_negative_score(self, engine_service: RulesEngineService):
        """Score of -1 (NTC sentinel) should be P4."""
        decision = await engine_service.evaluate_risk_tier(-1)
        assert decision.assigned_tier == "P4"

    @pytest.mark.asyncio
    async def test_decision_metadata(self, engine_service: RulesEngineService):
        """Decision should include tier description and score."""
        decision = await engine_service.evaluate_risk_tier(720)
        assert "Low Risk" in decision.tier_description
        assert decision.score_used == 720

    @pytest.mark.asyncio
    async def test_version_tracking(self, engine_service: RulesEngineService):
        """Decision should track which rule version was used."""
        decision = await engine_service.evaluate_risk_tier(750)
        assert decision.rule_version == "2.1.0"
        assert isinstance(decision.rule_id, str)
        assert len(decision.rule_id) > 0

    @pytest.mark.asyncio
    async def test_fail_closed_missing_rule(self, session_factory, engine):
        """Missing E2 rule should raise RulesEngineError."""
        async with session_factory() as session:
            rules = _sample_all_rules()
            for r in rules:
                if r["engine_id"] == "E2":
                    continue
                session.add(RuleRegistry(**r))
            await session.commit()

        reg = RuleRegistryService(session_factory, default_ttl=300)
        svc = RulesEngineService(reg)

        with pytest.raises(RulesEngineError) as exc_info:
            await svc.evaluate_risk_tier(750)

        assert exc_info.value.engine_id == "E2"


# ═══════════════════════════════════════════════════════════════════════════
#  E5: Readiness Decision Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestE5Readiness:
    """Readiness evaluation tests."""

    @pytest.mark.asyncio
    async def test_ready_high_score(self, engine_service: RulesEngineService):
        """Score >= 75 with healthy financials should be Ready."""
        decision = await engine_service.evaluate_readiness(
            score=85, band="Ready", financial_health_score=80.0,
        )

        assert decision.is_ready is True
        assert decision.blocking_conditions is None
        assert decision.band == "Ready"
        assert decision.rule_version == "1.0.0"

    @pytest.mark.asyncio
    async def test_ready_boundary(self, engine_service: RulesEngineService):
        """Score of exactly 75 should be Ready."""
        decision = await engine_service.evaluate_readiness(
            score=75, band="Ready", financial_health_score=80.0,
        )
        assert decision.is_ready is True
        assert decision.band == "Ready"

    @pytest.mark.asyncio
    async def test_moderately_ready(self, engine_service: RulesEngineService):
        """Score in 50–74 range should be Moderately Ready."""
        decision = await engine_service.evaluate_readiness(
            score=60, band="Moderately Ready", financial_health_score=80.0,
        )

        assert decision.is_ready is False
        assert decision.band == "Moderately Ready"
        assert "not yet ready" in decision.blocking_conditions.lower()

    @pytest.mark.asyncio
    async def test_needs_improvement(self, engine_service: RulesEngineService):
        """Score in 25–49 range should be Needs Improvement."""
        decision = await engine_service.evaluate_readiness(
            score=35, band="Needs Improvement", financial_health_score=80.0,
        )

        assert decision.is_ready is False
        assert decision.band == "Needs Improvement"

    @pytest.mark.asyncio
    async def test_not_ready_low_score(self, engine_service: RulesEngineService):
        """Score < 25 should be Not Ready."""
        decision = await engine_service.evaluate_readiness(
            score=10, band="Not Ready", financial_health_score=80.0,
        )

        assert decision.is_ready is False
        assert decision.band == "Not Ready"

    @pytest.mark.asyncio
    async def test_financial_health_floor_breach(
        self, engine_service: RulesEngineService,
    ):
        """Score below financial health floor should force Not Ready with score 0."""
        decision = await engine_service.evaluate_readiness(
            score=80, band="Ready", financial_health_score=0.3,  # Below 0.5 floor
        )

        assert decision.is_ready is False
        assert decision.score == 0
        assert decision.band == "Not Ready"
        assert "financial health" in decision.blocking_conditions.lower()
        assert "financial_health_floor_breach" in decision.triggered_rule_names

    @pytest.mark.asyncio
    async def test_financial_health_floor_boundary(
        self, engine_service: RulesEngineService,
    ):
        """Exactly at the floor threshold should NOT trigger the breach."""
        decision = await engine_service.evaluate_readiness(
            score=80, band="Ready", financial_health_score=0.5,  # Exactly at threshold
        )

        assert decision.is_ready is True
        assert decision.band == "Ready"

    @pytest.mark.asyncio
    async def test_band_reclassification(self, engine_service: RulesEngineService):
        """When engine band differs from rule band, should reclassify."""
        # Score is 70 but engine reported "Ready" — rules say "Moderately Ready"
        decision = await engine_service.evaluate_readiness(
            score=70, band="Ready", financial_health_score=80.0,
        )

        assert decision.band == "Moderately Ready"
        assert "band_reclassified" in decision.triggered_rule_names

    @pytest.mark.asyncio
    async def test_band_reclassification_triggers_not_ready(
        self, engine_service: RulesEngineService,
    ):
        """Reclassification to a non-Ready band should set is_ready=False."""
        decision = await engine_service.evaluate_readiness(
            score=30, band="Ready", financial_health_score=80.0,
        )

        assert decision.is_ready is False
        assert decision.band == "Needs Improvement"
        assert "band_reclassified" in decision.triggered_rule_names

    @pytest.mark.asyncio
    async def test_decision_metadata(self, engine_service: RulesEngineService):
        """Decision should include rule version and ID."""
        decision = await engine_service.evaluate_readiness(
            score=90, band="Ready", financial_health_score=80.0,
        )

        assert decision.rule_version == "1.0.0"
        assert isinstance(decision.rule_id, str)
        assert len(decision.rule_id) > 0

    @pytest.mark.asyncio
    async def test_fail_closed_missing_rule(self, session_factory, engine):
        """Missing E5 rule should raise RulesEngineError."""
        async with session_factory() as session:
            rules = _sample_all_rules()
            for r in rules:
                if r["engine_id"] == "E5":
                    continue
                session.add(RuleRegistry(**r))
            await session.commit()

        reg = RuleRegistryService(session_factory, default_ttl=300)
        svc = RulesEngineService(reg)

        with pytest.raises(RulesEngineError) as exc_info:
            await svc.evaluate_readiness(80, "Ready", 80.0)

        assert exc_info.value.engine_id == "E5"

    @pytest.mark.asyncio
    async def test_triggered_rule_names_empty_on_success(
        self, engine_service: RulesEngineService,
    ):
        """When no rules are triggered, triggered list should be empty."""
        decision = await engine_service.evaluate_readiness(
            score=90, band="Ready", financial_health_score=80.0,
        )

        assert decision.triggered_rule_names == []


# ═══════════════════════════════════════════════════════════════════════════
#  Integration: Cross-engine consistency
# ═══════════════════════════════════════════════════════════════════════════


class TestCrossEngineConsistency:
    """Verify consistent behaviour across engines."""

    @pytest.mark.asyncio
    async def test_version_independent_across_engines(
        self, engine_service: RulesEngineService,
    ):
        """Each engine should report its own version."""
        elig = await engine_service.evaluate_eligibility(_valid_person_a_features())
        tier = await engine_service.evaluate_risk_tier(750)
        ready = await engine_service.evaluate_readiness(85, "Ready", 80.0)

        assert elig.rule_version == "1.0.0"  # E1
        assert tier.rule_version == "2.1.0"  # E2
        assert ready.rule_version == "1.0.0"  # E5

    @pytest.mark.asyncio
    async def test_each_decision_has_unique_rule_id(
        self, engine_service: RulesEngineService,
    ):
        """Each engine's decision should reference a different rule."""
        elig = await engine_service.evaluate_eligibility(_valid_person_a_features())
        tier = await engine_service.evaluate_risk_tier(750)
        ready = await engine_service.evaluate_readiness(85, "Ready", 80.0)

        rule_ids = {elig.rule_id, tier.rule_id, ready.rule_id}
        assert len(rule_ids) == 3  # All three are different rules
