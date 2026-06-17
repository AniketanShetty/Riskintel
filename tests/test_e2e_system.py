"""
tests/test_e2e_system.py
------------------------
Smallest set of end-to-end tests that prove RiskIntel works as a complete system.

Coverage rationale:
  Each test exercises a complete FSM path through the HTTP API layer,
  including auth, routing, domain logic, persistence, and FSM transitions.
  Unit tests for individual services already exist; these tests prove
  the paths compose correctly end-to-end.

Paths covered:
  E2E-01  Happy path: INTAKE â†’ TRIAGE â†’ AA â†’ OPTIMIZATION â†’ READY
  E2E-02  Bureau hard reject: INTAKE â†’ TRIAGE â†’ NOT_READY_YET
  E2E-03  Triage math fail: INTAKE â†’ TRIAGE â†’ NOT_READY_YET
  E2E-04  FO path: INTAKE â†’ TRIAGE â†’ FO webhook â†’ VERIFIED â†’ OPTIMIZATION â†’ READY
  E2E-05  Reprompt loop: INTAKE â†’ ... â†’ PENDING_REPROMPT â†’ PENDING_VERIFICATION â†’ VERIFIED
  E2E-06  Counter-offer acceptance: NEARLY_READY â†’ READY
  E2E-07  Counter-offer rejection: NEARLY_READY â†’ NOT_READY_YET

Auth paths covered:
  A-01  Missing API key â†’ 401
  A-02  Wrong API key â†’ 403
  A-03  Missing HMAC signature â†’ 401
  A-04  Wrong HMAC signature â†’ 403
  A-05  Replayed HMAC timestamp â†’ 400

Idempotency paths covered:
  I-01  Same key, same body â†’ 200 with X-Idempotency-Replayed header, no second DB write
  I-02  Same key, different body â†’ 422
"""
import hashlib
import hmac
import json
import time

import pytest
from fastapi.testclient import TestClient
from main import app
from api.dependencies import get_db

TEST_API_KEY = "test-api-key"
TEST_WEBHOOK_SECRET = "test-webhook-secret"

# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

def _override_get_db(db_session):
    def _override():
        yield db_session
    return _override


def _signed_post(client, url, payload):
    """Compute HMAC-SHA256 + timestamp and POST to a webhook route."""
    raw_body = json.dumps(payload).encode()
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
    with TestClient(app, headers={"X-API-Key": TEST_API_KEY}) as c:
        yield c
    app.dependency_overrides.clear()


def _new_applicant(suffix: str) -> dict:
    return {
        "loan_amount": 25000,
        "loan_term": 12,
        "loan_purpose": "working_capital",
        "income_bracket": "30k-40k",
        "full_name": f"E2E User {suffix}",
        "national_id": suffix.ljust(10, "0")[:10],
        "pincode": "560001",
    }


def _intake_to_pending_verification(client, suffix="01"):
    r = client.post("/apply", json=_new_applicant(suffix))
    assert r.status_code == 200, r.text
    sid = r.json()["session_id"]
    r = client.post(f"/applications/{sid}/triage", json={"bureau_status": "PRIME"})
    assert r.status_code == 200 and r.json()["current_state"] == "PENDING_VERIFICATION"
    return sid


# ---------------------------------------------------------------------------
# E2E-01: Full happy path via AA â€” READY
# ---------------------------------------------------------------------------

def test_e2e_01_full_aa_happy_path_ready(client):
    sid = _intake_to_pending_verification(client, "01")

    r = _signed_post(client, "/webhooks/aa", {
        "session_id": sid, "status": "SUCCESS", "verified_income": 50000
    })
    assert r.status_code == 200 and r.json()["current_state"] == "VERIFIED"

    r = client.post(f"/applications/{sid}/optimize", json={"annual_rate": 0.18})
    assert r.status_code == 200
    assert r.json()["current_state"] == "READY"


