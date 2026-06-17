import pytest
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from db.session import SessionLocal

from models.session import ApplicationSession
from models.applicant import ApplicantProfile
from models.verification import VerificationRecord
from models.enums import ArtifactType
from schemas.events import EventType

from services.decision import submit_coapplicant
from services.verification import submit_reprompt_data, submit_artifact
from workers.ttl_worker import run_ttl_sweep

def test_coapplicant_persistence(db_session: Session):
    # Setup
    session = ApplicationSession(current_state="NEARLY_READY", loan_amount=10000, loan_term=12, loan_purpose="medical", income_bracket="30k-40k")
    db_session.add(session)
    db_session.commit()

    # Action
    coapp_data = {"full_name": "Jane Doe", "national_id": "ABC12345", "pincode": "110001"}
    submit_coapplicant(db_session, session.id, coapp_data)
    
    # Assert
    profile = db_session.query(ApplicantProfile).filter_by(session_id=session.id, is_co_applicant=True).first()
    assert profile is not None
    assert profile.full_name == "Jane Doe"
    assert session.current_state == "PENDING_VERIFICATION"

def test_reprompt_persistence(db_session: Session):
    # Setup
    session = ApplicationSession(current_state="PENDING_REPROMPT", loan_amount=10000, loan_term=12, loan_purpose="medical", income_bracket="30k-40k")
    verif = VerificationRecord(session_id=session.id, verification_source="FIELD_OFFICER", verification_status="MISSING_SECONDARY_CONTACT")
    db_session.add(session)
    db_session.add(verif)
    db_session.commit()

    # Action
    submit_reprompt_data(db_session, session.id, "9876543210")

    # Assert
    verif_updated = db_session.query(VerificationRecord).filter_by(session_id=session.id).first()
    assert verif_updated.secondary_contact_number == "9876543210"
    assert session.current_state == "PENDING_VERIFICATION"

def test_artifact_persistence(db_session: Session):
    # Setup
    session = ApplicationSession(current_state="PENDING_REPROMPT", loan_amount=10000, loan_term=12, loan_purpose="medical", income_bracket="30k-40k")
    verif = VerificationRecord(session_id=session.id, verification_source="FIELD_OFFICER", verification_status="UNREACHABLE")
    db_session.add(session)
    db_session.add(verif)
    db_session.commit()

    # Action
    submit_artifact(db_session, session.id, ArtifactType.RENT_AGREEMENT, "testhash123")

    # Assert
    verif_updated = db_session.query(VerificationRecord).filter_by(session_id=session.id).first()
    assert verif_updated.artifact_type == ArtifactType.RENT_AGREEMENT
    assert verif_updated.artifact_hash == "testhash123"
    assert session.current_state == "PENDING_VERIFICATION"

def test_ttl_worker(db_session: Session):
    # Setup
    past_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
    
    session1 = ApplicationSession(current_state="PENDING_VERIFICATION", updated_at=past_date, loan_amount=10000, loan_term=12, loan_purpose="medical", income_bracket="30k-40k")
    session2 = ApplicationSession(current_state="PENDING_REPROMPT", updated_at=past_date, loan_amount=10000, loan_term=12, loan_purpose="medical", income_bracket="30k-40k")
    session3 = ApplicationSession(current_state="NEARLY_READY", updated_at=past_date, loan_amount=10000, loan_term=12, loan_purpose="medical", income_bracket="30k-40k")
    
    db_session.add_all([session1, session2, session3])
    db_session.commit()

    s1_id = session1.id
    s2_id = session2.id
    s3_id = session3.id

    # Action
    # We patch SessionLocal to use the test db_session
    import workers.ttl_worker
    workers.ttl_worker.SessionLocal = lambda: db_session
    workers.ttl_worker.run_ttl_sweep(db=db_session)

    # Assert
    session1 = db_session.query(ApplicationSession).get(s1_id)
    session2 = db_session.query(ApplicationSession).get(s2_id)
    session3 = db_session.query(ApplicationSession).get(s3_id)
    
    assert session1.current_state == "NOT_READY_YET"
    assert session2.current_state == "NOT_READY_YET"
    assert session3.current_state == "NOT_READY_YET"
