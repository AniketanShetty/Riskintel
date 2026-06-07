"""Edge-case probe — sends synthetic edge borrowers through the full orchestrator."""
import sys, json
sys.path.insert(0, r"C:\Users\anike\Desktop\Riskintel\backend")

from app.orchestrator import execute_orchestrator
from app.audit import get_db_path
import sqlite3

cases = {
    "1_Very_young_18": {
        "user_type": "person_b",
        "full_name": "Edge Young", "age": 18, "gender": "M",
        "primary_business": "Tailoring", "secondary_business": "none",
        "annual_income": 50000, "monthly_expenses": 3000,
        "loan_amount": 5000, "loan_purpose": "Apparels",
        "loan_tenure": 12, "loan_installments": 12,
        "young_dependents": 0, "old_dependents": 0,
        "occupants_count": 1, "home_ownership": 0,
        "type_of_house": "R", "house_area": 200,
        "sanitary_availability": 0, "water_availability": 0.0,
        "social_class": "GEN"
    },
    "2_Very_old_70": {
        "user_type": "person_b",
        "full_name": "Edge Old", "age": 70, "gender": "F",
        "primary_business": "Farming", "secondary_business": "Dairy",
        "annual_income": 80000, "monthly_expenses": 4000,
        "loan_amount": 15000, "loan_purpose": "Crop",
        "loan_tenure": 24, "loan_installments": 24,
        "young_dependents": 0, "old_dependents": 2,
        "occupants_count": 3, "home_ownership": 1,
        "type_of_house": "T1", "house_area": 600,
        "sanitary_availability": 1, "water_availability": 1.0,
        "social_class": "OBC"
    },
    "3_Extreme_income_high_50M": {
        "user_type": "person_b",
        "full_name": "Edge Rich", "age": 45, "gender": "M",
        "primary_business": "Manufacturing", "secondary_business": "Wholesale",
        "annual_income": 50000000, "monthly_expenses": 100000,
        "loan_amount": 500000, "loan_purpose": "Equipment",
        "loan_tenure": 36, "loan_installments": 36,
        "young_dependents": 0, "old_dependents": 0,
        "occupants_count": 2, "home_ownership": 1,
        "type_of_house": "T1", "house_area": 2000,
        "sanitary_availability": 1, "water_availability": 1.0,
        "social_class": "GEN"
    },
    "4_Extreme_income_zero": {
        "user_type": "person_b",
        "full_name": "Edge Zero", "age": 35, "gender": "M",
        "primary_business": "Services", "secondary_business": "none",
        "annual_income": 0, "monthly_expenses": 0,
        "loan_amount": 10000, "loan_purpose": "Apparels",
        "loan_tenure": 12, "loan_installments": 12,
        "young_dependents": 3, "old_dependents": 1,
        "occupants_count": 5, "home_ownership": 0,
        "type_of_house": "R", "house_area": 100,
        "sanitary_availability": 0, "water_availability": 0.0,
        "social_class": "SC"
    },
    "5_Extreme_assets_zero": {
        "user_type": "person_b",
        "full_name": "Edge NoAssets", "age": 30, "gender": "F",
        "primary_business": "Tailoring", "secondary_business": "none",
        "annual_income": 60000, "monthly_expenses": 2000,
        "loan_amount": 8000, "loan_purpose": "Apparels",
        "loan_tenure": 12, "loan_installments": 12,
        "young_dependents": 1, "old_dependents": 0,
        "occupants_count": 2, "home_ownership": 0,
        "type_of_house": "R", "house_area": 50,
        "sanitary_availability": 0, "water_availability": 0.0,
        "social_class": "ST"
    },
    "6_Missing_house_area": {
        "user_type": "person_b",
        "full_name": "Edge MissingArea", "age": 40, "gender": "M",
        "primary_business": "Grocery", "secondary_business": "none",
        "annual_income": 100000, "monthly_expenses": 5000,
        "loan_amount": 20000, "loan_purpose": "Stock",
        "loan_tenure": 12, "loan_installments": 12,
        "young_dependents": 2, "old_dependents": 0,
        "occupants_count": 4, "home_ownership": 1,
        "type_of_house": "T2", "house_area": None,
        "sanitary_availability": 1, "water_availability": 0.5,
        "social_class": "OBC"
    },
    "7_Missing_annual_income": {
        "user_type": "person_b",
        "full_name": "Edge MissingIncome", "age": 38, "gender": "F",
        "primary_business": "Tailoring", "secondary_business": "none",
        "annual_income": None, "monthly_expenses": 4500,
        "loan_amount": 15000, "loan_purpose": "Apparels",
        "loan_tenure": 12, "loan_installments": 12,
        "young_dependents": 1, "old_dependents": 0,
        "occupants_count": 3, "home_ownership": 1,
        "type_of_house": "T2", "house_area": 400,
        "sanitary_availability": 1, "water_availability": 1.0,
        "social_class": "OBC"
    },
    "8_Rare_business_Computer_Repair": {
        "user_type": "person_b",
        "full_name": "Edge RareBiz", "age": 32, "gender": "M",
        "primary_business": "Computer Repair", "secondary_business": "none",
        "annual_income": 200000, "monthly_expenses": 6000,
        "loan_amount": 50000, "loan_purpose": "Equipment",
        "loan_tenure": 24, "loan_installments": 24,
        "young_dependents": 0, "old_dependents": 0,
        "occupants_count": 2, "home_ownership": 1,
        "type_of_house": "T1", "house_area": 600,
        "sanitary_availability": 1, "water_availability": 1.0,
        "social_class": "OBC"
    },
    "9_Negative_loan_amount": {
        "user_type": "person_b",
        "full_name": "Edge Negative", "age": 40, "gender": "M",
        "primary_business": "Services", "secondary_business": "none",
        "annual_income": 100000, "monthly_expenses": 5000,
        "loan_amount": -5000, "loan_purpose": "Apparels",
        "loan_tenure": 12, "loan_installments": 12,
        "young_dependents": 1, "old_dependents": 0,
        "occupants_count": 2, "home_ownership": 1,
        "type_of_house": "T1", "house_area": 300,
        "sanitary_availability": 1, "water_availability": 1.0,
        "social_class": "OBC"
    },
    "10_Negative_income": {
        "user_type": "person_b",
        "full_name": "Edge NegIncome", "age": 35, "gender": "M",
        "primary_business": "Services", "secondary_business": "none",
        "annual_income": -100, "monthly_expenses": 5000,
        "loan_amount": 5000, "loan_purpose": "Apparels",
        "loan_tenure": 12, "loan_installments": 12,
        "young_dependents": 1, "old_dependents": 0,
        "occupants_count": 2, "home_ownership": 1,
        "type_of_house": "T1", "house_area": 300,
        "sanitary_availability": 1, "water_availability": 1.0,
        "social_class": "OBC"
    },
    "11_PersonA_young_18_no_income": {
        "user_type": "person_a",
        "full_name": "Edge P-A Young", "age": 18, "gender": "M",
        "marital_status": "Single", "education": "Graduate",
        "self_employed": "No", "years_at_current_employer": 0,
        "annual_income": 0, "dependents": 0,
        "cibil_score": 750, "loan_amount": 300000,
        "loan_term": 12, "loan_purpose": "personal",
        "residential_assets_value": 0, "commercial_assets_value": 0,
        "luxury_assets_value": 0, "bank_asset_value": 0
    },
    "12_PersonA_CIBIL_0_sentinel": {
        "user_type": "person_a",
        "full_name": "Edge Cibil0", "age": 30, "gender": "M",
        "marital_status": "Married", "education": "Graduate",
        "self_employed": "No", "years_at_current_employer": 5,
        "annual_income": 500000, "dependents": 2,
        "cibil_score": 0, "loan_amount": 500000,
        "loan_term": 12, "loan_purpose": "personal",
        "residential_assets_value": 1000000, "commercial_assets_value": 0,
        "luxury_assets_value": 0, "bank_asset_value": 500000
    },
    "13_PersonA_CIBIL_1000_above_range": {
        "user_type": "person_a",
        "full_name": "Edge Cibil1000", "age": 30, "gender": "M",
        "marital_status": "Married", "education": "Graduate",
        "self_employed": "No", "years_at_current_employer": 5,
        "annual_income": 500000, "dependents": 2,
        "cibil_score": 1000, "loan_amount": 500000,
        "loan_term": 12, "loan_purpose": "personal",
        "residential_assets_value": 1000000, "commercial_assets_value": 0,
        "luxury_assets_value": 0, "bank_asset_value": 500000
    },
    "14_PersonA_missing_CIBIL": {
        "user_type": "person_a",
        "full_name": "Edge MissingCibil", "age": 30, "gender": "M",
        "marital_status": "Married", "education": "Graduate",
        "self_employed": "No", "years_at_current_employer": 5,
        "annual_income": 500000, "dependents": 2,
        "cibil_score": None, "loan_amount": 500000,
        "loan_term": 12, "loan_purpose": "personal",
        "residential_assets_value": 1000000, "commercial_assets_value": 0,
        "luxury_assets_value": 0, "bank_asset_value": 0
    },
}