# ---------------------------------------------------------------------------
# E2E-02: Bureau hard reject â†’ NOT_READY_YET (no verification ever happens)
# ---------------------------------------------------------------------------

def test_e2e_02_bureau_hard_reject(client):
    r = client.post("/apply", json={
        **_new_applicant("02"),
        "loan_amount": 25000,
    })
    assert r.status_code == 200
    sid = r.json()["session_id"]

    r = client.post(f"/applications/{sid}/triage", json={"bureau_status": "THIN_FILE"})
    assert r.status_code == 200
    assert r.json()["current_state"] == "NOT_READY_YET"


# ---------------------------------------------------------------------------
# E2E-03: Triage math fail â†’ NOT_READY_YET immediately
# ---------------------------------------------------------------------------

def test_e2e_03_triage_math_fail(client):
    payload = {
        **_new_applicant("03"),
        "loan_amount": 500000,
        "loan_term": 12,
        "income_bracket": "0-10k",   # income base ~3k, target EMI ~41k â†’ fail
    }
    r = client.post("/apply", json=payload)
    assert r.status_code == 200
    sid = r.json()["session_id"]

    r = client.post(f"/applications/{sid}/triage", json={"bureau_status": "PRIME"})
    assert r.status_code == 200
    assert r.json()["current_state"] == "NOT_READY_YET"


# ---------------------------------------------------------------------------
# E2E-04: Full happy path via FO webhook â†’ READY
# ---------------------------------------------------------------------------
# E2E-04: Full happy path via FO webhook → READY
# ---------------------------------------------------------------------------

def test_e2e_04_fo_webhook_verified_to_ready(client):
    sid = _intake_to_pending_verification(client, "04")

    # FO reports verified clean
    r = _signed_post(client, "/webhooks/fo", {
        "session_id": sid, "status": "VERIFIED_CLEAN", "verified_income": 45000
    })
    assert r.status_code == 200 and r.json()["current_state"] == "VERIFIED"

    r = client.post(f"/applications/{sid}/optimize", json={"annual_rate": 0.18})
    assert r.status_code == 200
    assert r.json()["current_state"] == "READY"


# ---------------------------------------------------------------------------
# E2E-05: Reprompt loop → VERIFIED (FO missing secondary contact)
# ---------------------------------------------------------------------------

def test_e2e_05_reprompt_loop_resolves(client):
    sid = _intake_to_pending_verification(client, "05")

    # FO can't reach borrower — asks for secondary contact
    r = _signed_post(client, "/webhooks/fo", {
        "session_id": sid, "status": "MISSING_SECONDARY_CONTACT"
    })
    assert r.status_code == 200 and r.json()["current_state"] == "PENDING_REPROMPT"

    # User submits secondary contact
    r = client.post(f"/applications/{sid}/reprompt",
                    json={"secondary_contact": "+91-9999999999"})
    assert r.status_code == 200 and r.json()["current_state"] == "PENDING_VERIFICATION"

    # FO now succeeds
    r = _signed_post(client, "/webhooks/fo", {
        "session_id": sid, "status": "VERIFIED_CLEAN", "verified_income": 38000
    })
    assert r.status_code == 200 and r.json()["current_state"] == "VERIFIED"

# ---------------------------------------------------------------------------
# E2E-06: Counter-offer acceptance: NEARLY_READY â†’ READY
# ---------------------------------------------------------------------------

def test_e2e_06_counter_offer_accepted(client):
    """NEARLY_READY + POST /decision/{id}/accept â†’ READY."""
    payload = {
        **_new_applicant("06"),
        "loan_amount": 100000,
        "income_bracket": "10k-20k", # Income is low -> NEARLY_READY
    }
    r = client.post("/apply", json=payload)
    assert r.status_code == 200
    sid = r.json()["session_id"]

    client.post(f"/applications/{sid}/triage", json={"bureau_status": "PRIME"})
    _signed_post(client, "/webhooks/aa", {"session_id": sid, "status": "SUCCESS", "verified_income": 6000})
    r = client.post(f"/applications/{sid}/optimize", json={"annual_rate": 0.18})
    assert r.json()["current_state"] == "NEARLY_READY"

    r = client.post(f"/decision/{sid}/accept")
    assert r.status_code == 200
    assert r.json()["current_state"] == "READY"


