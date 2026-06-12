# RiskIntel V2 Scorecard Formulas

**Governance Rule:** 100% Deterministic. No ML. No Probabilities. No Hidden Weights.

---

## 1. Repayment Trust

Evaluates the borrower's historical propensity to honor obligations via a binary gating mechanism.

### 1.1 Person A (Digital Pathway)
*   **Inputs:** `credit_score`, `active_dpd_days`, `bureau_settled_36m`
*   **Rules:**
    *   If `credit_score` == 0 or -1 (Thin File), bypass Person A logic and reroute to Person B (Physical Pathway).
    *   If `credit_score` < 650 -> FAIL (Coaching: "Add a co-applicant with CIBIL ≥ 650").
    *   If `credit_score` >= 650 -> PASS.
*   **Hard Reject Conditions (Terminal Fail):**
    *   `active_dpd_days` > 0 (Currently missing payments).
    *   `bureau_settled_36m` == True (Written off account within 3 years).

### 1.2 Person B (Physical Pathway)
*   **Inputs:** `verification_status`, `secondary_contact_number`, `vintage_artifact_type`
*   **Rules:**
    *   `TRUST_DEFERRED_TO_VERIFICATION`. Trust is not granted by default; it must be earned through the Field Officer verification gate.
    *   If `verification_status` == `VERIFIED_CLEAN` or `VERIFIED_WITH_VARIANCE` -> PASS.
*   **Hard Reject Conditions:**
    *   `verification_status` == `FRAUD_DETECTED`

---

## 2. Affordability Index

Evaluates exact cash-flow capacity to service the requested loan.

### 2.1 Inputs
*   `verified_income` (from AA or Field Officer, not intake bracket).
*   `existing_emi` (from Bureau or AA).
*   `pincode` (to derive cost multiplier).
*   `loan_amount`, `loan_term`

### 2.2 Formula Definitions

**1. Living Cost Baseline:**
`monthly_living_cost` = `BASE_RURAL_LINE` (e.g., ₹2,500) * `Pincode_Tier_Multiplier`
The borrower is evaluated as an individual economic unit. `household_scale_factor` is banned.

**2. Free Cash Flow (FCF):**
`FCF` = `verified_income` - `monthly_living_cost`

**3. Maximum Allowed DTI (Debt-To-Income):**
Hardcoded regulatory cap: `MAX_DTI` = 0.50 (50%)

**4. Available Capacity (The Ceiling):**
`available_capacity` = MIN((`verified_income` * `MAX_DTI`) - `existing_emi`, `FCF` - `existing_emi`)

**5. Target EMI (The Demand):**
`target_emi` = `PMT(interest_rate, loan_term, loan_amount)`

**6. EMI Shortfall:**
`emi_shortfall` = `target_emi` - `available_capacity`

### 2.3 Rules
*   If `emi_shortfall` <= 0: Affordability PASS.
*   If `emi_shortfall` > 0: Send to Optimization Engine.

### 2.4 Hard Reject Conditions
*   `available_capacity` <= 0 AND `loan_purpose` is INDIVISIBLE. (If DIVISIBLE, negative capacity routes to the Optimization Engine to attempt amount reduction).

---

## 3. Livelihood Resilience

Evaluates the stability of the cash-flow source via a pure vintage gate.

### 3.1 Inputs
*   `business_vintage_months` (derived from `vintage_artifact_issue_date` or AA history).

### 3.2 Rules (Binary Gate)
*   **PASS:** `business_vintage_months` >= 24
*   **FAIL:** `business_vintage_months` < 24

### 3.3 Hard Reject Conditions
*   Evaluation results in **FAIL**. (System treats any livelihood with less than 24 months of verifiable history as too fragile to underwrite).

---

## 4. Verification Strength

Acts as the fundamental lock. Optimization math cannot run on unverified Triage estimates.

### 4.1 Inputs
*   `national_id_match_score` (Person A).
*   `verification_status` (Person B).
*   `vintage_artifact_type` (Person B).
*   `secondary_contact_number` (Person B).

### 4.2 Rules
*   **Person A:** `national_id_match_score` >= 0.85 (Fuzzy match of Name to PAN DB) AND Account Aggregator pull succeeds.
*   **Person B:** Field Officer submits `verification_status` == `VERIFIED_CLEAN` or `VERIFIED_WITH_VARIANCE`.

### 4.3 Verification Outcomes & Engine Impact
*   `VERIFIED_CLEAN`: Intake estimates matched reality. Engine unlocks and uses the exact numeric values.
*   `VERIFIED_WITH_VARIANCE`: Reality is lower than Intake Bracket lower-bound. Engine unlocks but MUST use the lower `verified_monthly_cash_income`.
*   `FRAUD_DETECTED`: Terminal Hard Reject. Triggers AML/Fraud logging.
*   `ARTIFACT_MISSING`: The FO could not capture a valid `vintage_artifact_type`. Forces `business_vintage_months` = 0 (Automatically triggering a Livelihood Resilience Failure).
*   `MISSING_SECONDARY_CONTACT`: Triggers a re-prompt to the borrower to provide a valid contact, rather than a terminal reject.
*   `UNREACHABLE`: Triggers a 14-day retry window (max 2 attempts) before escalating to a Hard Reject.
