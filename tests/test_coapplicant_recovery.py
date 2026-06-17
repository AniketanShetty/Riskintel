"""
Integration test: Co-Applicant Recovery Loop

Proves that the OptimizationResult versioning implementation correctly:
1. Produces attempt_number=1 after the first (solo) optimization run.
2. Preserves the attempt_number=1 row immutably while the session re-enters PENDING_VERIFICATION.
3. Produces attempt_number=2 after the second (co-applicant) optimization run.
4. Both historical rows remain individually queryable and correct.

FSM path exercised:
  INTAKE -> TRIAGE -> PENDING_VERIFICATION -> VERIFIED -> OPTIMIZATION
  -> NEARLY_READY -> PENDING_VERIFICATION -> VERIFIED -> OPTIMIZATION -> READY
"""
import pytest
from sqlalchemy import func
from services.intake import create_application, submit_application
from services.triage import run_triage_evaluation
from services.verification import process_aa_webhook
from services.optimization import run_optimization
from services.orchestrator import process_event
from models.verification import OptimizationResult
from models.enums import BureauGateStatus
from schemas.events import OrchestratorEvent, EventType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_to_verified(db_session, payload, verified_income: int) -> str:
    """
    Drives a session from INTAKE through to VERIFIED.
    Returns the session_id.
    """
    session_obj = create_application(db_session, payload)
    submit_application(db_session, session_obj.id, actor="test_user")
    run_triage_evaluation(db_session, session_obj.id, BureauGateStatus.PRIME)
    process_aa_webhook(
        db_session,
        session_obj.id,
        {"status": "SUCCESS", "verified_income": verified_income},
    )
    return session_obj.id


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