# ---------------------------------------------------------------------------
# E2E-07: Counter-offer rejection: NEARLY_READY â†’ NOT_READY_YET
# ---------------------------------------------------------------------------

def test_e2e_07_counter_offer_rejected(client):
    """NEARLY_READY + POST /decision/{id}/reject â†’ NOT_READY_YET."""
    payload = {
        **_new_applicant("07"),
        "loan_amount": 100000,
        "income_bracket": "10k-20k",
    }
    r = client.post("/apply", json=payload)
    sid = r.json()["session_id"]

    client.post(f"/applications/{sid}/triage", json={"bureau_status": "PRIME"})
    _signed_post(client, "/webhooks/aa", {"session_id": sid, "status": "SUCCESS", "verified_income": 6000})
    r = client.post(f"/applications/{sid}/optimize", json={"annual_rate": 0.18})
    assert r.json()["current_state"] == "NEARLY_READY"

    r = client.post(f"/decision/{sid}/reject")
    assert r.status_code == 200
    assert r.json()["current_state"] == "NOT_READY_YET"


# ---------------------------------------------------------------------------
# E2E-08: Submit Co-Applicant: NEARLY_READY â†’ PENDING_VERIFICATION
# ---------------------------------------------------------------------------

def test_e2e_08_submit_coapplicant(client):
    """NEARLY_READY + POST /decision/{id}/coapplicant â†’ PENDING_VERIFICATION."""
    payload = {
        **_new_applicant("08"),
        "loan_amount": 100000,
        "income_bracket": "10k-20k",
    }
    r = client.post("/apply", json=payload)
    sid = r.json()["session_id"]

    client.post(f"/applications/{sid}/triage", json={"bureau_status": "PRIME"})
    _signed_post(client, "/webhooks/aa", {"session_id": sid, "status": "SUCCESS", "verified_income": 6000})
    r = client.post(f"/applications/{sid}/optimize", json={"annual_rate": 0.18})
    assert r.json()["current_state"] == "NEARLY_READY"

    r = client.post(f"/decision/{sid}/coapplicant", json={
        "full_name": "Co Applicant",
        "national_id": "ABC98765",
        "pincode": "110001"
    })
    assert r.status_code == 200
    assert r.json()["current_state"] == "PENDING_VERIFICATION"

# ---------------------------------------------------------------------------
# A-01: Missing API key -> 401

def test_auth_a01_missing_api_key(db_session):
    app.dependency_overrides[get_db] = _override_get_db(db_session)
    # No X-API-Key header
    with TestClient(app) as c:
        r = c.post("/apply", json=_new_applicant("a01"))
    app.dependency_overrides.clear()
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# A-02: Wrong API key â†’ 403
# ---------------------------------------------------------------------------

def test_auth_a02_wrong_api_key(db_session):
    app.dependency_overrides[get_db] = _override_get_db(db_session)
    with TestClient(app, headers={"X-API-Key": "totally-wrong"}) as c:
        r = c.post("/apply", json=_new_applicant("a02"))
    app.dependency_overrides.clear()
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# A-03: Missing HMAC signature on webhook â†’ 401
# ---------------------------------------------------------------------------

def test_auth_a03_missing_hmac_signature(client):
    # Post to webhook without HMAC headers
    r = client.post("/webhooks/aa", json={
        "session_id": "any", "status": "SUCCESS", "verified_income": 1000
    })
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# A-04: Wrong HMAC signature â†’ 403
# ---------------------------------------------------------------------------

