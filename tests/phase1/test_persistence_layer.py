import pytest
import uuid
import time
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, InternalError, ProgrammingError
import subprocess

from db.base import Base
from models.session import ApplicationSession
from models.applicant import ApplicantProfile
from models.verification import VerificationRecord
from models.state_event import StateTransitionEvent
from models.enums import ApplicationState, LoanPurpose, LoanTerm, IncomeBracket, BureauGateStatus

def run_alembic_upgrade():
    subprocess.run(["python", "-m", "alembic", "upgrade", "head"], check=True)

def run_alembic_downgrade():
    subprocess.run(["python", "-m", "alembic", "downgrade", "base"], check=True)

def test_alembic_upgrade_downgrade(engine):
    # Proves migration syntax and dependencies are valid
    try:
        run_alembic_downgrade()
    except Exception:
        pass # Handle if already at base
    
    run_alembic_upgrade()
    run_alembic_downgrade()
    run_alembic_upgrade()

    # Removing the in-process Alembic autogenerate test because of the namespace collision with the local 'alembic' folder.
    # The drift check is validated explicitly in the CI pipeline using `alembic revision --autogenerate`.
    pass

def test_orm_applicant_overlaps_collision(db_session):
    # Proves explicit overlaps prevents Identity Map overwrite
    session_obj = ApplicationSession(
        loan_amount=10000,
        loan_term=12,
        loan_purpose="medical",
        income_bracket="10k-20k"
    )
    
    primary = ApplicantProfile(
        is_co_applicant=False,
        full_name="John Doe",
        national_id="1234567890",
        pincode="123456"
    )
    co_app = ApplicantProfile(
        is_co_applicant=True,
        full_name="Jane Doe",
        national_id="0987654321",
        pincode="654321"
    )
    
    session_obj.primary_applicant = primary
    session_obj.co_applicant = co_app
    
    db_session.add(session_obj)
    db_session.flush()
    
    assert session_obj.primary_applicant.is_co_applicant is False
    assert session_obj.co_applicant.is_co_applicant is True
    assert session_obj.primary_applicant.id != session_obj.co_applicant.id

def test_db_check_constraint_rejection(db_session):
    # Proves constraints physically reject bad bounds and invalid enums
    with pytest.raises(IntegrityError) as exc_info:
        db_session.execute(text(
            "INSERT INTO application_sessions (id, current_state, loan_amount, loan_term, loan_purpose, income_bracket) "
            "VALUES (:id, 'INTAKE', 50, 12, 'medical', '10k-20k')"
        ), {"id": str(uuid.uuid4())})
    assert "chk_loan_amount_bounds" in str(exc_info.value)
    db_session.rollback()

    with pytest.raises(IntegrityError) as exc_info:
        db_session.execute(text(
            "INSERT INTO application_sessions (id, current_state, loan_amount, loan_term, loan_purpose, income_bracket) "
            "VALUES (:id, 'HACKED', 10000, 12, 'medical', '10k-20k')"
        ), {"id": str(uuid.uuid4())})
    assert "chk_application_state_enum" in str(exc_info.value)
    db_session.rollback()

def test_db_unique_constraint_rejection(db_session):
    # Proves duplicate co-applicants are structurally blocked
    sess_id = str(uuid.uuid4())
    db_session.execute(text(
        "INSERT INTO application_sessions (id, current_state, loan_amount, loan_term, loan_purpose, income_bracket) "
        "VALUES (:id, 'INTAKE', 10000, 12, 'medical', '10k-20k')"
    ), {"id": sess_id})
    db_session.commit()

    db_session.execute(text(
        "INSERT INTO applicant_profiles (id, session_id, is_co_applicant, full_name, national_id, pincode) "
        "VALUES (:id, :sess, TRUE, 'Co App 1', '1111111111', '111111')"
    ), {"id": str(uuid.uuid4()), "sess": sess_id})
    db_session.commit()

    with pytest.raises(IntegrityError) as exc_info:
        db_session.execute(text(
            "INSERT INTO applicant_profiles (id, session_id, is_co_applicant, full_name, national_id, pincode) "
            "VALUES (:id, :sess, TRUE, 'Co App 2', '2222222222', '222222')"
        ), {"id": str(uuid.uuid4()), "sess": sess_id})
    assert "uq_session_applicant_type" in str(exc_info.value)
    db_session.rollback()

