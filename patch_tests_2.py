import os
files_to_check = [
    'backend/tests/test_e2e_person_a.py',
    'backend/tests/test_e2e_person_b.py',
    'backend/tests/test_integration_high_value.py',
    'backend/tests/test_orchestrator.py'
]
for f in files_to_check:
    with open(f, 'r') as file:
        content = file.read()
    content = content.replace('"recommendations"', '"explanation"')
    content = content.replace("'recommendations'", "'explanation'")
    content = content.replace('test_person_a_recommendations_keys', 'test_person_a_explanation_keys')
    content = content.replace('test_person_b_recommendations_keys', 'test_person_b_explanation_keys')
    with open(f, 'w') as file:
        file.write(content)
print("done")
