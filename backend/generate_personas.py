import json
import uuid
import warnings
warnings.filterwarnings('ignore')
from app.orchestrator import execute_orchestrator
from datetime import datetime, timezone

# 1. Person A Approval
p1_req = {
    'user_type': 'person_a', 'full_name': 'Arun Kumar', 'age': 34, 'gender': 'M', 'marital_status': 'Married',
    'education': 'Graduate', 'self_employed': 'No', 'years_at_current_employer': 6,
    'annual_income': 9600000, 'dependents': 2, 'loan_amount': 50000, 'loan_term': 12,
    'loan_purpose': 'home', 'cibil_score': 750,
    'residential_assets_value': 5600000, 'commercial_assets_value': 0,
    'luxury_assets_value': 0, 'bank_asset_value': 3300000
}

# 2. Person A Policy Override
p2_req = p1_req.copy()
p2_req['full_name'] = 'Priya Sharma'
p2_req['cibil_score'] = 650

# 3. Person B Ready
p3_req = {
    'user_type': 'person_b', 'full_name': 'Vikram Singh', 'age': 35, 'gender': 'M', 'marital_status': 'Married',
    'education': 'Graduate', 'dependents': 2, 'young_dependents': 1, 'old_dependents': 0,
    'primary_business': 'Retail', 'secondary_business': 'None',
    'years_in_business': 5, 'annual_income': 800000, 'monthly_expenses': 20000,
    'loan_amount': 50000, 'loan_purpose': 'business_expansion', 'loan_tenure': 12, 'loan_installments': 12,
    'occupants_count': 4, 'home_ownership': 1, 'type_of_house': 'pucca', 'house_area': 1200,
    'sanitary_availability': 1, 'water_availability': 'full', 'social_class': 'OBC',
    'cibil_score': 0
}

# 4. Person B Business Misalignment
p4_req = p3_req.copy()
p4_req['full_name'] = 'Rahul Gupta'
p4_req['loan_purpose'] = 'crop' # Retail + crop = Misaligned

# 5. Person B Financial Health Coaching
p5_req = p3_req.copy()
p5_req['full_name'] = 'Meera Patel'
p5_req['annual_income'] = 0 # Triggers FH Floor Veto

reqs = [
    ('person_a_approved', 'Person A Approval', p1_req),
    ('person_a_override', 'Person A Policy Override', p2_req),
    ('person_b_ready', 'Person B Ready', p3_req),
    ('person_b_misalignment', 'Person B Business Misalignment', p4_req),
    ('person_b_fh_coaching', 'Person B Financial Health Coaching', p5_req),
]

output_personas = []
reports = []

for pid, name, req in reqs:
    res = execute_orchestrator(req)
    
    expected = ''
    actual = ''
    mismatch = False
    
    if pid == 'person_a_approved':
        expected = 'Highly Likely or Likely, no override'
        actual = f"{res['eligibility']['verdict']}, override={res['eligibility']['policy_override_applied']}"
        if res['eligibility']['verdict'] in ['Borderline', 'Unlikely'] or res['eligibility']['policy_override_applied']:
            mismatch = True
    elif pid == 'person_a_override':
        expected = 'Unlikely, override=True'
        actual = f"{res['eligibility']['verdict']}, override={res['eligibility']['policy_override_applied']}"
        if not res['eligibility']['policy_override_applied']:
            mismatch = True
    elif pid == 'person_b_ready':
        expected = 'Ready'
        actual = f"{res['readiness']['band']}"
        if res['readiness']['band'] != 'Ready':
            mismatch = True
    elif pid == 'person_b_misalignment':
        expected = 'Business Misalignment rule fired (purpose_alignment)'
        factors = [f['feature'] for f in res['explanation']['contributing_factors']]
        actual = f"Factors: {factors}"
        if 'business_viability' not in factors:
            mismatch = True
    elif pid == 'person_b_fh_coaching':
        expected = 'Not Ready / Needs Improvement due to Financial Health'
        actual = f"{res['readiness']['band']}"
        factors = [f['feature'] for f in res['explanation']['contributing_factors']]
        if res['readiness']['band'] in ['Ready', 'Moderately Ready'] or 'financial_health' not in factors:
            mismatch = True

    reports.append({
        'Persona': name,
        'Expected Outcome': expected,
        'Actual Outcome': actual,
        'Mismatch': str(mismatch),
        'Severity': 'High' if mismatch else 'None'
    })
    
    p_json = {
        'id': pid,
        'name': name,
        'status': 'success',
        'user_type': req['user_type'],
        'correlation_id': res['correlation_id'],
        'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'routing_decision': res['routing_decision'],
        'applicant': req,
        'archetype': res.get('archetype')
    }
    if req['user_type'] == 'person_a':
        p_json['eligibility'] = res['eligibility']
        p_json['risk_tier'] = res['risk_tier']
    else:
        p_json['readiness'] = res['readiness']
        
    p_json['explanation'] = res['explanation']
    output_personas.append(p_json)

with open('mockPersonas_generated.json', 'w') as f:
    json.dump(output_personas, f, indent=2)

with open('report.json', 'w') as f:
    json.dump(reports, f, indent=2)

print('Done.')
