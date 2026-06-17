from sqlalchemy.orm import Session
from models.session import ApplicationSession
from models.applicant import ApplicantProfile
from schemas.events import OrchestratorEvent, EventType
from services.orchestrator import process_event

def create_application(db: Session, payload: dict) -> ApplicationSession:
    """
    Parses the raw intake payload, instantiates the DB models, and commits
    to generate the UUID anchor. The state starts at INTAKE.
    """
    # Create the root session
    session_obj = ApplicationSession(
        loan_amount=payload["loan_amount"],
        loan_term=payload["loan_term"],
        loan_purpose=payload["loan_purpose"],
        income_bracket=payload["income_bracket"]
    )
    
    # Create the primary applicant profile
    primary_applicant = ApplicantProfile(
        is_co_applicant=False,
        full_name=payload["full_name"],
        national_id=payload["national_id"],
        pincode=payload["pincode"]
    )
    
    session_obj.primary_applicant = primary_applicant
    
    db.add(session_obj)
    db.flush()
    db.refresh(session_obj)
    
    return session_obj

def submit_application(db: Session, session_id: str, actor: str = "system") -> ApplicationSession:
    """
    Triggers the transition from INTAKE to TRIAGE using the Orchestrator.
    """
    event = OrchestratorEvent(
        session_id=session_id,
        event_type=EventType.INTAKE_SUBMISSION,
        payload={}
    )
    
    # Process event atomically locks row, advances state, appends ledger, and commits.
    updated_session = process_event(db, event, actor=actor)
    return updated_session
