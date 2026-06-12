# RiskIntel V2 API Contracts

This document defines the OpenAPI-style backend contracts that drive the deterministic RiskIntel V2 architecture. 

---

## 1. `POST /api/v2/intake_submission`

Captures the Universal 5-Question Floor and routes the applicant to either Triage failure or Pending Verification.

### Request Schema
```json
{
  "applicant_profile": {
    "full_name": "string (Min: 2, Max: 100)",
    "national_id": "string (Valid PAN/Aadhaar format)",
    "pincode": "string (6-digit Indian Pincode)"
  },
  "co_applicant_profile": {
    "full_name": "string (Nullable)",
    "national_id": "string (Nullable)",
    "pincode": "string (Nullable)"
  },
  "livelihood": {
    "income_bracket": "string (Enum: 10k-20k, 20k-30k, etc.)"
  },
  "loan_request": {
    "loan_amount": "integer (Min: 1000)",
    "loan_term": "integer (Enum: 12, 36, 60, etc.)",
    "loan_purpose": "string (Enum: medical, working_capital, etc.)"
  }
}
```

### Response Schema
```json
{
  "correlation_id": "uuid",
  "next_state": "string (Enum: PENDING_VERIFICATION, NOT_READY_YET)",
  "triage_result": {
    "triage_pass": "boolean",
    "bureau_gate_status": "string (Enum: PRIME, SUB_PRIME, THIN_FILE)",
    "failure_reason": "string (Nullable. Populated if next_state == NOT_READY_YET)"
  }
}
```

---

## 2. `POST /api/v2/verification_complete`

Accepts the Field Officer CRM payload or Account Aggregator webhook, permanently replacing intake brackets with verified integers.

### Request Schema
```json
{
  "correlation_id": "uuid",
  "verification_source": "string (Enum: FIELD_OFFICER, ACCOUNT_AGGREGATOR)",
  "verification_payload": {
    "verification_status": "string (Enum: VERIFIED_CLEAN, VERIFIED_WITH_VARIANCE, FRAUD_DETECTED, UNREACHABLE)",
    "verified_monthly_cash_income": "integer (Min: 0)",
    "secondary_contact_number": "string (Nullable)",
    "fo_visit_photo_hash": "string (SHA-256)",
    "vintage_artifact": {
      "artifact_type": "string (Enum: municipal_license, rent_agreement, merchant_qr, none)",
      "issue_date": "string (YYYY-MM-DD)",
      "artifact_hash": "string (SHA-256)"
    }
  }
}
```

### Response Schema
```json
{
  "correlation_id": "uuid",
  "next_state": "string (Enum: OPTIMIZATION, NOT_READY_YET)",
  "verification_audit": {
    "timestamp": "iso8601",
    "status": "string (Enum: ACCEPTED, REJECTED)",
    "business_vintage_months_derived": "integer"
  }
}
```

---

## 3. `POST /api/v2/optimization_run`

Executes the deterministic mathematics on verified data to produce the final outcome. Called internally by the backend after `VERIFIED` state is reached.

### Request Schema
*Internal Trigger. No external payload required. Reads directly from the DB State.*
```json
{
  "correlation_id": "uuid"
}
```

### Response Schema
```json
{
  "correlation_id": "uuid",
  "final_state": "string (Enum: READY, NEARLY_READY, NOT_READY_YET)",
  "optimization_output": {
    "approved_loan_amount": "integer",
    "approved_tenure": "integer",
    "coapplicant_required": "boolean",
    "required_coapplicant_income_baseline": "integer (Nullable)"
  },
  "scorecard_metrics": {
    "repayment_trust": "string (Enum: PASS, FAIL)",
    "livelihood_resilience_tier": "integer (1, 2, 3)",
    "available_capacity": "integer",
    "emi_shortfall": "integer"
  },
  "explanation": {
    "decision_verdict": "string",
    "primary_reason": "string",
    "recovery_roadmap": "string (Nullable. Populated if NOT_READY_YET)"
  }
}
```

---

## 4. `POST /api/v2/counter_offer_response`

**Description:** Mathematically resolves the `NEARLY_READY` state when a borrower responds to a stretched tenure or reduced amount counter-offer.

### Request Schema
```json
{
  "correlation_id": "uuid",
  "action": "string (Enum: ACCEPT, REJECT)"
}
```

### Response Schema
```json
{
  "correlation_id": "uuid",
  "final_state": "string (Enum: READY, NOT_READY_YET)",
  "resolution_timestamp": "iso8601"
}
```

---

## Validation & Failure Modes

1.  **400 Bad Request:** Payload violates type schema or enums (e.g., submitting `dependents` when the field is constitutionally banned).
2.  **403 Forbidden:** Attempting to call `POST /api/v2/optimization_run` while the application is in `INTAKE` or `PENDING_VERIFICATION` state (enforces the Verification Freeze).
3.  **422 Unprocessable Entity:** `loan_amount` or `loan_term` violate the absolute product bounds configured in the system.
