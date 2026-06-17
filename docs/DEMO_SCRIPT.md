# Demo Script: RiskIntel V2

This document provides a 10-minute end-to-end interactive script demonstrating the orchestration, state machine transitions, and recovery loops in RiskIntel V2.

## Prerequisites
* Ensure the Docker stack is running (`docker compose up -d`).
* All requests below require the `X-API-Key` header matching your environment variable. Webhook steps require an HMAC signature (a helper utility is typically used to generate these, but the logic remains the same).

---

## 1. Intake and Triage (Happy Path)

**Goal:** Create a new application and pass the initial mathematical triage gate.

**API Call:**
```http
POST /apply
X-API-Key: <YOUR_API_KEY>
X-Idempotency-Key: demo-session-1
Content-Type: application/json

{
  "loan_amount": 20000,
  "loan_term": 12,
  "loan_purpose": "medical",
  "income_bracket": "30k-40k",
  "full_name": "Demo User",
  "national_id": "1234567890",
  "pincode": "110001"
}
```
**Expected State:** The system will respond with `session_id`. Internally, the FSM transitions from `INTAKE` to `TRIAGE`.

**API Call:**
```http
POST /triage
X-API-Key: <YOUR_API_KEY>
Content-Type: application/json

{
  "session_id": "<SESSION_ID>"
}
```
**Expected State:** Because `20000` fits safely inside the triage multipliers for `30k-40k`, the application transitions to `PENDING_VERIFICATION`.

---

## 2. Recovery Loop: Reprompt Demonstration

**Goal:** Simulate a Field Officer submitting a blurry photo, triggering the cyclical FSM recovery loop.

**API Call:**
```http
POST /webhooks/fo
X-Webhook-Timestamp: 1718000000
X-Webhook-Signature: sha256=<HMAC_SIGNATURE>
Content-Type: application/json

{
  "session_id": "<SESSION_ID>",
  "status": "FAILED",
  "failure_reason": "IMAGE_BLURRY",
  "tamper_evidence_pass": true
}
```
**Expected State:** The FSM intercepts the failure and routes the application to `PENDING_REPROMPT`. 

**Recovery Action:** The FO uploads a clean photo.
```http
POST /webhooks/fo
X-Webhook-Timestamp: 1718000100
X-Webhook-Signature: sha256=<HMAC_SIGNATURE>
Content-Type: application/json

{
  "session_id": "<SESSION_ID>",
  "status": "SUCCESS",
  "tamper_evidence_pass": true
}
```
**Expected State:** The state machine unlocks and returns to `PENDING_VERIFICATION`.

---

## 3. Recovery Loop: Counter-Offer (NEARLY_READY)

**Goal:** Push the application through optimization where the requested amount is slightly too high for the verified income, triggering a counter-offer.

*(Assume the Account Aggregator webhook successfully posted verifying a low income constraint).*

**API Call:**
```http
POST /optimize
X-API-Key: <YOUR_API_KEY>
Content-Type: application/json

{
  "session_id": "<SESSION_ID>"
}
```
**Expected State:** The Optimization math engine determines the user cannot afford the 12-month tenure. Instead of rejecting, it algebraically stretches the term to 24 months. The FSM transitions to `NEARLY_READY`.

**User Accepts Counter-Offer:**
```http
POST /decision/<SESSION_ID>/accept
X-API-Key: <YOUR_API_KEY>
```
**Expected State:** The FSM locks the final terms and transitions the applicant to `READY` for disbursement.

---

## 4. Failure Isolation (Dead-Letter Webhooks)

**Goal:** Demonstrate how the system handles rogue or out-of-order network traffic.

**Action:** Attempt to send a webhook for a session that is already in `READY` (or `REJECTED`).

**API Call:**
```http
POST /webhooks/aa
X-Webhook-Timestamp: 1718000200
X-Webhook-Signature: sha256=<HMAC_SIGNATURE>
Content-Type: application/json

{
  "session_id": "<SESSION_ID>",
  "status": "SUCCESS",
  "verified_income": 90000
}
```
**Expected State:** The primary database transaction rolls back, throwing an `InvalidTransitionError` (`HTTP 409`). However, in the background, an isolated autonomous transaction persists the rogue payload into the `dead_letter_webhooks` table for engineering forensic auditing.
