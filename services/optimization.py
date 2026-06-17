from sqlalchemy import func
from sqlalchemy.orm import Session
from models.session import ApplicationSession
from models.enums import DivisibilityClass
from models.verification import OptimizationResult
from schemas.events import OrchestratorEvent, EventType
from services.orchestrator import process_event
from services.optimization_math import optimize_loan

INDIVISIBLE_PURPOSES = ["medical", "education", "wedding", "two_wheeler"]

def run_optimization(db: Session, session_id: str, annual_rate: float = 0.18, actor: str = "optimizer") -> ApplicationSession:
    """
    Executes loan mathematics against verified capacity.
    """
    session_obj = db.query(ApplicationSession).with_for_update().filter_by(id=session_id).first()
    if not session_obj:
        raise ValueError(f"Session {session_id} not found.")

    if session_obj.current_state != "VERIFIED":
        raise ValueError(f"Session {session_id} is not in VERIFIED state.")

    event_start = OrchestratorEvent(
        session_id=session_id,
        event_type=EventType.VERIFICATION_PAYLOAD_PROCESSED,
        payload={}
    )
    # Move to OPTIMIZATION state, but don't commit yet to avoid double-commit gap
    session_obj = process_event(db, event_start, actor=actor, auto_commit=False)

    # Get verified capacity.
    # By rule, VERIFIED state means we have at least one successful VerificationRecord
    # We take the most recent one.
    successful_verifications = [
        v for v in session_obj.verifications 
        if v.verification_status in ("VERIFIED_CLEAN", "VERIFIED_WITH_VARIANCE")
    ]
    if not successful_verifications:
        raise ValueError(f"Cannot optimize session {session_id} without a successful verification.")
    
    last_verification = sorted(successful_verifications, key=lambda x: x.attempt_number)[-1]
    available_capacity = last_verification.verified_monthly_cash_income or 0

    # Determine divisibility
    is_divisible = session_obj.loan_purpose not in INDIVISIBLE_PURPOSES

    # Execute math engine
    output = optimize_loan(
        principal=session_obj.loan_amount,
        annual_rate=annual_rate,
        tenure_months=session_obj.loan_term,
        available_capacity=available_capacity,
        is_divisible=is_divisible
    )

    # Use MAX(attempt_number)+1 inside the same transaction to avoid
    # any ORM lazy-load or stale identity map issues.
    max_attempt = db.query(
        func.max(OptimizationResult.attempt_number)
    ).filter(
        OptimizationResult.session_id == session_id
    ).scalar() or 0
    next_attempt = max_attempt + 1

    # Persist the OptimizationResult
    result = OptimizationResult(
        session_id=session_id,
        attempt_number=next_attempt,
        repayment_trust="PASS" if available_capacity > 0 else "FAIL",
        available_capacity=available_capacity,
        target_emi=output.target_emi,
        contract_emi=output.contract_emi,
        approved_loan_amount=output.approved_loan_amount,
        approved_tenure=output.approved_tenure,
        coapplicant_required=output.coapplicant_required,
        decision_verdict=output.status,
        primary_reason="Optimization completed.",
        livelihood_resilience_pass=True
    )
    db.add(result)
    db.flush()

    # Route based on math engine output
    if output.status == "READY":
        event_type = EventType.AFFORDABILITY_TARGET_MET
    elif output.status == "NEARLY_READY":
        event_type = EventType.AFFORDABILITY_ALTERNATIVE_FOUND
    else:
        event_type = EventType.MATH_WALL_HIT

    event = OrchestratorEvent(
        session_id=session_id,
        event_type=event_type,
        payload={
            "approved_loan_amount": output.approved_loan_amount,
            "approved_tenure": output.approved_tenure,
            "contract_emi": output.contract_emi,
            "status": output.status
        }
    )

    return process_event(db, event, actor=actor)
