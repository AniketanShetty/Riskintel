import pytest
import uuid
from sqlalchemy.exc import IntegrityError
from schemas.events import OrchestratorEvent, EventType
from models.session import ApplicationSession
from models.applicant import ApplicantProfile
from models.verification import VerificationRecord, OptimizationResult
from models.state_event import StateTransitionEvent
from services.orchestrator import process_event, InvalidTransitionError, SessionNotFoundError

def test_orchestrator_happy_path(db_session):
    # 1. Setup Initial Session
    sess_id = str(uuid.uuid4())
    session_obj = ApplicationSession(
        id=sess_id,
        current_state="INTAKE",
        loan_amount=10000,
        loan_term=12,
        loan_purpose="medical",
        income_bracket="10k-20k"
    )
    db_session.add(session_obj)
    db_session.commit()

    # 2. Fire Event
    event = OrchestratorEvent(
        session_id=sess_id,
        event_type=EventType.INTAKE_SUBMISSION,
        payload={"ip_address": "127.0.0.1"}
    )
    
    updated_session = process_event(db_session, event, actor="user_agent")
    
    # 3. Assert State Mutation
    assert updated_session.current_state == "TRIAGE"
    
    # 4. Assert Audit Ledger
    audit_events = db_session.query(StateTransitionEvent).filter_by(session_id=sess_id).all()
    assert len(audit_events) == 1
    assert audit_events[0].from_state == "INTAKE"
    assert audit_events[0].to_state == "TRIAGE"
    assert audit_events[0].trigger_event == "INTAKE_SUBMISSION"
    assert audit_events[0].actor == "user_agent"

def test_orchestrator_invalid_transition(db_session):
    sess_id = str(uuid.uuid4())
    session_obj = ApplicationSession(
        id=sess_id,
        current_state="INTAKE",
        loan_amount=10000,
        loan_term=12,
        loan_purpose="medical",
        income_bracket="10k-20k"
    )
    db_session.add(session_obj)
    db_session.commit()

    # Fire an event that is not allowed from INTAKE
    event = OrchestratorEvent(
        session_id=sess_id,
        event_type=EventType.AA_SUCCESS,
        payload={}
    )
    
    with pytest.raises(InvalidTransitionError):
        process_event(db_session, event)
        
    # Ensure DB is cleanly rolled back and no audit event was saved
    audit_events = db_session.query(StateTransitionEvent).filter_by(session_id=sess_id).all()
    assert len(audit_events) == 0

def test_orchestrator_session_not_found(db_session):
    event = OrchestratorEvent(
        session_id=str(uuid.uuid4()),
        event_type=EventType.INTAKE_SUBMISSION,
        payload={}
    )
    with pytest.raises(SessionNotFoundError):
        process_event(db_session, event)
