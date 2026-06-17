import pytest
from fastapi.testclient import TestClient
import time
import json
import hmac
import hashlib

from main import app
from api.dependencies import get_db
from models.dead_letter import DeadLetterWebhook
from services.intake import create_application, submit_application

TEST_WEBHOOK_SECRET = "test-webhook-secret"

def _override_get_db(db_session):
    def _override():
        yield db_session
    return _override

def _signed_post(client, url, payload):
    """Compute HMAC-SHA256 + timestamp and POST to a webhook route."""
    raw_body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    ts = str(int(time.time()))
    signed_payload = ts.encode() + b"." + raw_body
    sig = "sha256=" + hmac.new(
        TEST_WEBHOOK_SECRET.encode(), signed_payload, hashlib.sha256
    ).hexdigest()
    return client.post(
        url,
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": sig,
            "X-Timestamp": ts,
        },
    )

@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = _override_get_db(db_session)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_dead_letter_case_1_invalid_state(client, db_session):
    """
    Case 1: Webhook arrives in invalid state.
    Expected: Dead-letter row written.
    """
    # Create application in INTAKE state (not ready for webhook)
    session_obj = create_application(db_session, {
        "loan_amount": 10000, "loan_term": 12, "loan_purpose": "medical",
        "income_bracket": "30k-40k", "full_name": "DL User 1",
        "national_id": "9999999991", "pincode": "123456"
    })
    db_session.commit()
    sid = session_obj.id

    # Post AA webhook (will fail because state is INTAKE, not PENDING_VERIFICATION)
    payload = {"session_id": sid, "status": "SUCCESS", "verified_income": 50000}
    r = _signed_post(client, "/webhooks/aa", payload)
    assert r.status_code == 409  # InvalidTransitionError

    # Check dead letter log
    from db.session import SessionLocal
    check_db = SessionLocal()
    logs = check_db.query(DeadLetterWebhook).filter_by(session_id=sid).all()
    
    assert len(logs) == 1
    assert logs[0].failure_reason == "INVALID_STATE"
    assert logs[0].session_id == sid
    assert logs[0].route == "/webhooks/aa"
    assert "SUCCESS" in logs[0].raw_payload

    # Cleanup manually since the dead letter was saved in a separate session that isn't rolled back by the test fixture
    check_db.query(DeadLetterWebhook).filter_by(session_id=sid).delete()
    check_db.commit()
    check_db.close()


def test_dead_letter_case_2_invalid_payload(client, db_session):
    """
    Case 2: Webhook contains invalid payload.
    Expected: Dead-letter row written.
    """
    # Missing required field "status"
    test_sid = "dl-case-2-uuid"
    payload = {"session_id": test_sid, "verified_income": 50000}
    r = _signed_post(client, "/webhooks/aa", payload)
    assert r.status_code == 422  # RequestValidationError

    # Check dead letter log
    from db.session import SessionLocal
    check_db = SessionLocal()
    logs = check_db.query(DeadLetterWebhook).filter_by(session_id=test_sid).all()
    
    assert len(logs) == 1
    assert logs[0].failure_reason == "INVALID_PAYLOAD"
    assert logs[0].session_id == test_sid
    assert logs[0].route == "/webhooks/aa"

    check_db.query(DeadLetterWebhook).filter_by(session_id=test_sid).delete()
    check_db.commit()
    check_db.close()


def test_dead_letter_case_3_webhook_succeeds(client, db_session):
    """
    Case 3: Webhook succeeds.
    Expected: No dead-letter row.
    """
    from services.triage import run_triage_evaluation
    from models.enums import BureauGateStatus

    # Create application and move to PENDING_VERIFICATION
    session_obj = create_application(db_session, {
        "loan_amount": 10000, "loan_term": 12, "loan_purpose": "medical",
        "income_bracket": "30k-40k", "full_name": "DL User 3",
        "national_id": "9999999993", "pincode": "123456"
    })
    submit_application(db_session, session_obj.id)
    run_triage_evaluation(db_session, session_obj.id, BureauGateStatus.PRIME)
    db_session.commit()
    sid = session_obj.id

    # Post valid AA webhook
    payload = {"session_id": sid, "status": "SUCCESS", "verified_income": 50000}
    r = _signed_post(client, "/webhooks/aa", payload)
    assert r.status_code == 200

    # Check dead letter log
    from db.session import SessionLocal
    check_db = SessionLocal()
    logs = check_db.query(DeadLetterWebhook).filter_by(session_id=sid).all()
    
    assert len(logs) == 0

    check_db.close()
