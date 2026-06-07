import os, re
files = [
    'backend/tests/test_e2e_person_a.py',
    'backend/tests/test_e2e_person_b.py',
    'backend/tests/test_integration_high_value.py',
    'backend/tests/test_orchestrator.py',
    'backend/tests/test_reports.py'
]
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Simple replaces
    content = content.replace('"strengths": []', '"decision_verdict": "Mock", "primary_reason": "Mock", "contributing_factors": []')
    content = content.replace('"strengths": ["Strong CIBIL."]', '"decision_verdict": "Mock", "primary_reason": "Mock", "contributing_factors": []')
    content = content.replace('"strengths": ["Owns home."]', '"decision_verdict": "Mock", "primary_reason": "Mock", "contributing_factors": []')
    content = content.replace('"strengths"', '"decision_verdict"')
    content = content.replace('"risk_factors"', '"primary_reason"')
    content = content.replace('"improvement_areas"', '"primary_reason"')
    content = content.replace('"action_plan"', '"contributing_factors"')
    content = content.replace('"next_steps"', '"contributing_factors"')
    
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)
print("done")
