import os
import re

for root, _, files in os.walk('backend/tests'):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            original_content = content
            
            # 1. Replace dict keys
            content = content.replace('["recommendations"]', '["explanation"]')
            content = content.replace('.get("recommendations"', '.get("explanation"')
            content = content.replace('"recommendations": {', '"explanation": {')
            
            # 2. Map old mock returns to the new ExplanationSchema mock
            # For Person A / Person B mocks:
            mock_pattern_e4 = r'mock_e4\.return_value = \{.*?\}'
            def replace_mock(m):
                return 'mock_e4.return_value = {"decision_verdict": "Likely", "primary_reason": "Mock reason", "contributing_factors": [{"feature": "mock", "value": "mock", "evidence": "mock", "reason": "mock", "improvement_advice": "mock"}], "triggered_rule_ids": ["R1"]}'
            content = re.sub(mock_pattern_e4, replace_mock, content)
            
            # 3. Replace assertions mapping old keys to new keys
            content = re.sub(r'"strengths" in (.*?)\["explanation"\]', r'"decision_verdict" in \1["explanation"]', content)
            content = re.sub(r'"risk_factors" in (.*?)\["explanation"\]', r'"primary_reason" in \1["explanation"]', content)
            content = re.sub(r'"improvement_areas" in (.*?)\["explanation"\]', r'"primary_reason" in \1["explanation"]', content)
            content = re.sub(r'"action_plan" in (.*?)\["explanation"\]', r'"contributing_factors" in \1["explanation"]', content)
            content = re.sub(r'"next_steps" in (.*?)\["explanation"\]', r'"contributing_factors" in \1["explanation"]', content)
            
            # 4. Handle test_integration_high_value.py and test_e2e_person_b_http.py iteration over keys
            # for key in ("strengths", "risk_factors", "recommendations", "action_plan"):
            content = content.replace('("strengths", "risk_factors", "recommendations", "action_plan")', '("decision_verdict", "primary_reason", "contributing_factors")')
            content = content.replace('("strengths", "improvement_areas", "recommendations", "next_steps")', '("decision_verdict", "primary_reason", "contributing_factors")')
            
            # 5. Handle assert len(...) >= 1
            content = re.sub(r'len\((.*?)\["explanation"\]\["strengths"\]\)', r'len(\1["explanation"]["contributing_factors"])', content)
            content = re.sub(r'len\((.*?)\["explanation"\]\["action_plan"\]\)', r'len(\1["explanation"]["contributing_factors"])', content)
            content = re.sub(r'len\((.*?)\["explanation"\]\["next_steps"\]\)', r'len(\1["explanation"]["contributing_factors"])', content)

            if content != original_content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Updated {path}")
