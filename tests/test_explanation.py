import pytest
from services.explanation import generate_decision_explanation
from models.session import ApplicationSession
from models.verification import OptimizationResult
from models.state_event import StateTransitionEvent
import models.applicant  # required for sqlalchemy mapper initialization

def test_explanation_ready():
    session = ApplicationSession(current_state="READY", loan_amount=20000, loan_term=12)
    opt_result = OptimizationResult(
        approved_loan_amount=20000,
        approved_tenure=12,
        contract_emi=1833,
        decision_verdict="READY",
        primary_reason="OK",
        repayment_trust="PASS",
        available_capacity=3000
    )
    session.optimization_results = [opt_result]

    explanation = generate_decision_explanation(session)
    assert explanation is not None
    assert explanation.approved_terms is not None
    assert explanation.approved_terms.final_loan_amount == 20000
    assert explanation.approved_terms.monthly_emi == 1833
    assert explanation.counter_offer is None

def test_explanation_nearly_ready():
    session = ApplicationSession(current_state="NEARLY_READY", loan_amount=20000, loan_term=12)
    opt_result = OptimizationResult(
        approved_loan_amount=20000,
        approved_tenure=24,
        contract_emi=980,
        decision_verdict="NEARLY_READY",
        primary_reason="Affordability alternative found",
        repayment_trust="PASS",
        available_capacity=1000
    )
    session.optimization_results = [opt_result]

    explanation = generate_decision_explanation(session)
    assert explanation is not None
    assert explanation.counter_offer is not None
    assert explanation.counter_offer.proposed_tenure_months == 24
    assert explanation.counter_offer.proposed_monthly_emi == 980
    assert explanation.approved_terms is None

def test_explanation_not_ready_yet_math_wall():
    session = ApplicationSession(current_state="NOT_READY_YET")
    event = StateTransitionEvent(trigger_event="MATH_WALL_HIT", from_state="OPTIMIZATION", to_state="NOT_READY_YET", actor="system")
    session.state_events = [event]

    explanation = generate_decision_explanation(session)
    assert explanation is not None
    assert explanation.rejection_details is not None
    assert "too high" in explanation.rejection_details.reason
    assert "smaller amount" in explanation.rejection_details.actionable_advice

def test_explanation_not_ready_yet_bureau():
    session = ApplicationSession(current_state="NOT_READY_YET")
    event = StateTransitionEvent(trigger_event="BUREAU_TRUST_FAIL", from_state="TRIAGE", to_state="NOT_READY_YET", actor="system")
    session.state_events = [event]

    explanation = generate_decision_explanation(session)
    assert explanation is not None
    assert explanation.rejection_details is not None
    assert "credit history" in explanation.rejection_details.reason

def test_explanation_pending_reprompt():
    session = ApplicationSession(current_state="PENDING_REPROMPT")
    explanation = generate_decision_explanation(session)
    assert explanation is not None
    assert explanation.reprompt_requirements is not None
    assert "secondary_contact_number" in explanation.reprompt_requirements.missing_fields

def test_explanation_other_states():
    session = ApplicationSession(current_state="INTAKE")
    explanation = generate_decision_explanation(session)
    assert explanation is None