def test_auth_a04_wrong_hmac_signature(client):
    raw_body = json.dumps({"session_id": "any", "status": "SUCCESS", "verified_income": 1000}).encode()
    ts = str(int(time.time()))
    r = client.post(
        "/webhooks/aa",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": "sha256=deadbeefdeadbeef",
            "X-Timestamp": ts,
        },
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# A-05: Replayed HMAC timestamp (outside tolerance window) â†’ 400
# ---------------------------------------------------------------------------

def test_auth_a05_replayed_timestamp(client):
    payload = {"session_id": "any", "status": "SUCCESS", "verified_income": 1000}
    raw_body = json.dumps(payload).encode()
    # Timestamp is 10 minutes old â€” outside the 5-minute tolerance
    stale_ts = str(int(time.time()) - 700)
    signed_payload = stale_ts.encode() + b"." + raw_body
    sig = "sha256=" + hmac.new(
        TEST_WEBHOOK_SECRET.encode(), signed_payload, hashlib.sha256
    ).hexdigest()
    r = client.post(
        "/webhooks/aa",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": sig,
            "X-Timestamp": stale_ts,
        },
    )
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# I-01: Idempotency replay â€” same key, same body â†’ cached response returned
# ---------------------------------------------------------------------------

def test_idempotency_i01_replay_returns_cached_response(client):
    payload = _new_applicant("i01")
    key = "idem-test-key-i01"

    r1 = client.post("/apply", json=payload, headers={"X-Idempotency-Key": key})
    assert r1.status_code == 200
    sid1 = r1.json()["session_id"]

    # Second identical request with same key
    r2 = client.post("/apply", json=payload, headers={"X-Idempotency-Key": key})
    assert r2.status_code == 200
    assert r2.json()["session_id"] == sid1          # same session returned
    assert r2.headers.get("X-Idempotency-Replayed") == "true"


# ---------------------------------------------------------------------------
# I-02: Idempotency key reuse with different body â†’ 422
# ---------------------------------------------------------------------------

def test_idempotency_i02_key_reuse_different_body_rejected(client):
    payload_a = _new_applicant("i02a")
    payload_b = {**_new_applicant("i02b"), "loan_amount": 50000}  # different amount
    key = "idem-test-key-i02"

    r1 = client.post("/apply", json=payload_a, headers={"X-Idempotency-Key": key})
    assert r1.status_code == 200

    r2 = client.post("/apply", json=payload_b, headers={"X-Idempotency-Key": key})
    assert r2.status_code == 422
def test_e2e_09_aa_empty(client, db_session):
    sid = _intake_to_pending_verification(client, "09")
    r = _signed_post(client, "/webhooks/aa", {"session_id": sid, "status": "EMPTY"})
    assert r.status_code == 200
    assert r.json()["current_state"] == "PENDING_VERIFICATION"
    
def test_e2e_10_aa_failed_retry(client):
    sid = _intake_to_pending_verification(client, "10")
    r = _signed_post(client, "/webhooks/aa", {"session_id": sid, "status": "FAILED"})
    assert r.status_code == 200
    assert r.json()["current_state"] == "PENDING_VERIFICATION"

def test_e2e_11_aa_timeout_retry(client):
    sid = _intake_to_pending_verification(client, "11")
    r = _signed_post(client, "/webhooks/aa", {"session_id": sid, "status": "TIMEOUT"})
    assert r.status_code == 200
    assert r.json()["current_state"] == "PENDING_VERIFICATION"

def test_e2e_12_aa_exhausted_fallback(client):
    sid = _intake_to_pending_verification(client, "12")
    _signed_post(client, "/webhooks/aa", {"session_id": sid, "status": "FAILED"})
    _signed_post(client, "/webhooks/aa", {"session_id": sid, "status": "TIMEOUT"})
    r = _signed_post(client, "/webhooks/aa", {"session_id": sid, "status": "FAILED"})
    assert r.status_code == 200
    assert r.json()["current_state"] == "PENDING_VERIFICATION"
