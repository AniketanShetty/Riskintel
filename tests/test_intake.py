import pytest
from sqlalchemy.exc import IntegrityError
from services.intake import create_application, submit_application
from models.session import ApplicationSession
from models.applicant import ApplicantProfile
from models.verification import VerificationRecord, OptimizationResult
from models.state_event import StateTransitionEvent

def test_create_and_submit_application(db_session):
    payload = {
        "loan_amount": 25000,
        "loan_term": 24,
        "loan_purpose": "medical",
        "income_bracket": "30k-40k",
        "full_name": "Test User",
        "national_id": "9999999999",
        "pincode": "123456"
    }
    
    # 1. Create Application
    session_obj = create_application(db_session, payload)
    assert session_obj.id is not None
    assert session_obj.current_state == "INTAKE"
    assert session_obj.primary_applicant.full_name == "Test User"
    
    # 2. Submit Application
    updated_session = submit_application(db_session, session_obj.id, actor="test_user")
    assert updated_session.current_state == "TRIAGE"
    
    # 3. Verify ledger entry
    assert len(updated_session.state_events) == 1
    assert updated_session.state_events[0].trigger_event == "INTAKE_SUBMISSION"
