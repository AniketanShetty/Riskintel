# RiskIntel — Thin-File Policy

**Date:** 2026-06-07
**Status:** Enforceable Product Policy

## 1. Definition: What counts as a thin-file borrower

A **thin-file borrower** is an applicant who meets any of the following criteria:
- Bureau score is absent (no record or the bureau returned no score).
- Bureau score is `0` or `-1` (the standard sentinels for "no history").
- Bureau score is explicitly self-declared as "new to credit."

## 2. Target State: What the system MUST do

To ensure fairness and transparency, the system must treat the absence of a credit history as an explicit signal requiring a distinct workflow:
- **Explicit Routing:** If a Person A (bureau-scored) application is submitted with a missing, `0`, or `-1` CIBIL score, the system must explicitly route them to a specialized exception flow, or the Person B (thin-file) readiness assessment pipeline, with full logging.
- **Surface the Reroute:** The system must embed the original requested route, the actual executed route, and the reason for the diversion directly in the API response.
- **Fail Gracefully on ML Inputs:** If a borrower falls into out-of-distribution thresholds that cause system failures (e.g., CIBIL values causing unhandled exceptions), the orchestrator must catch the error, log it, and return a clean 500 error requiring manual review.

## 3. Target State: What the system MUST NOT do

- **No Silent Rerouting:** The system must not convert a Person A payload into a Person B payload without explicitly logging the conversion and notifying the caller. 
- **No Approval Probabilities:** The system must not generate, estimate, or return a credit approval probability for thin-file borrowers (Person B).
- **No E3 Archetypes:** The E3 Borrower Archetype KMeans clustering model must never be executed or returned for a thin-file borrower.
- **No E1 Execution:** The E1 Eligibility model (which requires bureau data) must never evaluate a thin-file applicant.

## 4. Allowed Engines on the Thin-File Path

Only the following decision-support components are authorized for evaluating thin-file borrowers:
- **E5 (Readiness Engine):** Mandatory. Rule-based, auditable, deterministic scoring of housing, infrastructure, financial health, household burden, and business viability.
- **E6 (Livelihood Engine):** Mandatory. Deterministic string lookup of business type, enforcing an explicit `is_unclassified` flag for unknown businesses.

## 5. Exposure of the Routing Decision

The routing decision must be explicit in the backend payload and audit trail:
- **For the Employee:** The API response payload must contain a dedicated `routing_decision` object. Example:
  ```json
  "routing_decision": {
    "original_user_type": "person_a",
    "routed_to": "person_b",
    "reason": "cibil_absent_or_sentinel"
  }
  ```
- **For the Borrower:** The response must contain a clear, plain-language text string explicitly stating that the assessment is a readiness heuristic, not a traditional credit score outcome.

## 6. Audit Log Requirements

Every assessment attempt by a thin-file borrower must be written to the `audit_log` with the following mandatory fields:
- `correlation_id` and `timestamp`.
- `user_type_original` and `routing_decision`.
- `engine_statuses` (capturing whether E5 and E6 completed successfully).
- Any `policy_override_flags` (e.g., E5 financial health floor breach).
- Any caught exceptions (if the assessment failed, it must not disappear from the log).

## 7. Borrower-Facing Message

If a thin-file borrower is routed to the readiness assessment, they must receive the following explicit message in the response payload:
> "You do not have a credit bureau history in our system. We will assess your application using a different process that looks at your income, expenses, business, and household factors — not at a credit score. The result is a readiness assessment, not an approval decision. A loan officer will review your application."

If a thin-file borrower cannot be assessed via the readiness engine and is rejected outright, they must receive a `THIN_FILE_NOT_SUPPORTED` error envelope with clear instructions.

## 8. Fallback and Manual-Review Path

If a borrower triggers an unhandled exception or falls out-of-distribution:
1. The orchestrator catches the error.
2. The orchestrator returns a `THIN_FILE_NOT_SUPPORTED` or a generic 500 error envelope indicating the automated system cannot process the application.
3. The response includes a fallback directive for **Manual Review by Loan Officer**.
4. The borrower is not automatically rejected; the system explicitly defers the decision to a human underwriter.

---
## Note on Current Audited Reality vs. Target State
**Current Reality (V1.0):** Today, `routing.py` silently reroutes CIBIL=0/-1 from Person A to Person B without notifying the caller. The audit log fails to capture assessments that raise exceptions, rendering thin-file failures invisible to compliance. 

**Target Enforcement:** The above policy mandates the removal of silent rerouting and enforces complete audit logging as an immediate prerequisite to any further production deployment.
