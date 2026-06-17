from schemas.events import EventType

class InvalidTransitionError(Exception):
    pass

# The core transition logic uses raw ApplicationState strings to bridge the DB constraints.
# The EventType enum strictly enforces the canonical incoming events.

TRANSITIONS = {
    # INTAKE
    ("INTAKE", EventType.INTAKE_SUBMISSION.value): "TRIAGE",
    
    # TRIAGE
    ("TRIAGE", EventType.TRIAGE_MATH_PASS.value): "PENDING_VERIFICATION",
    ("TRIAGE", EventType.TRIAGE_MATH_FAIL.value): "NOT_READY_YET",
    ("TRIAGE", EventType.BUREAU_TRUST_FAIL.value): "NOT_READY_YET",
    
    # PENDING_VERIFICATION (AA)
    ("PENDING_VERIFICATION", EventType.AA_PULL_FAILED_RETRY.value): "PENDING_VERIFICATION",
    ("PENDING_VERIFICATION", EventType.AA_PULL_EXHAUSTED_FALLBACK.value): "PENDING_VERIFICATION",
    ("PENDING_VERIFICATION", EventType.AA_PULL_EMPTY.value): "PENDING_VERIFICATION",
    ("PENDING_VERIFICATION", EventType.AA_SUCCESS.value): "VERIFIED",
    
    # PENDING_VERIFICATION (FO / Fallback)
    ("PENDING_VERIFICATION", EventType.FO_UNREACHABLE_RETRY.value): "PENDING_VERIFICATION",
    ("PENDING_VERIFICATION", EventType.FO_UNREACHABLE_MAX_RETRIES.value): "NOT_READY_YET",
    ("PENDING_VERIFICATION", EventType.FO_UNREACHABLE_TTL_EXPIRED.value): "NOT_READY_YET",
    ("PENDING_VERIFICATION", EventType.USER_REFUSAL.value): "NOT_READY_YET",
    ("PENDING_VERIFICATION", EventType.FO_FRAUD_DETECTED.value): "NOT_READY_YET",
    
    # Reprompt Loop
    ("PENDING_VERIFICATION", EventType.MISSING_SECONDARY_CONTACT.value): "PENDING_REPROMPT",
    ("PENDING_REPROMPT", EventType.REPROMPT_SUBMISSION_RECEIVED.value): "PENDING_VERIFICATION",
    ("PENDING_REPROMPT", EventType.REPROMPT_TIMEOUT_EXPIRED.value): "NOT_READY_YET",
    
    # Verification Success
    ("PENDING_VERIFICATION", EventType.FO_VERIFIED_CLEAN.value): "VERIFIED",
    ("PENDING_VERIFICATION", EventType.FO_VERIFIED_WITH_VARIANCE.value): "VERIFIED",
    
    # OPTIMIZATION
    ("VERIFIED", EventType.VERIFICATION_PAYLOAD_PROCESSED.value): "OPTIMIZATION",
    
    ("OPTIMIZATION", EventType.AFFORDABILITY_TARGET_MET.value): "READY",
    ("OPTIMIZATION", EventType.AFFORDABILITY_ALTERNATIVE_FOUND.value): "NEARLY_READY",
    ("OPTIMIZATION", EventType.MATH_WALL_HIT.value): "NOT_READY_YET",
    
    # NEARLY_READY
    ("NEARLY_READY", EventType.USER_SUBMITS_COAPPLICANT.value): "PENDING_VERIFICATION",
    ("NEARLY_READY", EventType.USER_ACCEPTS_COUNTER_OFFER.value): "READY",
    ("NEARLY_READY", EventType.USER_REJECTS_COUNTER_OFFER.value): "NOT_READY_YET",
    ("NEARLY_READY", EventType.COUNTER_OFFER_EXPIRED.value): "NOT_READY_YET",
    
    # NOT_READY_YET
    ("NOT_READY_YET", EventType.USER_SUBMITS_COAPPLICANT.value): "PENDING_VERIFICATION",
}

def get_next_state(current_state: str, event_type: EventType | str) -> str:
    # Safely extract value if an Enum is passed, otherwise use string
    event_val = event_type.value if isinstance(event_type, EventType) else event_type
    next_state = TRANSITIONS.get((current_state, event_val))
    if not next_state:
        raise InvalidTransitionError(f"Event '{event_val}' not allowed from state '{current_state}'")
    return next_state

def is_transition_allowed(current_state: str, event_type: EventType | str) -> bool:
    event_val = event_type.value if isinstance(event_type, EventType) else event_type
    return (current_state, event_val) in TRANSITIONS

# Set of all states logically present in the Graph
ALL_STATES = {
    "INTAKE", "TRIAGE", "PENDING_VERIFICATION",
    "PENDING_REPROMPT", "VERIFIED", "OPTIMIZATION", "READY",
    "NEARLY_READY", "NOT_READY_YET"
}
