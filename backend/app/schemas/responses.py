from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field

# --- Sub-models for responses ---

class EligibilityResponse(BaseModel):
    verdict: Literal["Highly Likely", "Likely", "Borderline", "Unlikely"]
    probability: float
    bias: float
    feature_contributions: Dict[str, float]
    policy_override_applied: Optional[bool] = False

class RiskTierThresholds(BaseModel):
    P1: str
    P2: str
    P3: str
    P4: str

class RiskTierThresholdValues(BaseModel):
    """Engine-provided SSOT numeric thresholds (governance refactor 2026-06-07)."""
    p1_min: int
    p2_min: int
    p2_max: int
    p3_min: int
    p3_max: int
    p4_max: int

class RiskTierResponse(BaseModel):
    tier: Literal["P1", "P2", "P3", "P4"]
    label: str
    description: str
    score_used: int
    thresholds: RiskTierThresholds
    # Additive SSOT: numeric threshold values actually used by the engine.
    # Frontend may read thresholds for display and threshold_values for
    # programmatic comparison. Optional to preserve backwards compatibility.
    threshold_values: Optional[RiskTierThresholdValues] = None

class ArchetypeResponse(BaseModel):
    label: str
    description: str
    cluster_id: int
    is_unclassified: bool = False

class ExplanationFactor(BaseModel):
    feature: str
    value: Any
    evidence: str
    reason: str
    improvement_advice: str
    advice_type: Optional[Literal["evidence_based", "inferred", "generic"]] = "generic"
    evidence_sources: Optional[List[str]] = None

class DecisionExplanation(BaseModel):
    decision_verdict: str
    primary_reason: str
    contributing_factors: List[ExplanationFactor]

class ReadinessFactor(BaseModel):
    score: int
    weight: float
    factors: Dict[str, Any]

class ReadinessComponents(BaseModel):
    financial_health: ReadinessFactor
    housing_stability: ReadinessFactor
    infrastructure_access: ReadinessFactor
    household_burden: ReadinessFactor
    business_viability: ReadinessFactor

class ReadinessResponse(BaseModel):
    score: int
    band: Literal["Ready", "Moderately Ready", "Needs Improvement", "Not Ready"]
    components: ReadinessComponents
    metadata: Optional[Dict[str, Any]] = None

# PersonBRecommendations replaced by DecisionExplanation
# --- Main Success Responses ---

class RoutingDecision(BaseModel):
    original_user_type: str
    routed_to: str
    reason: str

class PersonAResponse(BaseModel):
    status: Literal["success"]
    user_type: Literal["person_a"]
    timestamp: str
    correlation_id: str
    routing_decision: RoutingDecision
    applicant: dict
    eligibility: EligibilityResponse
    risk_tier: RiskTierResponse
    archetype: ArchetypeResponse
    explanation: DecisionExplanation

class PersonBResponse(BaseModel):
    status: Literal["success"]
    user_type: Literal["person_b"]
    timestamp: str
    correlation_id: str
    routing_decision: RoutingDecision
    applicant: dict
    readiness: ReadinessResponse
    archetype: ArchetypeResponse
    explanation: DecisionExplanation

# --- Error Responses ---

class ValidationDetail(BaseModel):
    field: str
    value: Any
    rule: str
    message: str

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[List[ValidationDetail]] = None

class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    error: ErrorDetail
