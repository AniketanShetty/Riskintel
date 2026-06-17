import enum
from datetime import datetime
from typing import Any, Dict
from pydantic import BaseModel, Field

class EventType(str, enum.Enum):
    """
    Canonical Event Catalog for the Phase 2 Orchestrator.
    Every transition relies strictly on these exact constants.
    """
    # Intake & Triage
    INTAKE_SUBMISSION = "INTAKE_SUBMISSION"
    TRIAGE_MATH_PASS = "TRIAGE_MATH_PASS"
    TRIAGE_MATH_FAIL = "TRIAGE_MATH_FAIL"
    BUREAU_TRUST_FAIL = "BUREAU_TRUST_FAIL"
    
    # Account Aggregator (AA) Verification
    AA_PULL_FAILED_RETRY = "AA_PULL_FAILED_RETRY"
    AA_PULL_EXHAUSTED_FALLBACK = "AA_PULL_EXHAUSTED_FALLBACK"
    AA_PULL_EMPTY = "AA_PULL_EMPTY"
    AA_SUCCESS = "AA_SUCCESS"
    
    # Field Officer (FO) Verification
    FO_UNREACHABLE_RETRY = "FO_UNREACHABLE_RETRY"
    FO_UNREACHABLE_MAX_RETRIES = "FO_UNREACHABLE_MAX_RETRIES"
    FO_UNREACHABLE_TTL_EXPIRED = "FO_UNREACHABLE_TTL_EXPIRED"
    FO_FRAUD_DETECTED = "FO_FRAUD_DETECTED"
    USER_REFUSAL = "USER_REFUSAL"
    
    # Verification Success
    FO_VERIFIED_CLEAN = "FO_VERIFIED_CLEAN"
    FO_VERIFIED_WITH_VARIANCE = "FO_VERIFIED_WITH_VARIANCE"
    
    # Reprompt Loop
    MISSING_SECONDARY_CONTACT = "MISSING_SECONDARY_CONTACT"
    REPROMPT_SUBMISSION_RECEIVED = "REPROMPT_SUBMISSION_RECEIVED"
    REPROMPT_TIMEOUT_EXPIRED = "REPROMPT_TIMEOUT_EXPIRED"
    
    # Optimization Triggers
    VERIFICATION_PAYLOAD_PROCESSED = "VERIFICATION_PAYLOAD_PROCESSED"
    
    # Optimization Outputs
    AFFORDABILITY_TARGET_MET = "AFFORDABILITY_TARGET_MET"
    AFFORDABILITY_ALTERNATIVE_FOUND = "AFFORDABILITY_ALTERNATIVE_FOUND"
    MATH_WALL_HIT = "MATH_WALL_HIT"
    
    # Recovery Loop
    USER_SUBMITS_COAPPLICANT = "USER_SUBMITS_COAPPLICANT"
    USER_ACCEPTS_COUNTER_OFFER = "USER_ACCEPTS_COUNTER_OFFER"
    USER_REJECTS_COUNTER_OFFER = "USER_REJECTS_COUNTER_OFFER"
    COUNTER_OFFER_EXPIRED = "COUNTER_OFFER_EXPIRED"

class OrchestratorEvent(BaseModel):
    """
    The singular strongly-typed event contract consumed by the State Machine Orchestrator.
    """
    session_id: str = Field(..., description="UUID of the ApplicationSession")
    event_type: EventType = Field(..., description="Canonical event triggering transition")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event-specific metadata")
    occurred_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of event occurrence")

    class Config:
        use_enum_values = True
