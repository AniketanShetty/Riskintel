# RiskIntel V2 Data Dictionary

This document defines every approved data field in the system, mapped directly to the unified V2 Constitution.

---

## 1. Universal Intake Fields

Collected upfront from all applicants (Person A & Person B).

| Field Name | Type | Allowed Values | Req/Opt | Source | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `full_name` | String | Min 2, Max 100 chars | Required | Intake | Used for identity verification and reporting. |
| `national_id` | String | Valid PAN / Aadhaar | Required | Intake | Unique identifier. Triggers Bureau Gate. |
| `pincode` | String | 6-digit Indian Pincode | Required | Intake | Used to compute `monthly_living_cost`. |
| `loan_amount` | Integer | Min 1000 | Required | Intake | The raw requested capital. |
| `loan_term` | Integer | 12, 36, 60, 84, 120, etc. | Required | Intake | Requested tenure in months. |
| `loan_purpose` | Select | `medical`, `vehicle`, `working_capital`, etc. | Required | Intake | Triggers Utility-Aware Underwriting locks. |
| `income_bracket` | Select | Pre-defined ranges | Required | Intake | Broad income range. Used strictly for Triage math. |


---

## 2. Person A Specific Intake Fields

| Field Name | Type | Allowed Values | Req/Opt | Source | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
*(No Person A specific intake fields exist. Universal fields capture all requirements).*

---

## 3. Person B Specific Intake Fields

| Field Name | Type | Allowed Values | Req/Opt | Source | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
*(No Person B specific intake fields exist. Universal fields capture all requirements).*

---

## 4. Derived & Bureau Fields

| Field Name | Type | Allowed Values | Req/Opt | Source | Pillar Mapping | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `credit_score` | Integer | 300 - 900, 0, -1 | Required | Bureau | Repayment Trust | Primary CIBIL score. |
| `existing_emi` | Integer | Min 0 | Required | Bureau/AA | Affordability | Active monthly debt obligations. |
| `active_dpd_days` | Integer | Min 0 | Required | Bureau | Repayment Trust | Current Days Past Due. If > 0, terminal reject. |
| `account_history_months` | Integer | Min 0 | Required | Account_Aggregator | Livelihood Resilience | Cash-flow vintage for Person A. |
| `monthly_living_cost` | Integer | Min 0 | Required | Derived | Affordability | `Base_Line * Pincode_Tier_Multiplier`. Individual unit. |
| `available_capacity` | Integer | Any | Required | Derived | Affordability | `(Verified_Income * Max_DTI) - Existing_EMI`. |
| `age` | Integer | 18 to 70 | Required | Bureau/KYC | Livelihood Resilience | Regulatory age lock derived from National ID. |

---

## 5. Stage 2 Physical Verification Fields (Person B)

Collected strictly by Field Officer CRM during `PENDING_VERIFICATION` state.

| Field Name | Type | Allowed Values | Req/Opt | Source | Pillar Mapping | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `secondary_contact_number` | String | Valid Indian Phone | Required | Field_Officer | Verification Strength | Fraud/Recovery skip-tracing anchor. |
| `fo_visit_photo_hash` | String | SHA-256 Hash | Required | Field_Officer | Verification Strength | Geotagged photo hash for anti-collusion audit trail. |
| `verified_monthly_cash_income`| Integer| Min 0 | Required | Field_Officer | Affordability | Deterministic cash income overriding intake bracket. |
| `vintage_artifact_type` | Select | `municipal_license`, `rent_agreement`, `ledger_book`, `merchant_qr`, `none` | Required | Field_Officer | Livelihood Resilience | Physical evidence type verifying business age. |
| `vintage_artifact_issue_date`| Date | YYYY-MM-DD | Required | Field_Officer | Livelihood Resilience | Issue date of the artifact. |
| `business_vintage_months` | Integer | Min 0 | Required | Derived | Livelihood Resilience | `Current_Date - vintage_artifact_issue_date`. 0 if artifact is `none`. |
| `verification_status` | Select | `VERIFIED_CLEAN`, `VERIFIED_WITH_VARIANCE`, `FRAUD_DETECTED`, `UNREACHABLE` | Required | Field_Officer | Verification Strength | Final output of field visit. |

---

## 6. Optimization Outputs

| Field Name | Type | Allowed Values | Req/Opt | Source | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `approved_loan_amount` | Integer | Min 1000 | Required | Optimization | Mutated amount (if Divisible). Locked if Indivisible. |
| `approved_tenure` | Integer | Min 12 | Required | Optimization | Mutated tenure to solve Affordability Shortfall. |
| `coapplicant_required` | Boolean | `true`, `false` | Required | Optimization | Triggered if capacity is negative after max tenure stretch. |
| `required_coapplicant_income`| Integer | Min 0 | Optional | Optimization | Exact numeric requirement output for the Co-Applicant. |
