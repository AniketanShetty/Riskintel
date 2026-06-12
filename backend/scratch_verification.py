import json
import sqlite3
from fastapi.testclient import TestClient
from app.main import app
from app.audit import get_db_path
from unittest.mock import patch

client = TestClient(app)

base_payload = {
    "user_type": "person_a",
    "full_name": "Test User",
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

scenarios = [
    ("Age 70 + Term 20", {"age": 70, "loan_term": 20, "cibil_score": 800, "annual_income": 1000000, "loan_amount": 100000}),
    ("Age 50 + Term 20", {"age": 50, "loan_term": 20, "cibil_score": 800, "annual_income": 1000000, "loan_amount": 100000}),
    ("Income 100000 + Loan 50000000", {"annual_income": 100000, "loan_amount": 50000000, "cibil_score": 800}),
    ("Income 1000000 + Loan 100000", {"annual_income": 1000000, "loan_amount": 100000, "cibil_score": 800}),
    ("Income below review threshold", {"annual_income": 250000, "loan_amount": 500000, "cibil_score": 800}),
    ("P4 + LTI simultaneously", {"cibil_score": 400, "annual_income": 100000, "loan_amount": 50000000}),
    ("Age-Term + P4 simultaneously", {"age": 60, "loan_term": 20, "cibil_score": 400}),
    ("Age-Term + LTI simultaneously", {"age": 60, "loan_term": 20, "annual_income": 100000, "loan_amount": 50000000, "cibil_score": 800}),
    ("All guardrails simultaneously", {"age": 60, "loan_term": 20, "cibil_score": 400, "annual_income": 100000, "loan_amount": 50000000}),
]

def run_scenario(name, overrides):
    payload = base_payload.copy()
    payload.update(overrides)
    
    # We must patch the ML parts since we don't want real ML execution to fail if models are missing or if it doesn't give Likely.
    # Actually, we want to see the orchestrator override. So we simulate E1 saying Highly Likely.
    # Wait, the real repository reality is whether it runs. If we don't patch, we test the full pipeline.
    # Let's try running without patching to test REALITY. But wait, if cibil is 400, Risk Tier will naturally give P4.
    pass

# We will run real integration testing without mocking to verify true reality.
for name, overrides in scenarios:
    payload = base_payload.copy()
    payload.update(overrides)
    
    response = client.post("/api/assess", json=payload)
    if response.status_code != 200:
        print(f"[{name}] FAILED HTTP {response.status_code}: {response.text}")
        continue
        
    data = response.json()
    verdict = data.get("eligibility", {}).get("verdict", "N/A")
    rules = data.get("explanation", {}).get("triggered_rule_ids", [])
    
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT policy_override_flags FROM audit_log WHERE correlation_id = ?", (data["correlation_id"],))
    row = cursor.fetchone()
    conn.close()
    
    flags = json.loads(row[0]) if row else []
    
    print(f"[{name}] Verdict: {verdict}")
    print(f"  Overrides: {flags}")
    print(f"  Rules Fired: {rules}")
    print("-" * 40)
