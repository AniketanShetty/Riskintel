import pytest
from sqlalchemy.exc import IntegrityError
from services.intake import create_application, submit_application
from services.triage import run_triage_evaluation
from services.verification import process_aa_webhook
from services.optimization import run_optimization
from models.session import ApplicationSession
from models.enums import BureauGateStatus
from models.verification import OptimizationResult
from models.state_event import StateTransitionEvent

def setup_optimization_session(db_session, payload, verified_income):
    session_obj = create_application(db_session, payload)
    submit_application(db_session, session_obj.id, actor="test_user")
    run_triage_evaluation(db_session, session_obj.id, BureauGateStatus.PRIME)
    process_aa_webhook(db_session, session_obj.id, {"status": "SUCCESS", "verified_income": verified_income})
    return session_obj.id

def test_optimization_ready(db_session):
    payload = {
        "loan_amount": 10000,
        "loan_term": 12,
        "loan_purpose": "working_capital", # divisible
        "income_bracket": "30k-40k", 
        "full_name": "Ready User",
        "national_id": "1111111111",
        "pincode": "123456"
    }
    # User makes 50000, target EMI for 10k over 12 months is ~917. Extremely affordable.
    session_id = setup_optimization_session(db_session, payload, verified_income=50000)
    
    updated_session = run_optimization(db_session, session_id, annual_rate=0.18)
    
    assert updated_session.current_state == "READY"
    assert len(updated_session.optimization_results) == 1
    assert updated_session.optimization_results[-1].approved_loan_amount == 10000
    assert updated_session.optimization_results[-1].decision_verdict == "READY"

def test_optimization_nearly_ready(db_session):
    payload = {
        "loan_amount": 100000,
        "loan_term": 12,
        "loan_purpose": "working_capital", # divisible
        "income_bracket": "30k-40k", 
        "full_name": "Nearly Ready User",
        "national_id": "2222222222",
        "pincode": "123456"
    }
    # 100k over 12m = ~9168 EMI. User makes 6000. So we stretch tenure or reduce principal.
    session_id = setup_optimization_session(db_session, payload, verified_income=6000)
    
    updated_session = run_optimization(db_session, session_id, annual_rate=0.18)
    
    assert updated_session.current_state == "NEARLY_READY"
    assert len(updated_session.optimization_results) == 1
    assert updated_session.optimization_results[-1].decision_verdict == "NEARLY_READY"

def test_optimization_fail(db_session):
    payload = {
        "loan_amount": 100000,
        "loan_term": 12,
        "loan_purpose": "medical", # indivisible
        "income_bracket": "30k-40k", 
        "full_name": "Fail User",
        "national_id": "3333333333",
        "pincode": "123456"
    }
    # 5L over 12m = ~45k EMI. Indivisible, so we can't reduce principal. Max stretch 60m = ~12k EMI. User makes 2000. It will fail.
    session_id = setup_optimization_session(db_session, payload, verified_income=2000)
    
    updated_session = run_optimization(db_session, session_id, annual_rate=0.18)
    
    assert updated_session.current_state == "NOT_READY_YET"
    assert len(updated_session.optimization_results) == 1
    
    result = updated_session.optimization_results[-1]
    assert result.decision_verdict == "NOT_READY_YET"
    assert result.approved_loan_amount is None
    assert result.approved_tenure is None
    assert result.contract_emi > 0
    # Audit trail survives
    assert result.target_emi > 0
    assert result.available_capacity == 2000
