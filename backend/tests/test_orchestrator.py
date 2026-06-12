"""
test_orchestrator.py

Comprehensive test suite for the RiskIntel Central Orchestration Layer.
Tests request validation, routing, overrides, exception isolation,
fail-closed audit logging, and tiered health checks.
"""
import json
import sqlite3
import pytest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from app.main import app as fastapi_app
from app.exceptions import CriticalEngineError, NonCriticalEngineError, AuditLogError
from app.audit import get_db_path

@pytest.fixture
def app():
    """Create a FastAPI app configured for testing."""
    app = fastapi_app
    yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
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

@pytest.fixture
def valid_person_b_payload():
    return {
        "user_type": "person_b",
        "full_name": "Jane Smith",
        "age": 40,
        "gender": "F",
        "primary_business": "Kirana shop",
        "secondary_business": "none",
        "annual_income": 150000,
        "monthly_expenses": 5000,
        "loan_amount": 25000,
        "loan_purpose": "working capital",
        "loan_tenure": 12,
        "loan_installments": 12,
        "young_dependents": 2,
        "old_dependents": 0,
        "occupants_count": 4,
        "home_ownership": 1,
        "type_of_house": "pucca",
        "house_area": 300,
        "sanitary_availability": 1,
        "water_availability": 1.0,
        "social_class": "OBC"
    }

# ── 1. Routing & Conversion Tests ─────────────────────────────────────────

