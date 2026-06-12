# RiskIntel V2: Product Requirements Document (PRD)

## 1. Product Vision
RiskIntel V2 is an implementation-ready, deterministic underwriting engine designed to eliminate manual business rules and subjectivity in lending to thin-file and undocumented borrowers.

## 2. Target Audience
*   **Primary Applicants (Thin-File):** Borrowers assessed via physical field officer visits (Person B pathway).
*   **Primary Applicants (Digital):** Borrowers assessed via Account Aggregator / Bureau (Person A pathway).
*   **Co-Applicants:** Household members brought in to mathematically salvage failed applications via the `NEARLY_READY` recovery loop.

## 3. Product Bounds & Catalog (Source: ADR-024)
The system operates under strict mathematical ceilings and floors:
*   **SYSTEM_MIN_LOAN_AMOUNT:** 1,000 INR
*   **SYSTEM_MAX_LOAN_AMOUNT:** 500,000 INR
*   **SYSTEM_MAX_TENURE:** 60 Months
*   **SYSTEM_BASE_INTEREST_RATE:** 0.24 (24% APR)
*   **SYSTEM_BASE_SUBSISTENCE_LINE:** 2,500 INR

## 4. User Stories & Edge Cases
*   **Cyclic Recovery (ADR-023):** If a user fails the Affordability Index, the system automatically stretches the tenure or reduces the loan amount (if Divisible) and offers a counter-proposal.
*   **Co-Applicant Salvation (ADR-024):** If the user is fundamentally unaffordable, the engine reverse-calculates the exact `required_coapplicant_income_baseline` and prompts the user to add a co-applicant.
*   **Reprompt Loop (ADR-025):** If a physical verification lacks a secondary contact, the system suspends optimization and triggers `PENDING_REPROMPT` instead of outright rejection.

## 5. Non-Functional Requirements
*   **Determinism:** Two identical payloads must mathematically produce the exact same final state.
*   **Immutability:** Categorical inputs (like income brackets) are permanently destroyed and replaced by integer truths during Verification.
*   **Tamper-Evidence:** Physical artifact validity must be cryptographically hashed (SHA-256) and verified before unfreezing Optimization.
