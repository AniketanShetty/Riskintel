from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field

# --- Sub-models for responses ---

class EligibilityResponse(BaseModel):
    verdict: Literal["Highly Likely", "Likely", "Borderline", "Unlikely"]
    probability: float
    bias: float
    feature_contributions: Dict[str, float]

class RiskTierThresholds(BaseModel):
    P1: str
    P2: str
    P3: str
    P4: str

class RiskTierResponse(BaseModel):
    tier: Literal["P1", "P2", "P3", "P4"]
    label: str
    description: str
    score_used: int
    thresholds: RiskTierThresholds

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
