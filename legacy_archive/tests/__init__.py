"""
tests/

RiskIntel test suite.

Structure (activated phase by phase):
    test_health.py          — Phase 1: Flask app starts, GET / returns 200
    test_preprocess_a.py    — Phase 2: Dataset A cleaning produces expected shape
    test_preprocess_b.py    — Phase 2: Dataset B cleaning produces expected shape
    test_preprocess_c.py    — Phase 2: Dataset C cleaning produces expected shape
    test_eligibility.py     — Phase 3: Eligibility engine returns valid contract
    test_risk_tier.py       — Phase 4: Risk tier logic returns P1–P4
    test_archetype.py       — Phase 5: Archetype engine returns valid label
    test_readiness.py       — Phase 6: Readiness engine scores within 0–100
    test_livelihood.py      — Phase 7: Livelihood engine returns valid label
    test_recommendation.py  — Phase 8: Recommendation engine returns required keys
    test_api.py             — Phase 9: Full API request/response contract tests

Run all tests:
    cd backend/
    pytest ../tests/ -v
"""
