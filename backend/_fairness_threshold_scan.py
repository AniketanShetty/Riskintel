"""CIBIL threshold scan for first-time borrower detection.
Sweep cibil_score 0..900, hold everything else constant.
"""
import sys; sys.path.insert(0, r"C:\Users\anike\Desktop\Riskintel\backend")
import warnings; warnings.filterwarnings("ignore")
from app.orchestrator import execute_orchestrator
import sys

base = {
    "user_type": "person_a",
    "full_name": "Sweep",
    "age": 30, "gender": "F",
    "marital_status": "Single", "education": "Graduate",
    "self_employed": "No", "years_at_current_employer": 4,
    "annual_income": 600000, "dependents": 0,
    "loan_amount": 500000,
    "loan_term": 24, "loan_purpose": "personal",
    "residential_assets_value": 0, "commercial_assets_value": 0,
    "luxury_assets_value": 0, "bank_asset_value": 0,
}

print(f"{'cibil':>6} {'user_type':>11} {'verdict':>12} {'prob':>8} {'tier':>5} {'route':>6}")
print("-"*60)
for cibil in [0, -1, 100, 200, 300, 400, 500, 540, 549, 550, 600, 658, 659, 700, 800, 900, 1000]:
    p = base.copy()
    p["cibil_score"] = cibil
    try:
        out = execute_orchestrator(p.copy())
        if out.get('status') == 'error':
            print(f"{cibil:>6} EXCEPTION: {out.get('error', {}).get('code', 'unknown')}")
            continue
        ut = out.get('user_type')
        elig = out.get('eligibility', {})
        tier = out.get('risk_tier', {})
        route = "A→B" if (ut == "person_b" and p['user_type'] == "person_a") else "A→A"
        print(f"{cibil:>6} {ut:>11} {str(elig.get('verdict','')):>12} {str(elig.get('probability',''))[:8]:>8} {str(tier.get('risk_tier','')):>5} {route:>6}")
    except Exception as e:
        print(f"{cibil:>6} EXCEPTION: {type(e).__name__}")
