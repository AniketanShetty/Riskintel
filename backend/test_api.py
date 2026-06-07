import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

with open('../frontend/src/data/mockPersonas.json', 'r') as f:
    personas = json.load(f)

for p in personas:
    payload = p['applicant'].copy()
    payload['user_type'] = p['user_type']
    
    resp = client.post('/api/assess', json=payload)
    if resp.status_code != 200:
        print(f"[{p['id']}] API Error {resp.status_code}: {resp.json()}")
    else:
        print(f"[{p['id']}] SUCCESS")