def test_db_audit_ledger_trigger_immutability(db_session):
    # Proves raw SQL updates and deletes on the ledger raise an exception
    sess_id = str(uuid.uuid4())
    db_session.execute(text(
        "INSERT INTO application_sessions (id, current_state, loan_amount, loan_term, loan_purpose, income_bracket) "
        "VALUES (:id, 'INTAKE', 10000, 12, 'medical', '10k-20k')"
    ), {"id": sess_id})
    
    event_id = str(uuid.uuid4())
    db_session.execute(text(
        "INSERT INTO state_transition_events (id, session_id, from_state, to_state, trigger_event, actor) "
        "VALUES (:id, :sess, 'INTAKE', 'TRIAGE', 'submit', 'USER')"
    ), {"id": event_id, "sess": sess_id})
    db_session.commit()

    with pytest.raises((InternalError, ProgrammingError)) as exc_info:
        db_session.execute(text("UPDATE state_transition_events SET to_state = 'READY' WHERE id = :id"), {"id": event_id})
    assert "Updates and Deletes are strictly forbidden" in str(exc_info.value)
    db_session.rollback()

    with pytest.raises((InternalError, ProgrammingError)) as exc_info:
        db_session.execute(text("DELETE FROM state_transition_events WHERE id = :id"), {"id": event_id})
    assert "Updates and Deletes are strictly forbidden" in str(exc_info.value)
    db_session.rollback()

def test_db_updated_at_trigger_advancement(db_session):
    # Proves updated_at advances automatically on raw SQL updates
    sess_id = str(uuid.uuid4())
    db_session.execute(text(
        "INSERT INTO application_sessions (id, current_state, loan_amount, loan_term, loan_purpose, income_bracket) "
        "VALUES (:id, 'INTAKE', 10000, 12, 'medical', '10k-20k')"
    ), {"id": sess_id})
    db_session.commit()

    initial_row = db_session.execute(text("SELECT updated_at FROM application_sessions WHERE id = :id"), {"id": sess_id}).fetchone()
    initial_updated_at = initial_row[0]

    time.sleep(0.1)
    
    db_session.execute(text("UPDATE application_sessions SET loan_amount = 50000 WHERE id = :id"), {"id": sess_id})
    db_session.commit()

    new_row = db_session.execute(text("SELECT updated_at FROM application_sessions WHERE id = :id"), {"id": sess_id}).fetchone()
    new_updated_at = new_row[0]

    assert new_updated_at > initial_updated_at

def test_orm_uuid_memory_generation():
    # Proves UUIDs generate offline in Python
    session_obj = ApplicationSession()
    assert isinstance(session_obj.id, str)
    assert len(session_obj.id) == 36
    val = uuid.UUID(session_obj.id, version=4)
    assert str(val) == session_obj.id

def test_db_timestamp_server_default(db_session):
    # Proves timestamps are generated by PostgreSQL NOW() context
    sess_id = str(uuid.uuid4())
    db_session.execute(text(
        "INSERT INTO application_sessions (id, current_state, loan_amount, loan_term, loan_purpose, income_bracket) "
        "VALUES (:id, 'INTAKE', 10000, 12, 'medical', '10k-20k')"
    ), {"id": sess_id})
    
    record = VerificationRecord(
        session_id=sess_id,
        verification_source="FIELD_OFFICER",
        verification_status="VERIFIED_CLEAN"
    )
    db_session.add(record)
    db_session.flush()
    db_session.refresh(record)

    assert record.received_at is not None
    assert isinstance(record.received_at, datetime)