def test_coapplicant_recovery_loop_produces_versioned_attempts(db_session):
    """
    Full integration test proving the co-applicant recovery loop produces
    OptimizationResult attempt_numbers [1, 2] and preserves historical outputs.
    """

    # ------------------------------------------------------------------ #
    # PHASE 1: Drive to NEARLY_READY via solo optimization                #
    # Primary applicant income is too low to satisfy the full principal.  #
    # This guarantees an AFFORDABILITY_ALTERNATIVE_FOUND outcome.         #
    # ------------------------------------------------------------------ #

    solo_payload = {
        "loan_amount": 100000,
        "loan_term": 12,
        "loan_purpose": "working_capital",   # DIVISIBLE — reduction allowed
        "income_bracket": "10k-20k",
        "full_name": "Primary Applicant",
        "national_id": "5555555551",
        "pincode": "560001",
    }

    session_id = _run_to_verified(db_session, solo_payload, verified_income=6000)

    # Run first optimization. Income=6000, EMI for 100k/12m ~= 9168 → NEARLY_READY.
    session_after_opt1 = run_optimization(db_session, session_id, annual_rate=0.18)

    # --- Assert: FSM landed in NEARLY_READY ---
    assert session_after_opt1.current_state == "NEARLY_READY", (
        f"Expected NEARLY_READY after first optimization, got {session_after_opt1.current_state}"
    )

    # --- Assert: Exactly one OptimizationResult row exists ---
    db_session.expire(session_after_opt1)
    db_session.refresh(session_after_opt1)
    assert len(session_after_opt1.optimization_results) == 1, (
        "Expected exactly 1 OptimizationResult after first run"
    )

    attempt_1 = session_after_opt1.optimization_results[0]

    # --- Assert: attempt_number is 1 ---
    assert attempt_1.attempt_number == 1, (
        f"Expected attempt_number=1, got {attempt_1.attempt_number}"
    )

    # --- Assert: Decision is NEARLY_READY ---
    assert attempt_1.decision_verdict == "NEARLY_READY", (
        f"Expected NEARLY_READY verdict, got {attempt_1.decision_verdict}"
    )

    # Snapshot the first attempt's approved values for later immutability check
    attempt_1_id = attempt_1.id
    attempt_1_approved_amount = attempt_1.approved_loan_amount
    attempt_1_available_capacity = attempt_1.available_capacity

    # ------------------------------------------------------------------ #
    # PHASE 2: Co-Applicant Recovery — re-enter verification loop        #
    # ------------------------------------------------------------------ #

    # Trigger USER_SUBMITS_COAPPLICANT: NEARLY_READY → PENDING_VERIFICATION
    coapplicant_event = OrchestratorEvent(
        session_id=session_id,
        event_type=EventType.USER_SUBMITS_COAPPLICANT,
        payload={}
    )
    session_after_coapp = process_event(db_session, coapplicant_event, actor="test_user")

    assert session_after_coapp.current_state == "PENDING_VERIFICATION", (
        f"Expected PENDING_VERIFICATION after coapplicant submission, "
        f"got {session_after_coapp.current_state}"
    )

    # --- Assert: The historical attempt_1 row is still intact ---
    rows_mid_recovery = db_session.query(OptimizationResult).filter_by(
        session_id=session_id
    ).order_by(OptimizationResult.attempt_number).all()

    assert len(rows_mid_recovery) == 1, (
        "Coapplicant submission must NOT delete or alter historical optimization rows"
    )
    assert rows_mid_recovery[0].id == attempt_1_id, (
        "Historical attempt_1 row identity must be preserved during recovery"
    )

    # ------------------------------------------------------------------ #
    # PHASE 3: Co-Applicant verification arrives (higher income)          #
    # Combined household income now satisfies the target EMI.             #
    # ------------------------------------------------------------------ #

    # Process AA webhook with co-applicant's higher income
    process_aa_webhook(
        db_session,
        session_id,
        {"status": "SUCCESS", "verified_income": 60000},
    )

    db_session.expire_all()
    session_pre_opt2 = db_session.query(
        __import__("models.session", fromlist=["ApplicationSession"]).ApplicationSession
    ).filter_by(id=session_id).first()

    assert session_pre_opt2.current_state == "VERIFIED", (
        f"Expected VERIFIED before second optimization, got {session_pre_opt2.current_state}"
    )

    # ------------------------------------------------------------------ #
    # PHASE 4: Second optimization run with combined household income     #
    # ------------------------------------------------------------------ #

    session_after_opt2 = run_optimization(db_session, session_id, annual_rate=0.18)

    assert session_after_opt2.current_state == "READY", (
        f"Expected READY after second optimization, got {session_after_opt2.current_state}"
    )

    # ------------------------------------------------------------------ #
    # PHASE 5: Full assertions on the versioned state of the table        #
    # ------------------------------------------------------------------ #

    db_session.expire(session_after_opt2)
    db_session.refresh(session_after_opt2)

    all_attempts = session_after_opt2.optimization_results
    assert len(all_attempts) == 2, (
        f"Expected exactly 2 OptimizationResult rows, got {len(all_attempts)}"
    )

    # --- Assert: attempt ordering is preserved ---
    assert all_attempts[0].attempt_number == 1
    assert all_attempts[1].attempt_number == 2

    attempt_2 = all_attempts[1]

    # --- Assert: attempt_2 decision is READY ---
    assert attempt_2.decision_verdict == "READY", (
        f"Expected READY for attempt_2, got {attempt_2.decision_verdict}"
    )

    # --- Assert: attempt_1 row is historically preserved and immutable ---
    attempt_1_reloaded = all_attempts[0]
    assert attempt_1_reloaded.id == attempt_1_id, (
        "Attempt 1 row UUID must not change"
    )
    assert attempt_1_reloaded.decision_verdict == "NEARLY_READY", (
        "Historical attempt_1 decision_verdict must remain NEARLY_READY"
    )
    assert attempt_1_reloaded.approved_loan_amount == attempt_1_approved_amount, (
        "Historical attempt_1 approved_loan_amount must not be overwritten"
    )
    assert attempt_1_reloaded.available_capacity == attempt_1_available_capacity, (
        "Historical attempt_1 available_capacity must not be overwritten"
    )

    # --- Assert: attempt_2 reflects the superior co-applicant income ---
    assert attempt_2.available_capacity > attempt_1_available_capacity, (
        "attempt_2 available_capacity must exceed attempt_1 (co-applicant income is higher)"
    )

    # --- Assert: composite unique constraint holds at DB level ---
    max_attempt_in_db = db_session.query(
        func.max(OptimizationResult.attempt_number)
    ).filter(
        OptimizationResult.session_id == session_id
    ).scalar()
    assert max_attempt_in_db == 2, (
        f"DB MAX(attempt_number) must be 2, got {max_attempt_in_db}"
    )

    # --- Assert: both rows are physically distinct ---
    assert all_attempts[0].id != all_attempts[1].id, (
        "Each attempt must have its own unique primary key"
    )
