"""
engines/

RiskIntel engine modules — activated phase by phase:

    Phase 3  → eligibility.py   (E1 — Binary classification, Random Forest)
    Phase 4  → risk_tier.py     (E2 — Rule-based CIBIL threshold logic)
    Phase 5  → archetype.py     (E3 — K-Means borrower clustering)
    Phase 6  → readiness.py     (E5 — Weighted composite scoring)
    Phase 7  → livelihood.py    (E6 — K-Means livelihood clustering)
    Phase 8  → recommendation.py (E4 — Rule-based deterministic advice)

Each engine is a stateless module: receives a plain dict, returns a plain dict.
No engine has side effects. No engine depends on another engine's internal state.
"""
