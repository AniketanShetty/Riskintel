import pytest
from fastapi.testclient import TestClient

# Assuming ml_service.py is in the same directory or Python path
from ml_service import app

client = TestClient(app)

# The baseline golden payload
VALID_PAYLOAD = {
    "cibil_score": 750,
    "net_monthly_income": 85000.50,
    "age": 35,
    "time_with_curr_empr": 48,
    "education": "GRADUATE"
}

@pytest.mark.parametrize(
    "test_case_name, payload_override, expected_status, expected_error_loc",
    [
        (
            "Valid Payload",
            {},
            200,
            None
        ),
        (
            "Extra Fields (Schema Drift Protection)",
            {"favorite_color": "blue", "dependents": 2},
            200,
            None
        ),
        (
            "Stringified Numbers (Type Coercion)",
            {"cibil_score": "750", "net_monthly_income": "85000.50"},
            200,
            None
        ),
        (
            "Boundary Values (Exact Edges)",
            {"cibil_score": 300, "age": 18, "time_with_curr_empr": 0},
            200,
            None
        ),
        (
            "Null Values",
            {"net_monthly_income": None},
            422,
            "net_monthly_income"
        ),
        (
            "Missing Fields",
            {"cibil_score": None}, # Using None as a placeholder; actual deletion happens in the test body
            422,
            "cibil_score"
        ),
        (
            "Negative Values",
            {"age": -5, "net_monthly_income": -1000},
            422,
            "age"
        ),
        (
            "Invalid Enums (SQLi/XSS Attempt)",
            {"education": "GRADUATE; DROP TABLE users;"},
            422,
            "education"
        ),
        (
            "Overflow Values",
            {"net_monthly_income": 1e999},
            422, # Pydantic or FastAPI JSON parser will reject this
            None # Error location varies depending on the parser depth
        ),
    ]
)
def test_ml_contract_fuzzing(test_case_name, payload_override, expected_status, expected_error_loc):
    """
    Fuzz tests the ML Inference Service API contract to ensure it acts as an impermeable shield
    for the underlying scikit-learn models.
    """
    # Create a fresh copy of the valid payload
    test_payload = dict(VALID_PAYLOAD)
    
    # Apply overrides
    for k, v in payload_override.items():
        if test_case_name == "Missing Fields" and v is None:
            del test_payload[k]
        else:
            test_payload[k] = v

    response = client.post("/v1/predict", json=test_payload)

    # Assert HTTP Status
    assert response.status_code == expected_status, f"[{test_case_name}] Expected {expected_status}, got {response.status_code}."

    if expected_status == 200:
        # Assert successful inference structure
        data = response.json()
        assert "archetype_label" in data
        assert "cluster_distances" in data
        assert "model_id" in data
    
    elif expected_status == 422 and expected_error_loc:
        # Assert Pydantic caught the specific malformed field
        errors = response.json().get("detail", [])
        error_fields = [err.get("loc", [])[-1] for err in errors]
        assert expected_error_loc in error_fields, f"[{test_case_name}] Expected validation error on '{expected_error_loc}', got {error_fields}."
