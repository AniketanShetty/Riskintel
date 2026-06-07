"""First-time vs established-borrower counterfactual.
Two personas. Hold all other variables. Vary only credit-history features.

For Person A we manipulate E1 (E1 doesn't have explicit credit-history fields but CIBIL
exists in the Person A intake; we test cibil_score=0 vs 700 to isolate bureau availability).
For Person B (Readiness) we vary credit-style proxies that DO exist in the data:
  - loan_purpose, sanitary_availability, water_availability, house_area, type_of_house
but NOT credit history (the Person B data has no prior-loan / bureau columns at all).

Persona A = Person B on everything except cibil_score, with cibil_score treated as a proxy
for "available bureau history". For Person B (E5) we use the loan_amount field as
the only signal that changes; Person B data has no prior-loan field so we cannot
synthesize "credit history" — we acknowledge this gap.
"""
import sys
sys.path.insert(0, r"C:\Users\anike\Desktop\Riskintel\backend")

import warnings; warnings.filterwarnings("ignore")

from app.orchestrator import execute_orchestrator
from app.audit import get_db_path
import sqlite3, json

# --------- Person A personas (E1) ---------
# Both have the same income, assets, demographics. Only cibil_score differs.
# cibil_score=0 is the documented sentinel for "no bureau history" (routing.py:77)
# cibil_score=700 represents a thin bureau file with a moderate score.

pa_no_history = {
    "user_type": "person_a",
    "full_name": "Persona No History",
    "age": 30, "gender": "F",
    "marital_status": "Single", "education": "Graduate",
    "self_employed": "No", "years_at_current_employer": 4,
    "annual_income": 600000, "dependents": 0,
    "cibil_score": 0,           # sentinel: no bureau
    "loan_amount": 500000,
    "loan_term": 24, "loan_purpose": "personal",
    "residential_assets_value": 0, "commercial_assets_value": 0,
    "luxury_assets_value": 0, "bank_asset_value": 0,
}

pa_5y_history = {
    "user_type": "person_a",
    "full_name": "Persona 5y History",
    "age": 30, "gender": "F",
    "marital_status": "Single", "education": "Graduate",
    "self_employed": "No", "years_at_current_employer": 4,
    "annual_income": 600000, "dependents": 0,
    "cibil_score": 700,         # 5y good repayment
    "loan_amount": 500000,
    "loan_term": 24, "loan_purpose": "personal",
    "residential_assets_value": 0, "commercial_assets_value": 0,
    "luxury_assets_value": 0, "bank_asset_value": 0,
}

# --------- Person B personas (E5/E6) ---------
# Person B's data has NO prior-loan / bureau columns. The closest proxies to credit
# history are: house_type, water/sanitary, loan_purpose, loan_amount, monthly_expenses.
# We hold demographics identical; we vary "credit-availability proxies" by setting
# them to floor values (Person A) vs typical middle values (Person B).
# We cannot simulate 5 years of repayment history because E5's data has no such column.
# This is itself a finding: Person B has NO credit history signal at all.

pb_no_history = {
    "user_type": "person_b",
    "full_name": "Persona No History",
    "age": 30, "gender": "F",
    "primary_business": "Tailoring", "secondary_business": "none",
    "annual_income": 60000, "monthly_expenses": 3000,
    "loan_amount": 5000, "loan_purpose": "Apparels",
    "loan_tenure": 12, "loan_installments": 12,
    "young_dependents": 0, "old_dependents": 0,
    "occupants_count": 1, "home_ownership": 0,
    "type_of_house": "R", "house_area": 200,
    "sanitary_availability": 0, "water_availability": 0.0,
    "social_class": "GEN"
}

pb_5y_history_proxy = {
    "user_type": "person_b",
    "full_name": "Persona 5y History",
    "age": 30, "gender": "F",
    "primary_business": "Tailoring", "secondary_business": "none",
    "annual_income": 60000, "monthly_expenses": 3000,
    "loan_amount": 5000, "loan_purpose": "Apparels",
    "loan_tenure": 12, "loan_installments": 12,
    "young_dependents": 0, "old_dependents": 0,
    "occupants_count": 1, "home_ownership": 0,
    "type_of_house": "T1", "house_area": 450,
    "sanitary_availability": 1, "water_availability": 1.0,
    "social_class": "GEN"
}

