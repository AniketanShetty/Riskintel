import pytest
from sqlalchemy.exc import IntegrityError
from services.intake import create_application, submit_application
from services.triage import run_triage_evaluation
from services.verification import process_aa_webhook, process_fo_webhook, submit_reprompt_data
from models.session import ApplicationSession
from models.enums import BureauGateStatus, VerificationStatus
from models.applicant import ApplicantProfile
from models.verification import VerificationRecord, OptimizationResult
from models.state_event import StateTransitionEvent

def setup_verification_session(db_session, payload):
    session_obj = create_application(db_session, payload)
    submit_application(db_session, session_obj.id, actor="test_user")
    run_triage_evaluation(db_session, session_obj.id, BureauGateStatus.PRIME)
    return session_obj.id

def test_aa_success(db_session):
    payload = {
        "loan_amount": 10000,
        "loan_term": 12,
        "loan_purpose": "medical",
        "income_bracket": "30k-40k", 
        "full_name": "AA User",
        "national_id": "1111111111",
        "pincode": "123456"
    }
    session_id = setup_verification_session(db_session, payload)
    
    updated_session = process_aa_webhook(db_session, session_id, {"status": "SUCCESS", "verified_income": 35000})
    
    assert updated_session.current_state == "VERIFIED"
    assert updated_session.verifications[0].verified_monthly_cash_income == 35000

def test_aa_retry_exhaustion_fallback(db_session):
    payload = {
        "loan_amount": 10000,
        "loan_term": 12,
        "loan_purpose": "medical",
        "income_bracket": "30k-40k", 
        "full_name": "AA Retry User",
        "national_id": "1111111111",
        "pincode": "123456"
    }
    session_id = setup_verification_session(db_session, payload)
    
    # 1st fail
    updated_session = process_aa_webhook(db_session, session_id, {"status": "FAILED"})
    assert updated_session.current_state == "PENDING_VERIFICATION"
    
    # 2nd fail
    updated_session = process_aa_webhook(db_session, session_id, {"status": "TIMEOUT"})
    assert updated_session.current_state == "PENDING_VERIFICATION"
    
    # 3rd fail -> FSM triggers fallback, but state remains PENDING_VERIFICATION (waiting for FO)
    updated_session = process_aa_webhook(db_session, session_id, {"status": "FAILED"})
    assert updated_session.current_state == "PENDING_VERIFICATION"
    assert updated_session.state_events[-1].trigger_event == "AA_PULL_EXHAUSTED_FALLBACK"

def test_fo_reprompt_flow(db_session):
    payload = {
        "loan_amount": 10000,
        "loan_term": 12,
        "loan_purpose": "medical",
        "income_bracket": "30k-40k", 
        "full_name": "FO User",
        "national_id": "1111111111",
        "pincode": "123456"
    }
    session_id = setup_verification_session(db_session, payload)
    
    # FO requests secondary contact
    updated_session = process_fo_webhook(db_session, session_id, {"status": "MISSING_SECONDARY_CONTACT"})
    assert updated_session.current_state == "PENDING_REPROMPT"
    
    # User provides it
    updated_session = submit_reprompt_data(db_session, session_id, "+91-9876543210")
    assert updated_session.current_state == "PENDING_VERIFICATION"
    
    # FO passes
    updated_session = process_fo_webhook(db_session, session_id, {"status": "VERIFIED_CLEAN", "verified_income": 36000})
    assert updated_session.current_state == "VERIFIED"
    assert updated_session.verifications[-1].verified_monthly_cash_income == 36000
