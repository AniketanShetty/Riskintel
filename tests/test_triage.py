import pytest
from sqlalchemy.exc import IntegrityError
from services.intake import create_application, submit_application
from services.triage import run_triage_evaluation
from models.session import ApplicationSession
from models.enums import BureauGateStatus
from models.applicant import ApplicantProfile
from models.verification import VerificationRecord, OptimizationResult
from models.state_event import StateTransitionEvent

def setup_triage_session(db_session, payload):
    session_obj = create_application(db_session, payload)
    submit_application(db_session, session_obj.id, actor="test_user")
    return session_obj.id

def test_triage_pass(db_session):
    payload = {
        "loan_amount": 10000,
        "loan_term": 12,
        "loan_purpose": "medical",
        "income_bracket": "30k-40k", # Base 15000, Target EMI 833 -> pass
        "full_name": "Pass User",
        "national_id": "1111111111",
        "pincode": "123456"
    }
    session_id = setup_triage_session(db_session, payload)
    
    updated_session = run_triage_evaluation(db_session, session_id, BureauGateStatus.PRIME)
    
    assert updated_session.current_state == "PENDING_VERIFICATION"
    assert updated_session.state_events[-1].trigger_event == "TRIAGE_MATH_PASS"

def test_triage_math_fail(db_session):
    payload = {
        "loan_amount": 500000, # 5L over 12 months -> ~41k EMI. 
        "loan_term": 12,
        "loan_purpose": "medical",
        "income_bracket": "10k-20k", # Base 6000. 41k is > 1.5 * 6k. -> fail
        "full_name": "Fail User",
        "national_id": "2222222222",
        "pincode": "123456"
    }
    session_id = setup_triage_session(db_session, payload)
    
    updated_session = run_triage_evaluation(db_session, session_id, BureauGateStatus.PRIME)
    
    assert updated_session.current_state == "NOT_READY_YET"
    assert updated_session.state_events[-1].trigger_event == "TRIAGE_MATH_FAIL"

def test_triage_bureau_fail(db_session):
    payload = {
        "loan_amount": 10000,
        "loan_term": 12,
        "loan_purpose": "medical",
        "income_bracket": "30k-40k",
        "full_name": "Thin File",
        "national_id": "3333333333",
        "pincode": "123456"
    }
    session_id = setup_triage_session(db_session, payload)
    
    updated_session = run_triage_evaluation(db_session, session_id, BureauGateStatus.THIN_FILE)
    
    assert updated_session.current_state == "NOT_READY_YET"
    assert updated_session.state_events[-1].trigger_event == "BUREAU_TRUST_FAIL"
