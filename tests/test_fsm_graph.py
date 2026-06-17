import pytest
from core.fsm_graph import TRANSITIONS, get_next_state, is_transition_allowed, InvalidTransitionError, ALL_STATES
from schemas.events import EventType

def test_happy_path_transitions():
    # Mandatory core flow tests using exact EventType
    assert get_next_state("INTAKE", EventType.INTAKE_SUBMISSION) == "TRIAGE"
    assert get_next_state("TRIAGE", EventType.TRIAGE_MATH_PASS) == "PENDING_VERIFICATION"
    assert get_next_state("PENDING_VERIFICATION", EventType.FO_UNREACHABLE_RETRY) == "PENDING_VERIFICATION"
    assert get_next_state("PENDING_VERIFICATION", EventType.FO_VERIFIED_CLEAN) == "VERIFIED"
    assert get_next_state("VERIFIED", EventType.VERIFICATION_PAYLOAD_PROCESSED) == "OPTIMIZATION"
    assert get_next_state("OPTIMIZATION", EventType.AFFORDABILITY_TARGET_MET) == "READY"
    assert get_next_state("OPTIMIZATION", EventType.AFFORDABILITY_ALTERNATIVE_FOUND) == "NEARLY_READY"
    assert get_next_state("OPTIMIZATION", EventType.MATH_WALL_HIT) == "NOT_READY_YET"

def test_invalid_transitions():
    # Ensure invalid events raise the expected error
    with pytest.raises(InvalidTransitionError):
        get_next_state("INTAKE", EventType.TRIAGE_MATH_PASS)
    
    with pytest.raises(InvalidTransitionError):
        get_next_state("READY", "any_event")
        
    assert is_transition_allowed("INTAKE", EventType.INTAKE_SUBMISSION) is True
    assert is_transition_allowed("VERIFIED", EventType.INTAKE_SUBMISSION) is False

def test_terminal_states():
    # A terminal state has no outbound transitions in the dictionary
    outbound_edges = {state for state, event in TRANSITIONS.keys()}
    terminal_states = ALL_STATES - outbound_edges
    
    assert "READY" in terminal_states
    assert "NOT_READY_YET" in terminal_states
    assert "INTAKE" not in terminal_states

def test_every_state_appears_in_graph():
    # Ensure all defined states are physically present in the graph (either as source or destination)
    all_sources = {state for state, event in TRANSITIONS.keys()}
    all_destinations = set(TRANSITIONS.values())
    graph_states = all_sources | all_destinations
    
    missing_from_graph = ALL_STATES - graph_states
    assert not missing_from_graph, f"States missing from FSM graph: {missing_from_graph}"

def test_no_duplicate_transitions():
    # Verify graph constraints
    assert len(TRANSITIONS) == len(EventType) # Every Enum value should map uniquely or identically

def test_reprompt_loop():
    assert get_next_state("PENDING_VERIFICATION", EventType.MISSING_SECONDARY_CONTACT) == "PENDING_REPROMPT"
    assert get_next_state("PENDING_REPROMPT", EventType.REPROMPT_SUBMISSION_RECEIVED) == "PENDING_VERIFICATION"
    assert get_next_state("PENDING_REPROMPT", EventType.REPROMPT_TIMEOUT_EXPIRED) == "NOT_READY_YET"

def test_recovery_loop():
    assert get_next_state("NEARLY_READY", EventType.USER_SUBMITS_COAPPLICANT) == "PENDING_VERIFICATION"
    assert get_next_state("NEARLY_READY", EventType.USER_ACCEPTS_COUNTER_OFFER) == "READY"
    assert get_next_state("NEARLY_READY", EventType.USER_REJECTS_COUNTER_OFFER) == "NOT_READY_YET"