def test_routing_person_a_standard(client, valid_person_a_payload):
    """Verify that a valid Person A payload routes correctly to Person A Flow."""
    with patch("app.orchestrator.get_eligibility") as mock_e1, \
         patch("app.orchestrator.get_risk_tier") as mock_e2, \
         patch("app.orchestrator.get_borrower_archetype") as mock_e3, \
         patch("app.orchestrator.generate_person_a_recommendations") as mock_e4:
         
        mock_e1.return_value = {"verdict": "Likely", "probability": 0.75, "bias": 0.5, "feature_contributions": {"f1": 0.25}}
        mock_e2.return_value = {"risk_tier": "P1", "tier_description": "Low Risk", "thresholds": {"p1_min": 701, "p2_min": 669, "p2_max": 700, "p3_min": 659, "p3_max": 668, "p4_max": 658}}
        mock_e3.return_value = {"cluster_id": 0, "archetype_label": "Highly Tenured Veterans"}
        mock_e4.return_value = {"decision_verdict": "Likely", "primary_reason": "Mock reason", "contributing_factors": [{"feature": "mock", "value": "mock", "evidence": "mock", "reason": "mock", "improvement_advice": "mock"}], "triggered_rule_ids": ["R1"]}
        
        response = client.post("/api/assess/person-a", json=valid_person_a_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["user_type"] == "person_a"
        assert data["eligibility"]["verdict"] == "Likely"
        assert data["risk_tier"]["tier"] == "P1"

def test_routing_ntc_reroute(client, valid_person_a_payload):
    """Verify that Person A payload with CIBIL score -1 routes to Person B Flow."""
    payload = valid_person_a_payload.copy()
    payload["cibil_score"] = -1
    
    with patch("app.orchestrator.get_readiness_score") as mock_e5, \
         patch("app.orchestrator.map_livelihood") as mock_e6, \
         patch("app.orchestrator.generate_person_b_recommendations") as mock_e4:
         
        mock_e5.return_value = {
            "score": 60, "band": "Moderately Ready", 
            "components": {
                "financial_health": {"score": 60, "weight": 0.35, "factors": {}},
                "housing_stability": {"score": 60, "weight": 0.20, "factors": {}},
                "infrastructure_access": {"score": 60, "weight": 0.15, "factors": {}},
                "household_burden": {"score": 60, "weight": 0.15, "factors": {}},
                "business_viability": {"score": 60, "weight": 0.15, "factors": {}}
            }, 
            "mapped_features": {}, "imputed_fields": [], "policy_override_applied": False,
            "thresholds": {"financial_health_floor": 0.5, "strong_status_min": 70, "satisfactory_status_min": 50, "band_ready_min": 75, "band_moderately_ready_min": 50, "band_needs_improvement_min": 25}
        }
        mock_e6.return_value = {"label": "Services", "description": "Desc", "cluster_id": 2}
        mock_e4.return_value = {"decision_verdict": "Likely", "primary_reason": "Mock reason", "contributing_factors": [{"feature": "mock", "value": "mock", "evidence": "mock", "reason": "mock", "improvement_advice": "mock"}], "triggered_rule_ids": ["R1"]}
        
        response = client.post("/api/assess", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        # Since it was rerouted to NTC Person B pipeline:
        assert data["user_type"] == "person_b"
        assert "readiness" in data
        assert data["readiness"]["band"] == "Moderately Ready"
        
        # Verify the database entry has the correct reroute override flag
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT policy_override_flags FROM audit_log WHERE correlation_id = ?", (data["correlation_id"],))
        row = cursor.fetchone()
        conn.close()
        
        assert row is not None
        flags = json.loads(row[0])
        assert "REROUTE_NTC_TO_PERSON_B" in flags

# ── 2. Request Validation Tests ───────────────────────────────────────────

def test_validation_missing_field(client):
    """Test that a missing required field returns MISSING_REQUIRED_FIELD."""
    payload = {"user_type": "person_a"}  # missing everything else
    response = client.post("/api/assess", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
    assert data["error"]["code"] == "MISSING_REQUIRED_FIELD"

def test_validation_invalid_user_type(client):
    """Test that an invalid user type returns error."""
    payload = {"user_type": "person_c"}
    response = client.post("/api/assess", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"

def test_validation_out_of_range(client, valid_person_a_payload):
    """Test that range violations return VALIDATION_ERROR with details."""
    payload = valid_person_a_payload.copy()
    payload["age"] = 80  # Max is 70
    payload["cibil_score"] = 250  # Must be 0, -1, or 300-900
    
    response = client.post("/api/assess", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "error"
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert len(data["error"]["details"]) >= 2

# ── 3. Exception Isolation Tests ─────────────────────────────────────────

def test_exception_isolation_critical_e1(client, valid_person_a_payload):
    """Test that critical E1 failure results in HTTP 500."""
    with patch("app.orchestrator.get_eligibility", side_effect=Exception("Database connection timeout")):
        response = client.post("/api/assess", json=valid_person_a_payload)
        assert response.status_code == 500
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "ENGINE_FAILURE"

def test_exception_isolation_non_critical_e3(client, valid_person_a_payload):
    """Test that non-critical E3 failure degrades gracefully (returns HTTP 200)."""
    with patch("app.orchestrator.get_eligibility") as mock_e1, \
         patch("app.orchestrator.get_risk_tier") as mock_e2, \
         patch("app.orchestrator.get_borrower_archetype", side_effect=Exception("KMeans model failure")) as mock_e3, \
         patch("app.orchestrator.generate_person_a_recommendations") as mock_e4:
         
        mock_e1.return_value = {"verdict": "Likely", "probability": 0.75, "bias": 0.5, "feature_contributions": {"f1": 0.25}}
        mock_e2.return_value = {"risk_tier": "P1", "tier_description": "Low Risk", "thresholds": {"p1_min": 701, "p2_min": 669, "p2_max": 700, "p3_min": 659, "p3_max": 668, "p4_max": 658}}
        mock_e4.return_value = {"decision_verdict": "Likely", "primary_reason": "Mock reason", "contributing_factors": [{"feature": "mock", "value": "mock", "evidence": "mock", "reason": "mock", "improvement_advice": "mock"}], "triggered_rule_ids": ["R1"]}
        
        response = client.post("/api/assess", json=valid_person_a_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        # Archetype has fallback
        assert data["archetype"]["label"] == "Unclassified"
        assert data["archetype"]["cluster_id"] == -1

# ── 4. Conflict Resolution Tests ──────────────────────────────────────────

def test_conflict_resolution_e2_p4_override(client, valid_person_a_payload):
    """Test that E2 Risk Tier P4 overrides E1 Highly Likely and forces verdict to Unlikely."""
    with patch("app.orchestrator.get_eligibility") as mock_e1, \
         patch("app.orchestrator.get_risk_tier") as mock_e2, \
         patch("app.orchestrator.get_borrower_archetype") as mock_e3, \
         patch("app.orchestrator.generate_person_a_recommendations") as mock_e4:
         
        mock_e1.return_value = {"verdict": "Highly Likely", "probability": 0.9, "bias": 0.5, "feature_contributions": {"f1": 0.4}}
        mock_e2.return_value = {"risk_tier": "P4", "tier_description": "High Risk", "thresholds": {"p1_min": 701, "p2_min": 669, "p2_max": 700, "p3_min": 659, "p3_max": 668, "p4_max": 658}}
        mock_e3.return_value = {"cluster_id": 0, "archetype_label": "Highly Tenured Veterans"}
        
        # Capture context passed to E4
        def mock_e4_side_effect(inputs, eligibility_res, risk_tier_res, archetype_res):
            assert eligibility_res["verdict"] == "Unlikely"
            return {
                "decision_verdict": "Unlikely",
                "primary_reason": "Mock primary reason",
                "contributing_factors": [],
                "triggered_rule_ids": []
            }
            
        mock_e4.side_effect = mock_e4_side_effect
        
        response = client.post("/api/assess", json=valid_person_a_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["eligibility"]["verdict"] == "Unlikely"
        
        # Verify the database entry has the correct override flag
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT policy_override_flags FROM audit_log WHERE correlation_id = ?", (data["correlation_id"],))
        row = cursor.fetchone()
        conn.close()
        
        flags = json.loads(row[0])
        assert "OVERRIDE_E2_P4_REJECTION" in flags

def test_conflict_resolution_e5_floor_breach(client, valid_person_b_payload):
    """Test that E5 floor breach overrides readiness band to Not Ready."""
    with patch("app.orchestrator.get_readiness_score") as mock_e5, \
         patch("app.orchestrator.map_livelihood") as mock_e6, \
         patch("app.orchestrator.generate_person_b_recommendations") as mock_e4:
         
        mock_e5.return_value = {
            "score": 75, "band": "Ready", 
            "components": {
                "financial_health": {"score": 75, "weight": 0.35, "factors": {}},
                "housing_stability": {"score": 75, "weight": 0.20, "factors": {}},
                "infrastructure_access": {"score": 75, "weight": 0.15, "factors": {}},
                "household_burden": {"score": 75, "weight": 0.15, "factors": {}},
                "business_viability": {"score": 75, "weight": 0.15, "factors": {}}
            }, 
            "mapped_features": {}, "imputed_fields": [], "policy_override_applied": True,
            "thresholds": {"financial_health_floor": 0.5, "strong_status_min": 70, "satisfactory_status_min": 50, "band_ready_min": 75, "band_moderately_ready_min": 50, "band_needs_improvement_min": 25}
        }
        mock_e6.return_value = {"label": "Services", "description": "Desc", "cluster_id": 2}
        mock_e4.return_value = {"decision_verdict": "Likely", "primary_reason": "Mock reason", "contributing_factors": [{"feature": "mock", "value": "mock", "evidence": "mock", "reason": "mock", "improvement_advice": "mock"}], "triggered_rule_ids": ["R1"]}
        
        response = client.post("/api/assess", json=valid_person_b_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["readiness"]["band"] == "Not Ready"
        assert data["readiness"]["score"] == 0
        
        # Verify database flags
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT policy_override_flags FROM audit_log WHERE correlation_id = ?", (data["correlation_id"],))
        row = cursor.fetchone()
        conn.close()
        
        flags = json.loads(row[0])
        assert "OVERRIDE_E5_FLOOR_BREACH" in flags
        assert "ENGINE_POLICY_OVERRIDE" in flags

# ── 5. Fail-Closed Audit Commit Tests ────────────────────────────────────

def test_fail_closed_audit_commit(client, valid_person_a_payload):
    """Verify that a SQLite exception during commit causes HTTP 500 (Fail-Closed)."""
    with patch("app.orchestrator.get_eligibility") as mock_e1, \
         patch("app.orchestrator.get_risk_tier") as mock_e2, \
         patch("app.orchestrator.get_borrower_archetype") as mock_e3, \
         patch("app.orchestrator.generate_person_a_recommendations") as mock_e4, \
         patch("app.orchestrator.write_audit_record", side_effect=AuditLogError("SQLite database is locked")):
         
        mock_e1.return_value = {"verdict": "Likely", "probability": 0.75, "bias": 0.5, "feature_contributions": {"f1": 0.25}}
        mock_e2.return_value = {"risk_tier": "P1", "tier_description": "Low Risk", "thresholds": {"p1_min": 701, "p2_min": 669, "p2_max": 700, "p3_min": 659, "p3_max": 668, "p4_max": 658}}
        mock_e3.return_value = {"cluster_id": 0, "archetype_label": "Highly Tenured Veterans"}
        mock_e4.return_value = {"decision_verdict": "Likely", "primary_reason": "Mock reason", "contributing_factors": [{"feature": "mock", "value": "mock", "evidence": "mock", "reason": "mock", "improvement_advice": "mock"}], "triggered_rule_ids": ["R1"]}
        
        response = client.post("/api/assess", json=valid_person_a_payload)
        assert response.status_code == 500
        data = response.json()
        assert data["status"] == "error"
        assert "withheld" in data["error"]["message"].lower()

# ── 6. Health Check Tests ────────────────────────────────────────────────

def test_health_live(client):
    """Verify live endpoint responds."""
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"

def test_health_ready_success(client):
    """Verify ready check succeeds when models exist."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "READY"

def test_health_ready_failure(client):
    """Verify ready check degrades when dependencies are unhealthy."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("DEGRADED", "READY")

def test_health_deep(client):
    """Verify deep health check returns DB state."""
    response = client.get("/health/deep")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert data["dependencies"]["sqlite_writable"] == "CONNECTED"

# ── 7. Person A Guardrails Tests ─────────────────────────────────────────

def test_person_a_age_term_guardrail(client, valid_person_a_payload):
    """Verify that Age + Term > 70 forces Unlikely verdict."""
    payload = valid_person_a_payload.copy()
    payload["age"] = 55
    payload["loan_term"] = 20  # Total 75
    
    with patch("app.orchestrator.get_eligibility") as mock_e1, \
         patch("app.orchestrator.get_risk_tier") as mock_e2, \
         patch("app.orchestrator.get_borrower_archetype") as mock_e3, \
         patch("app.orchestrator.generate_person_a_recommendations") as mock_e4:
         
        mock_e1.return_value = {"verdict": "Likely", "probability": 0.8, "bias": 0.5, "feature_contributions": {}}
        mock_e2.return_value = {"risk_tier": "P1", "tier_description": "Low Risk", "thresholds": {"p1_min": 700, "p2_min": 600, "p2_max": 699, "p3_min": 500, "p3_max": 599, "p4_max": 499}}
        mock_e3.return_value = {"cluster_id": 0, "archetype_label": "Mock"}
        mock_e4.return_value = {"decision_verdict": "Unlikely", "primary_reason": "Mock", "contributing_factors": [], "triggered_rule_ids": ["A-POLICY-002"]}
        
        response = client.post("/api/assess", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["eligibility"]["verdict"] == "Unlikely"
        
        # Verify database flags
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT policy_override_flags FROM audit_log WHERE correlation_id = ?", (data["correlation_id"],))
        row = cursor.fetchone()
        conn.close()
        
        flags = json.loads(row[0])
        assert "OVERRIDE_AGE_TERM_REJECTION" in flags

def test_person_a_lti_guardrail(client, valid_person_a_payload):
    """Verify that LTI > 6.0 forces Unlikely verdict."""
    payload = valid_person_a_payload.copy()
    payload["annual_income"] = 500000
    payload["loan_amount"] = 5000000  # LTI = 10.0
    
    with patch("app.orchestrator.get_eligibility") as mock_e1, \
         patch("app.orchestrator.get_risk_tier") as mock_e2, \
         patch("app.orchestrator.get_borrower_archetype") as mock_e3, \
         patch("app.orchestrator.generate_person_a_recommendations") as mock_e4:
         
        mock_e1.return_value = {"verdict": "Likely", "probability": 0.8, "bias": 0.5, "feature_contributions": {}}
        mock_e2.return_value = {"risk_tier": "P1", "tier_description": "Low Risk", "thresholds": {"p1_min": 700, "p2_min": 600, "p2_max": 699, "p3_min": 500, "p3_max": 599, "p4_max": 499}}
        mock_e3.return_value = {"cluster_id": 0, "archetype_label": "Mock"}
        mock_e4.return_value = {"decision_verdict": "Unlikely", "primary_reason": "Mock", "contributing_factors": [], "triggered_rule_ids": ["A-POLICY-003"]}
        
        response = client.post("/api/assess", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["eligibility"]["verdict"] == "Unlikely"
        
        # Verify database flags
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT policy_override_flags FROM audit_log WHERE correlation_id = ?", (data["correlation_id"],))
        row = cursor.fetchone()
        conn.close()
        
        flags = json.loads(row[0])
        assert "OVERRIDE_LTI_REJECTION" in flags

def test_person_a_low_income_flag(client, valid_person_a_payload):
    """Verify that Low Income appends flag but does not reject."""
    payload = valid_person_a_payload.copy()
    payload["annual_income"] = 250000
    payload["loan_amount"] = 500000  # LTI = 2.0
    
    with patch("app.orchestrator.get_eligibility") as mock_e1, \
         patch("app.orchestrator.get_risk_tier") as mock_e2, \
         patch("app.orchestrator.get_borrower_archetype") as mock_e3, \
         patch("app.orchestrator.generate_person_a_recommendations") as mock_e4:
         
        mock_e1.return_value = {"verdict": "Likely", "probability": 0.8, "bias": 0.5, "feature_contributions": {}}
        mock_e2.return_value = {"risk_tier": "P1", "tier_description": "Low Risk", "thresholds": {"p1_min": 700, "p2_min": 600, "p2_max": 699, "p3_min": 500, "p3_max": 599, "p4_max": 499}}
        mock_e3.return_value = {"cluster_id": 0, "archetype_label": "Mock"}
        mock_e4.return_value = {"decision_verdict": "Likely", "primary_reason": "Mock", "contributing_factors": [], "triggered_rule_ids": ["A-POLICY-004"]}
        
        response = client.post("/api/assess", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["eligibility"]["verdict"] == "Likely"
        
        # Verify database flags
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT policy_override_flags FROM audit_log WHERE correlation_id = ?", (data["correlation_id"],))
        row = cursor.fetchone()
        conn.close()
        
        flags = json.loads(row[0])
        assert "FLAG_LOW_INCOME_REVIEW" in flags

# --- PERSON B GUARDRAIL TESTS ---

def test_person_b_extreme_debt(client, valid_person_b_payload):
    payload = valid_person_b_payload.copy()
    payload["loan_amount"] = 5000000  # LTI = 10.0
    
    with patch("app.orchestrator.get_readiness_score") as mock_e5, \
         patch("app.orchestrator.map_livelihood") as mock_livelihood, \
         patch("app.orchestrator.generate_person_b_recommendations") as mock_e4:
         
        mock_e5.return_value = {
            "score": 80,
            "band": "Ready",
            "components": {
                "financial_health": {"score": 80, "weight": 0.35, "factors": {}},
                "housing_stability": {"score": 80, "weight": 0.20, "factors": {}},
                "infrastructure_access": {"score": 80, "weight": 0.15, "factors": {}},
                "household_burden": {"score": 80, "weight": 0.15, "factors": {}},
                "business_viability": {"score": 80, "weight": 0.15, "factors": {}}
            },
            "policy_override_applied": False,
            "thresholds": {"strong_status_min": 70}
        }
        mock_livelihood.return_value = {"cluster_id": 1, "label": "Mock", "description": "Mock"}
        mock_e4.return_value = {"decision_verdict": "Not Ready", "primary_reason": "Mock", "contributing_factors": []}
        
        response = client.post("/api/assess", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["readiness"]["band"] == "Not Ready"
        assert data["readiness"]["score"] == 0
        
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT policy_override_flags FROM audit_log WHERE correlation_id = ?", (data["correlation_id"],))
        row = cursor.fetchone()
        conn.close()
        
        flags = json.loads(row[0])
        assert "OVERRIDE_EXTREME_DEBT" in flags

def test_person_b_purpose_misalignment(client, valid_person_b_payload):
    payload = valid_person_b_payload.copy()
    
    with patch("app.orchestrator.get_readiness_score") as mock_e5, \
         patch("app.orchestrator.map_livelihood") as mock_livelihood, \
         patch("app.orchestrator.generate_person_b_recommendations") as mock_e4:
         
        mock_e5.return_value = {
            "score": 95,
            "band": "Ready",
            "components": {
                "financial_health": {"score": 95, "weight": 0.35, "factors": {}},
                "housing_stability": {"score": 95, "weight": 0.20, "factors": {}},
                "infrastructure_access": {"score": 95, "weight": 0.15, "factors": {}},
                "household_burden": {"score": 95, "weight": 0.15, "factors": {}},
                "business_viability": {"score": 95, "weight": 0.15, "factors": {"purpose_alignment": "Misaligned"}}
            },
            "policy_override_applied": False,
            "thresholds": {"strong_status_min": 70}
        }
        mock_livelihood.return_value = {"cluster_id": 1, "label": "Mock", "description": "Mock"}
        mock_e4.return_value = {"decision_verdict": "Moderately Ready", "primary_reason": "Mock", "contributing_factors": []}
        
        response = client.post("/api/assess", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["readiness"]["band"] == "Moderately Ready"
        assert data["readiness"]["score"] == 74
        
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT policy_override_flags FROM audit_log WHERE correlation_id = ?", (data["correlation_id"],))
        row = cursor.fetchone()
        conn.close()
        
        flags = json.loads(row[0])
        assert "FLAG_PURPOSE_MISMATCH" in flags

def test_person_b_low_income(client, valid_person_b_payload):
    payload = valid_person_b_payload.copy()
    payload["annual_income"] = 100000
    payload["loan_amount"] = 50000  # LTI = 0.5
    
    with patch("app.orchestrator.get_readiness_score") as mock_e5, \
         patch("app.orchestrator.map_livelihood") as mock_livelihood, \
         patch("app.orchestrator.generate_person_b_recommendations") as mock_e4:
         
        mock_e5.return_value = {
            "score": 85,
            "band": "Ready",
            "components": {
                "financial_health": {"score": 85, "weight": 0.35, "factors": {}},
                "housing_stability": {"score": 85, "weight": 0.20, "factors": {}},
                "infrastructure_access": {"score": 85, "weight": 0.15, "factors": {}},
                "household_burden": {"score": 85, "weight": 0.15, "factors": {}},
                "business_viability": {"score": 85, "weight": 0.15, "factors": {}}
            },
            "policy_override_applied": False,
            "thresholds": {"strong_status_min": 70}
        }
        mock_livelihood.return_value = {"cluster_id": 1, "label": "Mock", "description": "Mock"}
        mock_e4.return_value = {"decision_verdict": "Ready", "primary_reason": "Mock", "contributing_factors": []}
        
        response = client.post("/api/assess", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["readiness"]["band"] == "Ready"
        assert data["readiness"]["score"] == 85
        
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT policy_override_flags FROM audit_log WHERE correlation_id = ?", (data["correlation_id"],))
        row = cursor.fetchone()
        conn.close()
        
        flags = json.loads(row[0])
        assert "FLAG_LOW_INCOME_REVIEW" in flags

def test_person_b_e5_floor_breach(client, valid_person_b_payload):
    payload = valid_person_b_payload.copy()
    
    with patch("app.orchestrator.get_readiness_score") as mock_e5, \
         patch("app.orchestrator.map_livelihood") as mock_livelihood, \
         patch("app.orchestrator.generate_person_b_recommendations") as mock_e4:
         
        mock_e5.return_value = {
            "score": 0,
            "band": "Not Ready",
            "components": {
                "financial_health": {"score": 0, "weight": 0.35, "factors": {}},
                "housing_stability": {"score": 0, "weight": 0.20, "factors": {}},
                "infrastructure_access": {"score": 0, "weight": 0.15, "factors": {}},
                "household_burden": {"score": 0, "weight": 0.15, "factors": {}},
                "business_viability": {"score": 0, "weight": 0.15, "factors": {}}
            },
            "policy_override_applied": True,
            "thresholds": {"strong_status_min": 70}
        }
        mock_livelihood.return_value = {"cluster_id": 1, "label": "Mock", "description": "Mock"}
        mock_e4.return_value = {"decision_verdict": "Not Ready", "primary_reason": "Mock", "contributing_factors": []}
        
        response = client.post("/api/assess", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["readiness"]["band"] == "Not Ready"
        assert data["readiness"]["score"] == 0
        
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT policy_override_flags FROM audit_log WHERE correlation_id = ?", (data["correlation_id"],))
        row = cursor.fetchone()
        conn.close()
        
        flags = json.loads(row[0])
        assert "OVERRIDE_E5_FLOOR_BREACH" in flags

def test_person_b_guardrails_simultaneous(client, valid_person_b_payload):
    payload = valid_person_b_payload.copy()
    payload["loan_amount"] = 5000000  # Extreme debt
    
    with patch("app.orchestrator.get_readiness_score") as mock_e5, \
         patch("app.orchestrator.map_livelihood") as mock_livelihood, \
         patch("app.orchestrator.generate_person_b_recommendations") as mock_e4:
         
        # Also simulate misalignment
        mock_e5.return_value = {
            "score": 95,
            "band": "Ready",
            "components": {
                "financial_health": {"score": 95, "weight": 0.35, "factors": {}},
                "housing_stability": {"score": 95, "weight": 0.20, "factors": {}},
                "infrastructure_access": {"score": 95, "weight": 0.15, "factors": {}},
                "household_burden": {"score": 95, "weight": 0.15, "factors": {}},
                "business_viability": {"score": 95, "weight": 0.15, "factors": {"purpose_alignment": "Misaligned"}}
            },
            "policy_override_applied": False,
            "thresholds": {"strong_status_min": 70}
        }
        mock_livelihood.return_value = {"cluster_id": 1, "label": "Mock", "description": "Mock"}
        mock_e4.return_value = {"decision_verdict": "Not Ready", "primary_reason": "Mock", "contributing_factors": []}
        
        response = client.post("/api/assess", json=payload)
        assert response.status_code == 200
        data = response.json()
        # Extreme Debt wins
        assert data["readiness"]["band"] == "Not Ready"
        assert data["readiness"]["score"] == 0
        
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT policy_override_flags FROM audit_log WHERE correlation_id = ?", (data["correlation_id"],))
        row = cursor.fetchone()
        conn.close()
        
        flags = json.loads(row[0])
        assert "OVERRIDE_EXTREME_DEBT" in flags
        assert "FLAG_PURPOSE_MISMATCH" not in flags  # since elif prevents evaluation
