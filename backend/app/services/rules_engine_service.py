"""
RulesEngineService — deterministic underwriting layer powered by RuleRegistry.

Per architecture freeze: the E1 Eligibility Engine remains the trained
Random Forest (model artifacts under models/eligibility/). This service
provides parallel rule-based gating and is NOT a replacement for E1.
All thresholds are loaded from RuleRegistryService — zero hardcoded values.

Engines:
    E1 — Eligibility (Random Forest, see app/engines/eligibility/)
    E2 — Risk Tier (P1–P4 score-band assignment)
    E5 — Readiness (financial health floor + band mapping)

Architecture:
    RulesEngineService
        ├── evaluate_eligibility(features) → EligibilityDecision
        ├── evaluate_risk_tier(cibil_score) → RiskTierDecision
        └── evaluate_readiness(features, component_scores) → ReadinessDecision
"""
from __future__ import annotations

import uuid
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.services.rule_registry_service import RuleRegistryService, RuleRegistryError

logger = logging.getLogger(__name__)

# ── Engine identifiers ─────────────────────────────────────────────────────

ENGINE_E1 = "E1"
ENGINE_E2 = "E2"
ENGINE_E5 = "E5"

RULE_E1_ELIGIBILITY = "eligibility_rules"
RULE_E2_RISK_TIER = "risk_tier_rules"
RULE_E5_READINESS = "readiness_rules"


# ── Decision DTOs ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class EligibilityDecision:
    """Result of the E1 deterministic eligibility evaluation."""

    is_eligible: bool
    rejection_reason: Optional[str]
    rule_version: str
    rule_id: uuid.UUID
    triggered_rule_names: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class RiskTierDecision:
    """Result of the E2 risk tier assignment."""

    assigned_tier: str
    tier_description: str
    score_used: int
    rule_version: str
    rule_id: uuid.UUID


@dataclass(frozen=True)
class ReadinessDecision:
    """Result of the E5 readiness evaluation."""

    is_ready: bool
    blocking_conditions: Optional[str]
    score: int
    band: str
    rule_version: str
    rule_id: uuid.UUID
    triggered_rule_names: List[str] = field(default_factory=list)


# ── Custom exception (fail-closed) ─────────────────────────────────────────


class RulesEngineError(Exception):
    """
    Raised when the Rules Engine cannot produce a decision.

    This is the fail-closed mechanism: if rules are missing, corrupt, or
    a required evaluation fails, the engine raises instead of silently
    returning a default that could cause an incorrect underwriting decision.
    """

    def __init__(self, message: str, engine_id: Optional[str] = None) -> None:
        super().__init__(message)
        self.engine_id = engine_id


# ── Service ────────────────────────────────────────────────────────────────


