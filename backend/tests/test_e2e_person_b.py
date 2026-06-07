"""
test_e2e_person_b.py

End-to-end integration tests for Person B pipeline in RiskIntel.
Validates execution flow, Livelihood mapping, and E5 floor breach overrides.
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
        "user_type": "person_b",
        "full_name": "Ramesh Kumar",
        "age": 42,
        "gender": "M",
        "primary_business": "Tailoring",
        "secondary_business": "none",
        "annual_income": 120000,
        "monthly_expenses": 3000,
        "loan_amount": 10000,
        "loan_purpose": "Apparels",
        "loan_tenure": 12,
        "loan_installments": 12,
        "young_dependents": 2,
        "old_dependents": 0,
        "occupants_count": 4,
        "home_ownership": 1,
        "type_of_house": "semi_pucca",
        "house_area": 450,
        "sanitary_availability": 1,
        "water_availability": 1.0,
        "social_class": "OBC"
    }

def test_person_b_standard_flow(client, baseline_payload):
    """
    Test standard Person B workflow end-to-end.
    Ensures E5, Livelihood Mapper, and E4 run sequentially and output format is correct.
    """
    response = client.post("/api/assess/person-b", json=baseline_payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
    assert data["user_type"] == "person_b"
    assert "correlation_id" in data
    
    # Verify E5 structure
    assert "readiness" in data
    assert "score" in data["readiness"]
    assert "band" in data["readiness"]
    assert "components" in data["readiness"]
    assert "financial_health" in data["readiness"]["components"]
    
    # Verify E6 Livelihood Archetype structure
    assert "archetype" in data
    assert data["archetype"]["label"] == "Services"  # "Tailoring" maps to Services
    assert data["archetype"]["cluster_id"] == 2
    assert "description" in data["archetype"]
    
    # Verify E4 structure
    assert "recommendations" in data
    assert "strengths" in data["recommendations"]
    assert "improvement_areas" in data["recommendations"]
    assert "recommendations" in data["recommendations"]
    assert "next_steps" in data["recommendations"]

    # Verify SQLite Audit Ledger
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_log WHERE correlation_id = ?", (data["correlation_id"],))
    row = cursor.fetchone()
    conn.close()
    
    assert row is not None
    # Stored verdict is the readiness band
    assert row[7] == data["readiness"]["band"]

def test_e5_floor_breach_override(client, baseline_payload):
    """
    Test E5 floor breach override conflict logic.
    If E5 score is overridden by the floor override, verify final_verdict changes to 'Not Ready' and score is 0.
    """
    payload = baseline_payload.copy()
    payload["annual_income"] = 50000.0
    payload["monthly_expenses"] = 10000.0
    payload["loan_amount"] = 300000.0

    
    response = client.post("/api/assess/person-b", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Verify band and score are forced to Not Ready / 0
    assert data["readiness"]["band"] == "Not Ready"
    assert data["readiness"]["score"] == 0
    
    # Verify SQLite Audit Ledger flags
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT policy_override_flags FROM audit_log WHERE correlation_id = ?", (data["correlation_id"],))
    row = cursor.fetchone()
    conn.close()
    
    flags = json.loads(row[0])
    assert "OVERRIDE_E5_FLOOR_BREACH" in flags
    assert "ENGINE_POLICY_OVERRIDE" in flags
