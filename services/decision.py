from sqlalchemy.orm import Session
from models.session import ApplicationSession
from schemas.events import OrchestratorEvent, EventType
from services.orchestrator import process_event

def accept_counter_offer(db: Session, session_id: str, actor: str = "api_client") -> ApplicationSession:
    """
    User explicitly accepts the optimized counter-offer.
    Transitions from NEARLY_READY to READY.
    """
    event = OrchestratorEvent(
        session_id=session_id,
        event_type=EventType.USER_ACCEPTS_COUNTER_OFFER,
        payload={}
    )
    return process_event(db, event, actor=actor)

def reject_counter_offer(db: Session, session_id: str, actor: str = "api_client") -> ApplicationSession:
    """
    User explicitly rejects the optimized counter-offer.
    Transitions from NEARLY_READY to NOT_READY_YET.
    """
    event = OrchestratorEvent(
        session_id=session_id,
        event_type=EventType.USER_REJECTS_COUNTER_OFFER,
        payload={}
    )
    return process_event(db, event, actor=actor)

from models.applicant import ApplicantProfile

def submit_coapplicant(db: Session, session_id: str, coapplicant_data: dict, actor: str = "api_client") -> ApplicationSession:
    """
    User opts to add a co-applicant to boost income capacity.
    Transitions from NEARLY_READY back to PENDING_VERIFICATION.
    """
    profile = ApplicantProfile(
        session_id=session_id,
        is_co_applicant=True,
        full_name=coapplicant_data.get("full_name"),
        national_id=coapplicant_data.get("national_id"),
        pincode=coapplicant_data.get("pincode")
    )
    db.add(profile)

    event = OrchestratorEvent(
        session_id=session_id,
        event_type=EventType.USER_SUBMITS_COAPPLICANT,
        payload=coapplicant_data
    )
    return process_event(db, event, actor=actor)