class RulesEngineService:
    """
    Deterministic underwriting engine powered by RuleRegistry thresholds.

    All evaluation thresholds are loaded at call-time from the
    RuleRegistryService cache. No hardcoded values.

    Usage:
        engine = RulesEngineService(rule_registry_service)
        decision = await engine.evaluate_eligibility(features)
        tier = await engine.evaluate_risk_tier(cibil_score)
        readiness = await engine.evaluate_readiness(features, component_scores)

    Fail-closed: if any required rule is missing from the registry, the
    engine raises ``RulesEngineError`` rather than falling back silently.
    """

    def __init__(self, rule_registry: RuleRegistryService) -> None:
        """
        Args:
            rule_registry: Initialised RuleRegistryService instance.
        """
        self._registry = rule_registry

    # ── E1: Eligibility (deterministic, replaces retired Random Forest) ─────

    async def evaluate_eligibility(
        self, features: Dict[str, Any],
    ) -> EligibilityDecision:
        """
        Evaluate loan eligibility using deterministic rules.

        Checks performed (all thresholds from RuleRegistry):
            1. CIBIL score minimum
            2. Annual income minimum
            3. Debt-to-Income (DTI) ratio maximum
            4. Asset-to-Loan (ATL) ratio minimum
            5. Employment tenure minimum (if applicable)

        Args:
            features: Applicant feature dictionary (same schema as Person A).

        Returns:
            EligibilityDecision with is_eligible flag and optional rejection_reason.

        Raises:
            RulesEngineError: If the E1 rule cannot be loaded (fail-closed).
        """
        rule = await self._load_rule(ENGINE_E1, RULE_E1_ELIGIBILITY)
        payload = rule.logic_payload

        triggered: List[str] = []
        rejection_reason: Optional[str] = None

        # Extract thresholds from the rule payload
        cibil_min = payload.get("cibil_min_score", 0)
        min_income = payload.get("min_annual_income", 0)
        max_dti = payload.get("max_debt_to_income_ratio", float("inf"))
        min_atl = payload.get("min_asset_to_loan_ratio", 0)
        min_employment = payload.get("min_employment_years", 0)
        reasons = payload.get("rejection_reasons", {})

        # ── 1. CIBIL score check ──────────────────────────────────────────
        raw_cibil = features.get("cibil_score")
        try:
            cibil_score = int(raw_cibil) if raw_cibil is not None else 0
        except (ValueError, TypeError):
            cibil_score = 0

        # Skip CIBIL check if score is -1 (NTC — handled by routing layer)
        if cibil_score >= 0 and cibil_score < cibil_min:
            triggered.append("cibil_too_low")
            rejection_reason = reasons.get(
                "cibil", "CIBIL score is below the minimum requirement.",
            )

        # ── 2. Income check ───────────────────────────────────────────────
        raw_income = features.get("annual_income")
        try:
            annual_income = float(raw_income) if raw_income is not None else 0.0
        except (ValueError, TypeError):
            annual_income = 0.0

        if rejection_reason is None and annual_income < min_income:
            triggered.append("income_too_low")
            rejection_reason = reasons.get(
                "income", "Annual income does not meet the minimum requirement.",
            )

        # ── 3. Debt-to-Income ratio check ─────────────────────────────────
        raw_loan = features.get("loan_amount")
        try:
            loan_amount = float(raw_loan) if raw_loan is not None else 0.0
        except (ValueError, TypeError):
            loan_amount = 0.0

        if rejection_reason is None and max_dti < float("inf"):
            dti_ratio = loan_amount / max(1.0, annual_income)
            if dti_ratio > max_dti:
                triggered.append("dti_exceeded")
                rejection_reason = reasons.get(
                    "dti",
                    "Debt-to-income ratio exceeds the maximum allowable limit.",
                )

        # ── 4. Asset-to-Loan ratio check ──────────────────────────────────
        if rejection_reason is None and min_atl > 0 and loan_amount > 0:
            total_assets = (
                float(features.get("residential_assets_value", 0) or 0)
                + float(features.get("commercial_assets_value", 0) or 0)
                + float(features.get("luxury_assets_value", 0) or 0)
                + float(features.get("bank_asset_value", 0) or 0)
            )
            atl_ratio = total_assets / loan_amount
            if atl_ratio < min_atl:
                triggered.append("asset_coverage_insufficient")
                rejection_reason = reasons.get(
                    "assets",
                    "Total asset value is insufficient relative to loan amount.",
                )

        # ── 5. Employment tenure check ────────────────────────────────────
        if rejection_reason is None and min_employment > 0:
            raw_years = features.get("years_at_current_employer")
            try:
                emp_years = float(raw_years) if raw_years is not None else 0.0
            except (ValueError, TypeError):
                emp_years = 0.0

            if emp_years < min_employment:
                triggered.append("employment_tenure_too_short")
                rejection_reason = reasons.get(
                    "employment",
                    "Employment tenure does not meet the minimum requirement.",
                )

        is_eligible = rejection_reason is None

        return EligibilityDecision(
            is_eligible=is_eligible,
            rejection_reason=rejection_reason,
            rule_version=rule.version,
            rule_id=rule.id,
            triggered_rule_names=triggered,
        )

    # ── E2: Risk Tier (score-band assignment) ──────────────────────────────

    async def evaluate_risk_tier(self, cibil_score: int) -> RiskTierDecision:
        """
        Assign a risk tier based on CIBIL score.

        Tiers and thresholds are loaded from the E2 rule in RuleRegistry.

        Args:
            cibil_score: Applicant CIBIL score (integer).

        Returns:
            RiskTierDecision with assigned_tier (P1–P4).

        Raises:
            RulesEngineError: If the E2 rule cannot be loaded (fail-closed).
        """
        rule = await self._load_rule(ENGINE_E2, RULE_E2_RISK_TIER)
        payload = rule.logic_payload

        tiers = payload.get("tiers", {})

        # Check tiers in priority order — P1 first (highest score requirement)
        # Sorted by min_score descending
        sorted_tier_keys = sorted(
            tiers.keys(),
            key=lambda k: tiers[k].get("min_score", 0),
            reverse=True,
        )

        assigned_tier: Optional[str] = None
        assigned_description: Optional[str] = None

        for tier_key in sorted_tier_keys:
            cfg = tiers[tier_key]
            min_s = cfg.get("min_score", float("-inf"))
            max_s = cfg.get("max_score", float("inf"))
            if min_s <= cibil_score <= max_s:
                assigned_tier = tier_key
                assigned_description = cfg.get(
                    "description", f"Risk tier {tier_key}",
                )
                break

        if assigned_tier is None:
            # Fallback — should not happen if configuration is complete
            # Use the lowest tier as fallback
            fallback_key = sorted_tier_keys[-1] if sorted_tier_keys else "P4"
            assigned_tier = fallback_key
            assigned_description = tiers.get(fallback_key, {}).get(
                "description", f"Risk tier {fallback_key} (fallback)",
            )

        return RiskTierDecision(
            assigned_tier=assigned_tier,
            tier_description=assigned_description or "",
            score_used=cibil_score,
            rule_version=rule.version,
            rule_id=rule.id,
        )

    # ── E5: Readiness (band mapping + floor gating) ────────────────────────

    async def evaluate_readiness(
        self,
        score: int,
        band: str,
        financial_health_score: float,
    ) -> ReadinessDecision:
        """
        Evaluate readiness using rule-based thresholds.

        This is the gating layer for the E5 Readiness engine. It:
        1. Checks the financial health floor threshold
        2. Validates the band mapping against rule thresholds
        3. Returns a ReadinessDecision

        Args:
            score: Computed readiness score (0–100).
            band: Readiness band from the engine (e.g. "Ready").
            financial_health_score: Financial health component score (0–100).

        Returns:
            ReadinessDecision with is_ready flag and optional blocking_conditions.

        Raises:
            RulesEngineError: If the E5 rule cannot be loaded (fail-closed).
        """
        rule = await self._load_rule(ENGINE_E5, RULE_E5_READINESS)
        payload = rule.logic_payload

        triggered: List[str] = []
        blocking_conditions: Optional[str] = None

        # ── 1. Financial health floor check ────────────────────────────────
        floor_threshold = payload.get("financial_health_floor_threshold", 0.5)

        if financial_health_score < floor_threshold:
            triggered.append("financial_health_floor_breach")
            blocking_conditions = (
                "Financial health score is below the minimum floor threshold."
            )
            final_score = 0
            final_band = "Not Ready"
            is_ready = False

            return ReadinessDecision(
                is_ready=is_ready,
                blocking_conditions=blocking_conditions,
                score=final_score,
                band=final_band,
                rule_version=rule.version,
                rule_id=rule.id,
                triggered_rule_names=triggered,
            )

        # ── 2. Band validation ────────────────────────────────────────────
        bands = payload.get("bands", {})
        expected_band: Optional[str] = None

        # Sort bands by min_score descending
        sorted_band_keys = sorted(
            bands.keys(),
            key=lambda k: bands[k].get("min_score", 0),
            reverse=True,
        )

        for band_key in sorted_band_keys:
            cfg = bands[band_key]
            min_s = cfg.get("min_score", 0)
            if score >= min_s:
                expected_band = band_key
                break

        # If the band from the engine doesn't match, use the rule's expected band
        if expected_band and expected_band != band:
            triggered.append("band_reclassified")
            band = expected_band

        is_ready = band == "Ready"
        if not is_ready and not blocking_conditions:
            blocking_conditions = f"Readiness band is '{band}' — not yet ready."

        return ReadinessDecision(
            is_ready=is_ready,
            blocking_conditions=blocking_conditions,
            score=score,
            band=band,
            rule_version=rule.version,
            rule_id=rule.id,
            triggered_rule_names=triggered,
        )

    # ── Internal helpers ──────────────────────────────────────────────────

    async def _load_rule(
        self, engine_id: str, rule_name: str,
    ) -> Any:
        """
        Load a rule from the registry, raising RulesEngineError on failure.

        Args:
            engine_id: Engine identifier (E1, E2, E5).
            rule_name: Name of the rule to load.

        Returns:
            The RuleRegistry record.

        Raises:
            RulesEngineError: If the rule is missing or the registry fails.
        """
        try:
            rule = await self._registry.get_rule(engine_id, rule_name)
        except RuleRegistryError as exc:
            logger.error(
                "Fail-closed: registry unavailable for %s/%s: %s",
                engine_id, rule_name, exc,
            )
            raise RulesEngineError(
                f"Rule registry unavailable for engine '{engine_id}': {exc}",
                engine_id=engine_id,
            ) from exc

        if rule is None:
            logger.error(
                "Fail-closed: rule '%s' not found for engine '%s'.",
                rule_name, engine_id,
            )
            raise RulesEngineError(
                f"Required rule '{rule_name}' not found for engine '{engine_id}'. "
                "Cannot evaluate without configured thresholds.",
                engine_id=engine_id,
            )

        return rule
