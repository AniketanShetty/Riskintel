"""
test_e2e_failures.py

End-to-end integration tests for failure scenarios in RiskIntel.
Validates validation errors, exception isolation (critical/non-critical engines), and fail-closed audit commits.
"""
import json
import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import app as fastapi_app
from app.exceptions import AuditLogError
from app.audit import get_db_path

TEST_DB_PATH = "riskintel_e2e_test_failures.db"

@pytest.fixture
def app():
    app = fastapi_app
    yield app

@pytest.fixture
def client(app):
    return TestClient(app)

@pytest.fixture
def valid_person_a_payload():
    return {
        "user_type": "person_a",
        "full_name": "John Doe",
        "age": 35,
        "gender": "M",
        "marital_status": "Married",
        "education": "Graduate",
        "self_employed": "No",
        "years_at_current_employer": 5,
        "annual_income": 800000,
        "dependents": 2,
        "cibil_score": 750,
        "loan_amount": 500000,
        "loan_term": 5,
        "loan_purpose": "home",
        "residential_assets_value": 1500000,
        "commercial_assets_value": 0,
        "luxury_assets_value": 100000,
        "bank_asset_value": 200000
    }

# ── 1. Validation Failures ────────────────────────────────────────────────

def test_failure_missing_required_field(client):
    """Test that missing required fields return 400 with MISSING_REQUIRED_FIELD."""
    payload = {"user_type": "person_a"}  # completely empty list of options
    response = client.post("/api/assess", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
    assert data["error"]["code"] == "MISSING_REQUIRED_FIELD"

def test_failure_range_error(client, valid_person_a_payload):
    """Test that out-of-range inputs return 400 with VALIDATION_ERROR details."""
    payload = valid_person_a_payload.copy()
    payload["age"] = 85  # age must be between 18 and 70
    
    response = client.post("/api/assess", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert any(d["field"] == "age" for d in data["error"]["details"])

# ── 2. Exception Isolation Failures ──────────────────────────────────────

def test_failure_critical_engine_crash(client, valid_person_a_payload):
    """Test that a crash in a critical engine (E1) propagates to HTTP 500."""
    with patch("app.orchestrator.get_eligibility", side_effect=Exception("Model loading failure")):
        response = client.post("/api/assess", json=valid_person_a_payload)
        assert response.status_code == 500
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "ENGINE_FAILURE"

def test_failure_non_critical_engine_crash(client, valid_person_a_payload):
    """Test that a crash in a non-critical engine (E3) degrades gracefully (HTTP 200)."""
    # Mock E1, E2, and E4 so the pipeline can reach E3 without hitting
    # real model dependencies. E4's real implementation may choke on
    # the fallback archetype_res data, so provide a safe return value.
    with patch("app.orchestrator.get_eligibility") as mock_e1, \
         patch("app.orchestrator.get_risk_tier") as mock_e2, \
         patch("app.orchestrator.get_borrower_archetype", side_effect=ValueError("Feature array mismatch")) as mock_e3, \
         patch("app.orchestrator.generate_person_a_recommendations") as mock_e4:
        mock_e1.return_value = {"verdict": "Likely", "probability": 0.75, "bias": 0.5, "feature_contributions": {"f1": 0.25}}
        mock_e2.return_value = {"risk_tier": "P1", "tier_description": "Low Risk"}
        mock_e4.return_value = {"strengths": ["Analysis complete."], "risk_factors": [], "recommendations": [], "action_plan": [], "triggered_rule_ids": []}
        response = client.post("/api/assess", json=valid_person_a_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        # Conforms to fallback
        assert data["archetype"]["label"] == "Unclassified"
        assert data["archetype"]["cluster_id"] == -1

# ── 3. Fail-Closed Audit Failures ────────────────────────────────────────

def test_failure_audit_commit_locked(client, valid_person_a_payload):
    """Test that a database lock exception during audit commit causes fail-closed HTTP 500."""
    # Must also mock E1/E2 so the pipeline reaches the audit step.
    # The real E1 engine crashes with model mismatch before audit is called.
    with patch("app.orchestrator.get_eligibility") as mock_e1, \
         patch("app.orchestrator.get_risk_tier") as mock_e2, \
         patch("app.orchestrator.get_borrower_archetype") as mock_e3, \
         patch("app.orchestrator.generate_person_a_recommendations") as mock_e4, \
         patch("app.orchestrator.write_audit_record", side_effect=AuditLogError("SQLite DB is locked")):
        mock_e1.return_value = {"verdict": "Likely", "probability": 0.75, "bias": 0.5, "feature_contributions": {"f1": 0.25}}
        mock_e2.return_value = {"risk_tier": "P1", "tier_description": "Low Risk"}
        mock_e3.return_value = {"archetype_label": "Highly Tenured Veterans", "cluster_id": 0}
        mock_e4.return_value = {"strengths": [], "risk_factors": [], "recommendations": [], "action_plan": [], "triggered_rule_ids": []}
        response = client.post("/api/assess", json=valid_person_a_payload)
        assert response.status_code == 500
        data = response.json()
        assert data["status"] == "error"
        assert "withheld" in data["error"]["message"].lower()
