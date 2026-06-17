import os
import json
import time
import hmac
import hashlib
import requests
from typing import Dict, Any

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("RISKINTEL_API_KEY", "compose-demo-api-key")
WEBHOOK_SECRET = os.getenv("RISKINTEL_WEBHOOK_SECRET", "compose-demo-webhook-secret")

# Presentation Helpers
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_step(title: str, response: requests.Response = None):
    print(f"\n{Colors.BLUE}{Colors.BOLD}-> {title}{Colors.ENDC}")
    if response is not None:
        if response.status_code >= 400:
            print(f"{Colors.FAIL}Error {response.status_code}: {response.text}{Colors.ENDC}")
            exit(1)
        data = response.json()
        print(f"  {Colors.GREEN}Success (200){Colors.ENDC}")
        print(f"  Current State: {Colors.BOLD}{data.get('current_state', 'UNKNOWN')}{Colors.ENDC}")

def print_explanation(session_id: str):
    print(f"\n{Colors.WARNING}Fetching Decision Explanation...{Colors.ENDC}")
    headers = {"X-API-Key": API_KEY}
    response = requests.get(f"{API_URL}/applications/{session_id}", headers=headers)
    if response.status_code == 200:
        exp = response.json().get("explanation", {})
        print(json.dumps(exp, indent=2))
    else:
        print(f"{Colors.FAIL}Failed to fetch explanation.{Colors.ENDC}")

# HTTP Wrappers
def api_post(endpoint: str, payload: Dict[str, Any]) -> requests.Response:
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    return requests.post(f"{API_URL}{endpoint}", json=payload, headers=headers)

def webhook_post(endpoint: str, payload: Dict[str, Any]) -> requests.Response:
    body = json.dumps(payload, separators=(',', ':')).encode()
    timestamp = str(int(time.time()))
    signed_payload = timestamp.encode() + b"." + body
    signature = "sha256=" + hmac.new(WEBHOOK_SECRET.encode(), signed_payload, hashlib.sha256).hexdigest()
    
    headers = {
        "X-Timestamp": timestamp,
        "X-Hub-Signature-256": signature,
        "Content-Type": "application/json"
    }
    return requests.post(f"{API_URL}{endpoint}", data=body, headers=headers)

# ---------------------------------------------------------
# SCENARIOS
# ---------------------------------------------------------

def scenario_ready_salaried():
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== SCENARIO 1: SALARIED (READY) ==={Colors.ENDC}")
    print("Applicant wants 50,000. Verified capacity easily supports it.")
    
    res = api_post("/apply", {
        "loan_amount": 50000,
        "loan_term": 12,
        "loan_purpose": "home_repair",
        "income_bracket": "40k-50k",
        "full_name": "Alice Salaried",
        "national_id": "ABC12345",
        "pincode": "110001"
    })
    print_step("Intake Application", res)
    session_id = res.json()["session_id"]
    
    res = api_post(f"/applications/{session_id}/triage", {"bureau_status": "PRIME"})
    print_step("Bureau Triage", res)
    
    res = webhook_post("/webhooks/aa", {
        "session_id": session_id,
        "status": "SUCCESS",
        "verified_income": 5000
    })
    print_step("Account Aggregator Webhook (Verified: 45k)", res)
    
    res = api_post(f"/applications/{session_id}/optimize", {"annual_rate": 0.18})
    print_step("Optimization Engine Run", res)
    
    print_explanation(session_id)

def scenario_nearly_ready_gig():
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== SCENARIO 2: GIG WORKER (NEARLY_READY) ==={Colors.ENDC}")
    print("Applicant wants 100,000. Verified capacity too low for 12 months. Engine must stretch tenure.")
    
    res = api_post("/apply", {
        "loan_amount": 100000,
        "loan_term": 12,
        "loan_purpose": "working_capital",
        "income_bracket": "20k-30k",
        "full_name": "Bob Gigworker",
        "national_id": "XYZ98765",
        "pincode": "110001"
    })
    print_step("Intake Application", res)
    session_id = res.json()["session_id"]
    
    res = api_post(f"/applications/{session_id}/triage", {"bureau_status": "PRIME"})
    print_step("Bureau Triage", res)
    
    res = webhook_post("/webhooks/aa", {
        "session_id": session_id,
        "status": "SUCCESS",
        "verified_income": 5000
    })
    print_step("Account Aggregator Webhook (Verified: 25k)", res)
    
    res = api_post(f"/applications/{session_id}/optimize", {"annual_rate": 0.18})
    print_step("Optimization Engine Run", res)
    
    print_explanation(session_id)

def scenario_coapplicant_recovery():
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== SCENARIO 3: CO-APPLICANT RECOVERY LOOP ==={Colors.ENDC}")
    print("Applicant hits MATH_WALL. Adds co-applicant to combine income. Engine re-runs and Approves.")
    
    res = api_post("/apply", {
        "loan_amount": 100000,
        "loan_term": 12,
        "loan_purpose": "medical",
        "income_bracket": "10k-20k",
        "full_name": "Charlie Solo",
        "national_id": "DEF12345",
        "pincode": "110001"
    })
    print_step("Intake Application", res)
    session_id = res.json()["session_id"]
    
    res = api_post(f"/applications/{session_id}/triage", {"bureau_status": "PRIME"})
    print_step("Bureau Triage", res)
    
    res = webhook_post("/webhooks/aa", {
        "session_id": session_id,
        "status": "SUCCESS",
        "verified_income": 2000
    })
    print_step("Account Aggregator Webhook (Verified: 20k)", res)
    
    res = api_post(f"/applications/{session_id}/optimize", {"annual_rate": 0.18})
    print_step("Optimization Engine Run (MATH WALL HIT)", res)
    
    print_explanation(session_id)
    
    print(f"\n{Colors.WARNING}Borrower submits Co-Applicant...{Colors.ENDC}")
    res = api_post(f"/decision/{session_id}/coapplicant", {
        "full_name": "Dana Coapplicant",
        "national_id": "WXY45678",
        "pincode": "110001"
    })
    print_step("Co-Applicant Submission", res)
    
    res = webhook_post("/webhooks/aa", {
        "session_id": session_id,
        "status": "SUCCESS",
        "verified_income": 10000
    })
    print_step("Account Aggregator Webhook (Combined Verified: 10000)", res)
    
    res = api_post(f"/applications/{session_id}/optimize", {"annual_rate": 0.18})
    print_step("Optimization Engine Re-Run", res)
    
    print_explanation(session_id)

if __name__ == "__main__":
    try:
        scenario_ready_salaried()
        scenario_nearly_ready_gig()
        scenario_coapplicant_recovery()
        print(f"\n{Colors.GREEN}{Colors.BOLD}Demo Execution Complete.{Colors.ENDC}\n")
    except requests.exceptions.ConnectionError:
        print(f"{Colors.FAIL}Error: Could not connect to API at {API_URL}. Is the server running?{Colors.ENDC}")
