import sys
import json
import warnings
warnings.filterwarnings('ignore')
from app.orchestrator import execute_orchestrator

with open('../frontend/src/data/mockPersonas.json', 'r') as f:
    personas = json.load(f)

default_a = {
    'user_type': 'person_a',
    'full_name': 'Test A',
    'age': 30,
    'gender': 'M',
    'marital_status': 'Single',
    'education': 'Graduate',
    'self_employed': 'No',
    'years_at_current_employer': 5,
    'annual_income': 300000,
    'dependents': 0,
    'loan_amount': 50000,
    'loan_term': 12,
    'loan_purpose': 'personal',
    'cibil_score': 700,
    'residential_assets_value': 0,
    'commercial_assets_value': 0,
    'luxury_assets_value': 0,
    'bank_asset_value': 0
}

default_b = {
    'user_type': 'person_b',
    'full_name': 'Test B',
    'age': 30,
    'gender': 'M',
    'marital_status': 'Single',
    'education': 'Graduate',
    'dependents': 0,
    'business_type': 'Retail',
    'years_in_business': 2,
    'monthly_income': 40000,
    'monthly_expenses': 20000,
    'loan_amount': 50000,
    'loan_term': 12,
    'loan_purpose': 'business_expansion',
    'cibil_score': 0,
    'residential_assets_value': 0,
    'commercial_assets_value': 0,
    'luxury_assets_value': 0,
    'bank_asset_value': 0,
    'house_area': 100,
    'location_type': 'Urban'
}

print('=== Mismatches Only ===')

for p in personas:
    req = default_a.copy() if p['user_type'] == 'person_a' else default_b.copy()
    req.update(p['applicant'])
    if p['user_type'] == 'person_a' and req.get('cibil_score', 0) <= 0:
        req['cibil_score'] = p['applicant'].get('cibil_score', 0)
    
    if p['routing_decision']['routed_to'] == 'person_b':
        for k, v in default_b.items():
            if k not in req and k != 'user_type':
                req[k] = v

    try:
        res = execute_orchestrator(req)
        
        if res['routing_decision']['routed_to'] != p['routing_decision']['routed_to']:
            print(f"[{p['id']}] Routing mismatch: Expected {p['routing_decision']['routed_to']}, Got {res['routing_decision']['routed_to']}")
            
        if 'eligibility' in p:
            expected_verdict = p['eligibility']['verdict']
            actual_verdict = res['eligibility']['verdict']
            if expected_verdict != actual_verdict:
                print(f"[{p['id']}] Verdict mismatch: Expected {expected_verdict}, Got {actual_verdict}")
        
        if 'readiness' in p:
            expected_band = p['readiness']['band']
            actual_band = res['readiness'].get('band')
            if expected_band != actual_band:
                print(f"[{p['id']}] Band mismatch: Expected {expected_band}, Got {actual_band}")

        actual_reasons = [f['reason'] for f in res['explanation']['contributing_factors']]
        expected_reasons = [f['reason'] for f in p['explanation']['contributing_factors']]
        for er in expected_reasons:
            if er not in actual_reasons:
                print(f"[{p['id']}] Explanation missing expected reason: '{er}'")

    except Exception as e:
        print(f"[{p['id']}] Exception: {e}")
