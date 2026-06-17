import hashlib
import hmac
import json
import time
import uuid

import pytest
from fastapi.testclient import TestClient
from main import app
from api.dependencies import get_db

TEST_API_KEY = "test-api-key"
TEST_WEBHOOK_SECRET = "test-webhook-secret"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def override_get_db(db_session):
    def _override():
        yield db_session
    return _override


def _signed_webhook_post(client: TestClient, url: str, payload: dict) -> object:
    """
    POST to a webhook route with a valid HMAC-SHA256 + timestamp signature.
    Mirrors the signing contract defined in api/auth.py:
      signed_payload = timestamp_str.encode() + b"." + raw_body
      signature = "sha256=" + hmac.new(secret, signed_payload, sha256).hexdigest()
    """
    raw_body = json.dumps(payload).encode()
    ts = str(int(time.time()))
    signed_payload = ts.encode() + b"." + raw_body
    sig = "sha256=" + hmac.new(
        TEST_WEBHOOK_SECRET.encode(),
        signed_payload,
        hashlib.sha256,
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


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = override_get_db(db_session)
    # Provide the API key for all internal routes
    with TestClient(app, headers={"X-API-Key": TEST_API_KEY}) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_full_api_happy_path(client):
    # 1. Intake
    intake_payload = {
        "loan_amount": 25000,
        "loan_term": 12,
        "loan_purpose": "working_capital",
        "income_bracket": "30k-40k",
        "full_name": "API E2E User",
        "national_id": "9998887776",
        "pincode": "560001"
    }
    response = client.post("/apply", json=intake_payload)
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["current_state"] == "TRIAGE"
    session_id = data["session_id"]

    # 2. Triage
    triage_payload = {"bureau_status": "PRIME"}
    response = client.post(f"/applications/{session_id}/triage", json=triage_payload)
    assert response.status_code == 200
    assert response.json()["current_state"] == "PENDING_VERIFICATION"

    # 3. AA Webhook — must be HMAC-signed
    aa_payload = {"session_id": session_id, "status": "SUCCESS", "verified_income": 45000}
    response = _signed_webhook_post(client, "/webhooks/aa", aa_payload)
    assert response.status_code == 200
    assert response.json()["current_state"] == "VERIFIED"

    # 4. Optimization
    opt_payload = {"annual_rate": 0.18}
    response = client.post(f"/applications/{session_id}/optimize", json=opt_payload)
    assert response.status_code == 200
    assert response.json()["current_state"] == "READY"


def test_api_invalid_transition(client):
    intake_payload = {
        "loan_amount": 25000,
        "loan_term": 12,
        "loan_purpose": "working_capital",
        "income_bracket": "30k-40k",
        "full_name": "API E2E User 2",
        "national_id": "9998887772",
        "pincode": "560001"
    }
    response = client.post("/apply", json=intake_payload)
    session_id = response.json()["session_id"]

    # Try calling AA webhook before triage (from TRIAGE state, not PENDING_VERIFICATION)
    aa_payload = {"session_id": session_id, "status": "SUCCESS", "verified_income": 45000}
    response = _signed_webhook_post(client, "/webhooks/aa", aa_payload)

    # The FSM graph will raise InvalidTransitionError, caught by main.py
    assert response.status_code == 409
    assert "State machine transition conflict" in response.json()["message"]


def test_get_applications(client):
    # Setup: create an application
    intake_payload = {
        "loan_amount": 15000,
        "loan_term": 24,
        "loan_purpose": "education",
        "income_bracket": "10k-20k",
        "full_name": "GET API User",
        "national_id": "1112223334",
        "pincode": "560002"
    }
    client.post("/apply", json=intake_payload)

    # Test GET list
    response = client.get("/applications")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    # Check fields
    item = data["items"][0]
    assert "id" in item
    assert "current_state" in item
    assert "loan_amount" in item
    assert "created_at" in item


def test_get_application_detail(client):
    # Setup: create an application
    intake_payload = {
        "loan_amount": 20000,
        "loan_term": 12,
        "loan_purpose": "medical",
        "income_bracket": "40k-50k",
        "full_name": "GET Detail User",
        "national_id": "2223334445",
        "pincode": "560003"
    }
    apply_res = client.post("/apply", json=intake_payload)
    session_id = apply_res.json()["session_id"]

    # Test GET detail
    response = client.get(f"/applications/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert data["loan_amount"] == 20000
    assert data["loan_purpose"] == "medical"
    assert "created_at" in data
    assert "updated_at" in data

    # Test 404
    bad_id = str(uuid.uuid4())
    resp_404 = client.get(f"/applications/{bad_id}")
    assert resp_404.status_code == 404


def test_get_dlq(client):
    # Force a DLQ entry by causing an invalid transition
    intake_payload = {
        "loan_amount": 25000,
        "loan_term": 12,
        "loan_purpose": "working_capital",
        "income_bracket": "30k-40k",
        "full_name": "DLQ User",
        "national_id": "8887776665",
        "pincode": "560001"
    }
    apply_res = client.post("/apply", json=intake_payload)
    session_id = apply_res.json()["session_id"]

    # Invalid webhook
    aa_payload = {"session_id": session_id, "status": "SUCCESS", "verified_income": 45000}
    _signed_webhook_post(client, "/webhooks/aa", aa_payload)

    # Test GET DLQ
    response = client.get("/dlq")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1
    # Check fields
    item = data["items"][0]
    assert "id" in item
    assert "session_id" in item
    assert "route" in item
    assert "raw_payload" in item
    assert "failure_reason" in item
    assert "occurred_at" in item
