from sqlalchemy.orm import Session
from models.session import ApplicationSession
from models.enums import BureauGateStatus
from schemas.events import OrchestratorEvent, EventType
from services.orchestrator import process_event

# Mock table for base capacity derived from income bracket
BASE_CAPACITY_TABLE = {
    "0-10k": 3000,
    "10k-20k": 6000,
    "20k-30k": 10000,
    "30k-40k": 15000,
    "40k-50k": 20000,
    "50k+": 30000,
}

def run_triage_evaluation(db: Session, session_id: str, bureau_status: BureauGateStatus, actor: str = "triage_engine") -> ApplicationSession:
    """
    Evaluates bureau trust and rudimentary mathematical capacity.
    Advances state to PENDING_VERIFICATION (if pass) or NOT_READY_YET (if fail).
    """
    # We must explicitly query to get current values before evaluation
    session_obj = db.query(ApplicationSession).with_for_update().filter_by(id=session_id).first()
    if not session_obj:
        raise ValueError(f"Session {session_id} not found.")

    # 1. Bureau Trust Check
    if bureau_status == BureauGateStatus.THIN_FILE:
        # A hard fail triggers the orchestrator immediately
        event = OrchestratorEvent(
            session_id=session_id,
            event_type=EventType.BUREAU_TRUST_FAIL,
            payload={"bureau_status": bureau_status.value}
        )
        return process_event(db, event, actor=actor)

    # 2. Mathematical Check
    base_capacity = BASE_CAPACITY_TABLE.get(session_obj.income_bracket, 0)
    
    # Very rudimentary check: If they are asking for 10x their monthly capacity, fail them early.
    target_emi = session_obj.loan_amount / session_obj.loan_term
    
    if target_emi > base_capacity * 1.5:  # Over 150% of assumed monthly capacity is a hard fail
        event = OrchestratorEvent(
            session_id=session_id,
            event_type=EventType.TRIAGE_MATH_FAIL,
            payload={
                "base_capacity": base_capacity,
                "target_emi": target_emi
            }
        )
    else:
        # Triage Pass
        event = OrchestratorEvent(
            session_id=session_id,
            event_type=EventType.TRIAGE_MATH_PASS,
            payload={
                "base_capacity": base_capacity,
                "bureau_status": bureau_status.value
            }
        )

    # The Orchestrator automatically handles the atomic commit and state change
    return process_event(db, event, actor=actor)
