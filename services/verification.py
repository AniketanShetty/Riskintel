from sqlalchemy.orm import Session
from models.session import ApplicationSession
from models.verification import VerificationRecord
from models.enums import VerificationSource, VerificationStatus, ArtifactType
from schemas.events import OrchestratorEvent, EventType
from services.orchestrator import process_event

def process_aa_webhook(db: Session, session_id: str, payload: dict, actor: str = "aa_webhook") -> ApplicationSession:
    """
    Handles incoming Account Aggregator payloads.
    """
    session_obj = db.query(ApplicationSession).with_for_update().filter_by(id=session_id).first()
    if not session_obj:
        raise ValueError(f"Session {session_id} not found.")

    status = payload.get("status")
    
    attempt_num = len(session_obj.verifications) + 1
    
    # Anti-Corruption Layer: Translate HTTP/Vendor status to Domain status
    if status == "SUCCESS":
        domain_status = VerificationStatus.VERIFIED_CLEAN
    elif status in ("EMPTY", "FAILED", "TIMEOUT"):
        domain_status = VerificationStatus.UNREACHABLE
    else:
        raise ValueError(f"Unknown AA status: {status}")

    # We must insert the verification record first to keep an audit trail
    record = VerificationRecord(
        session_id=session_id,
        attempt_number=attempt_num,
        verification_source=VerificationSource.ACCOUNT_AGGREGATOR,
        verification_status=domain_status,
        verified_monthly_cash_income=payload.get("verified_income")
    )
    db.add(record)
    db.flush() # Flush to populate session_obj.verifications and evaluate retry counts

    if status == "SUCCESS":
        event_type = EventType.AA_SUCCESS
    elif status == "EMPTY":
        event_type = EventType.AA_PULL_EMPTY
    else: # FAILED / TIMEOUT
        if session_obj.aa_retry_count >= 2:  # Account for 3 max attempts (1 initial + 2 retries)
            event_type = EventType.AA_PULL_EXHAUSTED_FALLBACK
        else:
            event_type = EventType.AA_PULL_FAILED_RETRY

    event = OrchestratorEvent(
        session_id=session_id,
        event_type=event_type,
        payload=payload
    )

    return process_event(db, event, actor=actor)

def process_fo_webhook(db: Session, session_id: str, payload: dict, actor: str = "fo_webhook") -> ApplicationSession:
    """
    Handles incoming Field Officer payloads.
    """
    session_obj = db.query(ApplicationSession).with_for_update().filter_by(id=session_id).first()
    if not session_obj:
        raise ValueError(f"Session {session_id} not found.")

    status = payload.get("status")

    attempt_num = len(session_obj.verifications) + 1

    if status in [e.value for e in VerificationStatus]:
        record = VerificationRecord(
            session_id=session_id,
            attempt_number=attempt_num,
            verification_source=VerificationSource.FIELD_OFFICER,
            verification_status=status,
            verified_monthly_cash_income=payload.get("verified_income")
        )
        db.add(record)
        db.flush()

    if status == "VERIFIED_CLEAN":
        event_type = EventType.FO_VERIFIED_CLEAN
    elif status == "VERIFIED_WITH_VARIANCE":
        event_type = EventType.FO_VERIFIED_WITH_VARIANCE
    elif status == "FRAUD_DETECTED":
        event_type = EventType.FO_FRAUD_DETECTED
    elif status == "UNREACHABLE":
        if session_obj.fo_retry_count >= 1:
            event_type = EventType.FO_UNREACHABLE_MAX_RETRIES
        else:
            event_type = EventType.FO_UNREACHABLE_RETRY
    elif status == "MISSING_SECONDARY_CONTACT":
        event_type = EventType.MISSING_SECONDARY_CONTACT
    elif status == "USER_REFUSAL":
        event_type = EventType.USER_REFUSAL
    else:
        raise ValueError(f"Unknown FO status: {status}")

    event = OrchestratorEvent(
        session_id=session_id,
        event_type=event_type,
        payload=payload
    )

    return process_event(db, event, actor=actor)

def submit_reprompt_data(db: Session, session_id: str, secondary_contact: str, actor: str = "user") -> ApplicationSession:
    """
    Submits requested secondary contact info to exit PENDING_REPROMPT.
    """
    session_obj = db.query(ApplicationSession).with_for_update().filter_by(id=session_id).first()
    if session_obj and session_obj.verifications:
        latest_verification = session_obj.verifications[-1]
        latest_verification.secondary_contact_number = secondary_contact
        db.add(latest_verification)

    event = OrchestratorEvent(
        session_id=session_id,
        event_type=EventType.REPROMPT_SUBMISSION_RECEIVED,
        payload={"secondary_contact": secondary_contact}
    )
    return process_event(db, event, actor=actor)

def submit_artifact(db: Session, session_id: str, artifact_type: ArtifactType, file_hash: str, actor: str = "user") -> ApplicationSession:
    """
    Submits requested artifact to exit PENDING_REPROMPT.
    """
    session_obj = db.query(ApplicationSession).with_for_update().filter_by(id=session_id).first()
    if session_obj and session_obj.verifications:
        latest_verification = session_obj.verifications[-1]
        latest_verification.artifact_type = artifact_type
        latest_verification.artifact_hash = file_hash
        db.add(latest_verification)

    event = OrchestratorEvent(
        session_id=session_id,
        event_type=EventType.REPROMPT_SUBMISSION_RECEIVED,
        payload={"artifact_type": artifact_type.value, "artifact_hash": file_hash}
    )
    return process_event(db, event, actor=actor)
