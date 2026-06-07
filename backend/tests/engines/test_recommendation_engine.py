import pytest
from app.engines.recommendation.schema import ExplanationRule
from app.engines.recommendation.evaluator import evaluate_rules
from app.engines.recommendation.context import build_person_a_context
from app.engines.recommendation.recommendation_engine import generate_person_a_recommendations, generate_person_b_recommendations
from app.engines.recommendation.rules_person_a import PERSON_A_RULES

def test_determinism_and_sorting():
    rules = [
        ExplanationRule("Z-001", "f_z", 10, lambda ctx: True, lambda ctx: "e", "Z rule", "a", lambda ctx: {}),
        ExplanationRule("A-001", "f_a", 10, lambda ctx: True, lambda ctx: "e", "A rule", "a", lambda ctx: {}),
        ExplanationRule("M-001", "f_m", 50, lambda ctx: True, lambda ctx: "e", "M rule", "a", lambda ctx: {}),
    ]
    output, ids = evaluate_rules(rules, {})
    reasons = [f["reason"] for f in output]
    assert reasons == ["M rule", "A rule", "Z rule"]
    assert ids == ["M-001", "A-001", "Z-001"]

def test_truncation_and_audit_log():
    rules = [ExplanationRule(f"R-{i:03d}", "f", 10, lambda ctx: True, lambda ctx: "e", f"Rule {i}", "a", lambda ctx: {}) for i in range(10)]
    output, ids = evaluate_rules(rules, {}, max_factors=5)
    assert len(output) == 5
    assert len(ids) == 5
    assert ids == ["R-000", "R-001", "R-002", "R-003", "R-004"]

def test_fallback_rules():
    rules = [
        ExplanationRule("FALLBACK", "f", 0, lambda ctx: True, lambda ctx: "e", "Fallback", "a", lambda ctx: {}),
        ExplanationRule("REAL", "f", 10, lambda ctx: False, lambda ctx: "e", "Never triggers", "a", lambda ctx: {})
    ]
    output, _ = evaluate_rules(rules, {})
    assert output[0]["reason"] == "Fallback"

def test_immutability_blocking():
    inputs = {
        "annual_income": 1000,
        "age": 30,
        "gender": "M",
        "social_class": "General"
    }
    ctx = build_person_a_context(inputs, {}, {}, {})
    assert "annual_income" in ctx["inputs"]
    assert "age" not in ctx["inputs"]
    assert "gender" not in ctx["inputs"]
    assert "social_class" not in ctx["inputs"]

def test_contract_shape_person_a():
    output = generate_person_a_recommendations({}, {}, {}, {})
    assert "recommendation_version" in output
    assert "decision_verdict" in output
    assert "primary_reason" in output
    assert isinstance(output["contributing_factors"], list)

def test_contract_shape_person_b():
    # Provide a valid readiness_res so the threshold-gated rules
    # (B-IMP-001 / B-IMP-002) do not raise GovernanceError. With
    # financial_health=80 (above strong_status_min=70) and
    # business_viability=80, the improvement rules do not fire. With
    # band="Moderately Ready", B-STR-001 does not fire. The contract-shape
    # test only asserts the output structure, not the rule set.
    readiness_res = {
        "band": "Moderately Ready",
        "score": 60,
        "components": {
            "financial_health": {"score": 80, "weight": 0.35, "factors": {}},
            "housing_stability": {"score": 75, "weight": 0.20, "factors": {}},
            "infrastructure_access": {"score": 70, "weight": 0.15, "factors": {}},
            "household_burden": {"score": 65, "weight": 0.15, "factors": {}},
            "business_viability": {"score": 80, "weight": 0.15, "factors": {"purpose_alignment": "Aligned", "has_secondary_income": False, "primary_business": "Kirana shop"}},
        },
        "thresholds": {
            "strong_status_min": 70,
            "satisfactory_status_min": 50,
            "band_ready_min": 75,
            "band_moderately_ready_min": 50,
            "band_needs_improvement_min": 25,
            "financial_health_floor": 0.5,
        },
    }
    livelihood_res = {"label": "Kirana shop", "cluster_id": 2, "description": ""}
    output = generate_person_b_recommendations({}, readiness_res, livelihood_res)
    assert "recommendation_version" in output
    assert "decision_verdict" in output
    assert "primary_reason" in output
    assert isinstance(output["contributing_factors"], list)