def run(p, label):
    try:
        out = execute_orchestrator(p.copy())
        if out.get('status') == 'error':
            print(f"  {label}: ERROR {out['error']['code']}: {out['error']['message']}")
            return None
        elig = out.get('eligibility', {})
        tier = out.get('risk_tier', {})
        read = out.get('readiness', {})
        return {
            "verdict": elig.get('verdict'),
            "prob": elig.get('probability'),
            "tier": tier.get('risk_tier'),
            "band": read.get('band'),
            "score": read.get('score'),
            "components": read.get('components', {}),
            "policy_override": read.get('policy_override_applied'),
            "floor_breach": read.get('policy_override_applied'),
            "imputed": read.get('imputed_fields'),
        }
    except Exception as e:
        print(f"  {label}: EXCEPTION {type(e).__name__}: {e}")
        return None

print("="*72)
print("PERSON A — E1 ELIGIBILITY (CIBIL=0 vs CIBIL=700)")
print("="*72)
a_noh = run(pa_no_history, "Person A: no history (CIBIL=0)")
a_yes = run(pa_5y_history, "Person A: 5y history (CIBIL=700)")
for label, r in [("A_no_history", a_noh), ("A_5y_history", a_yes)]:
    print(f"  {label}: verdict={r['verdict']}  prob={r['prob']}  tier={r['tier']}")
print()
print("Counterfactual delta:")
if a_noh and a_yes:
    print(f"  verdict:   {a_noh['verdict']}  ->  {a_yes['verdict']}")
    # r1/r2 captured above already
    # Top contributors
    r1 = execute_orchestrator(pa_no_history.copy())
    r2 = execute_orchestrator(pa_5y_history.copy())
    c1 = sorted(r1.get('eligibility', {}).get('feature_contributions', {}).items(), key=lambda x: -abs(x[1]))[:3] if r1.get('eligibility') else []
    c2 = sorted(r2.get('eligibility', {}).get('feature_contributions', {}).items(), key=lambda x: -abs(x[1]))[:3] if r2.get('eligibility') else []
    p1 = r1.get('eligibility', {}).get('probability')
    p2 = r2.get('eligibility', {}).get('probability')
    if p1 is not None and p2 is not None:
        print(f"  prob:      {p1}  ->  {p2}   delta={p2-p1:+.4f}")
    else:
        print(f"  prob:      {p1}  ->  {p2}   delta=undefined (one side rerouted)")
    print(f"  tier:      {a_noh['tier']}  ->  {a_yes['tier']}")
    print(f"  override:  {a_noh['floor_breach']}  ->  {a_yes['floor_breach']}")
    print(f"  top-3 (no hist):  {c1}")
    print(f"  top-3 (5y hist):  {c2}")

# Note: routing behavior
print()
print("Routing trace (no history):")
r1 = execute_orchestrator(pa_no_history.copy())
print(f"  user_type returned: {r1.get('user_type')}  (request was person_a)")
print(f"  archetype: {r1.get('archetype')}")
print(f"  has risk_tier: {r1.get('risk_tier') is not None}")

print()
print("="*72)
print("PERSON B — E5 READINESS (no history proxies vs typical)")
print("="*72)
b_noh = run(pb_no_history, "Person B: no history proxies")
b_yes = run(pb_5y_history_proxy, "Person B: 5y history proxies")
for label, r in [("B_no_history", b_noh), ("B_5y_history", b_yes)]:
    comps = r['components']
    print(f"  {label}: band={r['band']}  score={r['score']}")
    print(f"    components: fh={comps.get('financial_health', {}).get('score')}  hsg={comps.get('housing_stability', {}).get('score')}  infra={comps.get('infrastructure_access', {}).get('score')}  burd={comps.get('household_burden', {}).get('score')}  biz={comps.get('business_viability', {}).get('score')}")
    print(f"    policy_override_applied: {r['floor_breach']}")
print()
print("Counterfactual delta (B no_history vs 5y_history):")
if b_noh and b_yes:
    print(f"  band:     {b_noh['band']}  ->  {b_yes['band']}")
    print(f"  score:    {b_noh['score']}  ->  {b_yes['score']}   delta={b_yes['score']-b_noh['score']:+d}")
    print(f"  floor:    {b_noh['floor_breach']}  ->  {b_yes['floor_breach']}")
    print(f"  threshold cross: {'YES' if b_noh['band'] != b_yes['band'] else 'no'}")

# Audit-log audit-row check
print()
print("="*72)
print("AUDIT LOG ROW COUNT")
print("="*72)
conn = sqlite3.connect(get_db_path())
n = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
print(f"  audit_log rows: {n}")
conn.close()
