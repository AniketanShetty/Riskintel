import pytest
from app.engines.recommendation.schema import Rule
from app.engines.recommendation.evaluator import evaluate_rules
from app.engines.recommendation.context import build_person_a_context
from app.engines.recommendation.recommendation_engine import generate_person_a_recommendations, generate_person_b_recommendations
from app.engines.recommendation.rules_person_a import PERSON_A_RULES

def test_determinism_and_sorting():
    rules = [
        Rule("Z-001", "strengths", 10, lambda ctx: True, "Z rule", lambda ctx: {}),
        Rule("A-001", "strengths", 10, lambda ctx: True, "A rule", lambda ctx: {}),
        Rule("M-001", "strengths", 50, lambda ctx: True, "M rule", lambda ctx: {}),
    ]
    output, ids = evaluate_rules(rules, {}, ["strengths"])
    assert output["strengths"] == ["M rule", "A rule", "Z rule"]
    assert ids == ["M-001", "A-001", "Z-001"]

def test_truncation_and_audit_log():
    rules = [Rule(f"R-{i:03d}", "strengths", 10, lambda ctx: True, f"Rule {i}", lambda ctx: {}) for i in range(10)]
    output, ids = evaluate_rules(rules, {}, ["strengths"])
    assert len(output["strengths"]) == 5
    assert len(ids) == 5
    assert ids == ["R-000", "R-001", "R-002", "R-003", "R-004"]

def test_fallback_rules():
    rules = [
        Rule("FALLBACK", "strengths", 0, lambda ctx: True, "Fallback", lambda ctx: {}),
        Rule("REAL", "strengths", 10, lambda ctx: False, "Never triggers", lambda ctx: {})
    ]
    output, _ = evaluate_rules(rules, {}, ["strengths"])
    assert output["strengths"] == ["Fallback"]

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

def test_verdict_anchoring():
    # If verdict is Unlikely, strong positive rules should be suppressed
    # Test A-STR-001 shouldn't trigger
    ctx = {
        "eligibility": {"verdict": "Unlikely"},
        "risk_tier": {"tier": "P1"}
    }
    output, _ = evaluate_rules(PERSON_A_RULES, ctx, ["strengths"])
    # It should fallback or use the specific Unlikely strength (A-STR-003)
    assert "Historical credit score is strong, though current loan parameters reduce eligibility." in output["strengths"]
    assert "Credit score (N/A) indicates strong repayment reliability." not in output["strengths"]

def test_educational_phrasing_compliance():
    # Ensure no rule contains prescriptive financial advice commands
    bad_words = ["Reduce ", "Pay ", "Increase ", "Apply "]
    all_rules = PERSON_A_RULES
    for rule in all_rules:
        for word in bad_words:
            assert word not in rule.text_template

def test_contract_shape_person_a():
    output = generate_person_a_recommendations({}, {}, {}, {})
    assert "recommendation_version" in output
    assert len(output["strengths"]) >= 1
    assert len(output["risk_factors"]) >= 1

def test_contract_shape_person_b():
    output = generate_person_b_recommendations({}, {}, {})
    assert "recommendation_version" in output
    assert len(output["strengths"]) >= 1
    assert len(output["improvement_areas"]) >= 1