# Fix the malformed case 14
cases["14_PersonA_missing_CIBIL"] = {
    "user_type": "person_a",
    "full_name": "Edge MissingCibil", "age": 30, "gender": "M",
    "marital_status": "Married", "education": "Graduate",
    "self_employed": "No", "years_at_current_employer": 5,
    "annual_income": 500000, "dependents": 2,
    "cibil_score": None, "loan_amount": 500000,
    "loan_term": 12, "loan_purpose": "personal",
    "residential_assets_value": 1000000, "commercial_assets_value": 0,
    "luxury_assets_value": 0, "bank_asset_value": 500000
}

db_path = get_db_path()
conn = sqlite3.connect(db_path)
before = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
print(f"Audit rows before: {before}\n")

results = {}
for name, payload in cases.items():
    print(f"=== {name} ===")
    try:
        out = execute_orchestrator(payload.copy())
        if out.get('status') == 'error':
            print(f"  ERROR: {out.get('error', {}).get('code')}: {out.get('error', {}).get('message')}")
        else:
            read = out.get('readiness', {})
            elig = out.get('eligibility', {})
            tier = out.get('risk_tier', {})
            if read:
                print(f"  band={read.get('band')}  score={read.get('score')}")
                print(f"  components: financial_health={read['components'].get('financial_health', {}).get('score')}, "
                      f"housing={read['components'].get('housing_stability', {}).get('score')}, "
                      f"infra={read['components'].get('infrastructure_access', {}).get('score')}, "
                      f"burden={read['components'].get('household_burden', {}).get('score')}, "
                      f"business={read['components'].get('business_viability', {}) .get('score')}")
                imputed = read.get('imputed_fields') or read.get('components', {}).get('financial_health', {}).get('factors', {})
                if isinstance(imputed, dict):
                    li = imputed.get('loan_income_ratio')
                    if li is None:
                        print(f"  imputed: loan_income_ratio=NULL (income missing)")
            else:
                print(f"  verdict={elig.get('verdict')}  prob={elig.get('probability')}  tier={tier.get('risk_tier')}")
                contribs = elig.get('feature_contributions', {})
                if contribs:
                    top = sorted(contribs.items(), key=lambda x: -abs(x[1]))[:3]
                    print(f"  top-3 contribs: {top}")
            flags = out.get('policy_override_flags', [])
            if flags:
                print(f"  overrides: {flags}")
            recs = out.get('recommendations', {})
            if recs:
                s = recs.get('strengths', [])
                w = recs.get('risk_factors') or recs.get('improvement_areas', [])
                r = recs.get('recommendations', [])
                a = recs.get('action_plan') or recs.get('next_steps', [])
                if s: print(f"  strengths: {s[:2]}")
                if w: print(f"  weak: {w[:2]}")
                if r: print(f"  recs: {r[:2]}")
                if a: print(f"  actions: {a[:2]}")
        results[name] = out
    except Exception as e:
        print(f"  EXCEPTION: {type(e).__name__}: {e}")
        results[name] = {"exception": f"{type(e).__name__}: {e}"}
    print()

after = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
print(f"Audit rows after:  {after}")
print(f"Net new audit rows: {after - before}")
conn.close()
