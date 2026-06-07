"""
test_e2e_person_a.py

End-to-end integration tests for Person A pipeline in RiskIntel.
Validates the complete execution flow, CIBIL boundaries, and E2 risk tier override.
"""
import json
import sqlite3
import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import app as fastapi_app
from app.audit import get_db_path

@pytest.fixture
def app():
    app = fastapi_app
    yield app

@pytest.fixture
def client(app):
    return TestClient(app)

@pytest.fixture
def baseline_payload():
    return {
        "user_type": "person_a",
        "full_name": "Aniket Sharma",
        "age": 34,
        "gender": "M",
        "marital_status": "Married",
        "education": "Graduate",
        "self_employed": "No",
        "years_at_current_employer": 6,
        "annual_income": 9600000,
        "dependents": 2,
        "cibil_score": 750,
        "loan_amount": 15000000,
        "loan_term": 12,
        "loan_purpose": "home",
        "residential_assets_value": 5600000,
        "commercial_assets_value": 3700000,
        "luxury_assets_value": 8800000,
        "bank_asset_value": 3300000
    }

def test_person_a_standard_flow(client, baseline_payload):
    """
    Test standard Person A workflow end-to-end.
    Ensures that E1, E2, E3, and E4 run sequentially and response matches contract.
    """
    response = client.post("/api/assess/person-a", json=baseline_payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
    assert data["user_type"] == "person_a"
    assert "correlation_id" in data
    
    # Verify E1 structure
    assert "eligibility" in data
    assert "verdict" in data["eligibility"]
    assert "probability" in data["eligibility"]
    assert "feature_contributions" in data["eligibility"]
    
    # Verify E2 structure
    assert "risk_tier" in data
    assert data["risk_tier"]["tier"] in ("P1", "P2", "P3", "P4")
    assert data["risk_tier"]["score_used"] == 750
    assert "thresholds" in data["risk_tier"]
    
    # Verify E3 structure
    assert "archetype" in data
    assert "label" in data["archetype"]
    assert "cluster_id" in data["archetype"]
    
    # Verify E4 structure
    assert "recommendations" in data
    assert "strengths" in data["recommendations"]
    assert "risk_factors" in data["recommendations"]
    assert "recommendations" in data["recommendations"]
    assert "action_plan" in data["recommendations"]
    
    # Verify SQLite Audit Ledger
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_log WHERE correlation_id = ?", (data["correlation_id"],))
    row = cursor.fetchone()
    conn.close()
    
    assert row is not None
    # Check stored parameters
    final_verdict = row[7]
    assert final_verdict == data["eligibility"]["verdict"]

def test_person_a_cibil_edge_cases(client, baseline_payload):
    """
    Test CIBIL score boundary values and correct risk tier mappings.
    CIBIL boundaries: P1 >= 701, P2 669-700, P3 659-668, P4 <= 658
    """
    # 1. Score 701 (P1 edge)
    payload = baseline_payload.copy()
    payload["cibil_score"] = 701
    res = client.post("/api/assess/person-a", json=payload)
    assert res.status_code == 200
    assert res.json()["risk_tier"]["tier"] == "P1"

    # 2. Score 700 (P2 upper edge)
    payload["cibil_score"] = 700
    res = client.post("/api/assess/person-a", json=payload)
    assert res.status_code == 200
    assert res.json()["risk_tier"]["tier"] == "P2"

    # 3. Score 669 (P2 lower edge)
    payload["cibil_score"] = 669
    res = client.post("/api/assess/person-a", json=payload)
    assert res.status_code == 200
    assert res.json()["risk_tier"]["tier"] == "P2"

    # 4. Score 668 (P3 upper edge)
    payload["cibil_score"] = 668
    res = client.post("/api/assess/person-a", json=payload)
    assert res.status_code == 200
    assert res.json()["risk_tier"]["tier"] == "P3"

    # 5. Score 659 (P3 lower edge)
    payload["cibil_score"] = 659
    res = client.post("/api/assess/person-a", json=payload)
    assert res.status_code == 200
    assert res.json()["risk_tier"]["tier"] == "P3"

    # 6. Score 658 (P4 edge)
    # Note: this will trigger P4 override since cibil is <= 658
    payload["cibil_score"] = 658
    res = client.post("/api/assess/person-a", json=payload)
    assert res.status_code == 200
    assert res.json()["risk_tier"]["tier"] == "P4"

def test_e2_risk_override_conflict(client, baseline_payload):
    """
    Test E2 P4 risk override logic.
    Forces E1 approval to 'Unlikely' and asserts that OVERRIDE_E2_P4_REJECTION is logged.
    """
    payload = baseline_payload.copy()
    payload["cibil_score"] = 600  # Forces Risk Tier P4
    
    # Mock E1 to return a favorable 'Highly Likely' approval
    with patch("app.orchestrator.get_eligibility") as mock_e1:
        mock_e1.return_value = {
            "verdict": "Highly Likely",
            "probability": 0.92,
            "bias": 0.72,
            "feature_contributions": {"cibil_score": 0.20}
        }
        
        response = client.post("/api/assess/person-a", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        # Override must change verdict to 'Unlikely'
        assert data["eligibility"]["verdict"] == "Unlikely"
        
        # Verify SQLite Audit Ledger contains override flag
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT policy_override_flags FROM audit_log WHERE correlation_id = ?", (data["correlation_id"],))
        row = cursor.fetchone()
        conn.close()
        
        flags = json.loads(row[0])
        assert "OVERRIDE_E2_P4_REJECTION" in flags
