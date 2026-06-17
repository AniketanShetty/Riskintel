# PHASE2_SPEC CANDIDATE: BUSINESS RULES AND MATHEMATICS

## MATHEMATICAL CONSTANTS

| Constant Name | Value | Source |
| :--- | :--- | :--- |
| `MAX_DTI` | `0.50` (50%) | `SCORECARD_FORMULAS.md` |
| `BASE_RURAL_LINE` | `2500` (INR) | `SCORECARD_FORMULAS.md` (Matches `SYSTEM_BASE_SUBSISTENCE_LINE` in ADR-024) |
| `SYSTEM_BASE_INTEREST_RATE` | `0.24` (24% APR) | Inferred from Context (ADR-024) |
| `SYSTEM_MAX_TENURE` | `60` (months) | Inferred from Context (ADR-024) |
| `SYSTEM_MIN_LOAN_AMOUNT` | `1000` (INR) | Inferred from Context (ADR-024) |
| `SYSTEM_MAX_LOAN_AMOUNT` | `500000` (INR) | Inferred from Context (ADR-024) |

## DERIVED VARIABLES

| Variable | Formula | Source |
| :--- | :--- | :--- |
| `monthly_living_cost` | `BASE_RURAL_LINE * Pincode_Tier_Multiplier` | `SCORECARD_FORMULAS.md` |
| `FCF` (Free Cash Flow) | `verified_income - monthly_living_cost` | `SCORECARD_FORMULAS.md` |
| `available_capacity` | `MIN((verified_income * MAX_DTI) - existing_emi, FCF - existing_emi)` | `SCORECARD_FORMULAS.md` |
| `target_emi` | `PMT(interest_rate, loan_term, loan_amount)` | `SCORECARD_FORMULAS.md` |
| `emi_shortfall` | `target_emi - available_capacity` | `SCORECARD_FORMULAS.md` |
| `co_app_monthly_living_cost`| `BASE_RURAL_LINE * Co_App_Pincode_Tier_Multiplier` | `ADR-021_COAPPLICANT_CONSTITUTION.md` |
| `co_app_fcf` | `co_app_verified_income - co_app_monthly_living_cost` | `ADR-021_COAPPLICANT_CONSTITUTION.md` |
| `co_app_available_capacity` | `MIN((co_app_verified_income * MAX_DTI) - co_app_existing_emi, co_app_fcf - co_app_existing_emi)` | `ADR-021_COAPPLICANT_CONSTITUTION.md` |
| `total_available_capacity` | `primary_available_capacity + co_app_available_capacity` | `ADR-021_COAPPLICANT_CONSTITUTION.md` |

## RULE INVENTORY

### Rule ID: R-01 (Person A Repayment Trust)
* **Source file:** `SCORECARD_FORMULAS.md`
* **Exact formula:** `IF credit_score >= 650 THEN PASS ELSE FAIL`
* **Inputs:** `credit_score`, `active_dpd_days`, `bureau_settled_36m`
* **Outputs:** `PASS`, `FAIL`, or `HARD_REJECT`
* **Constraints:** Thin files (`0` or `-1`) bypass logic to Person B.
* **Failure conditions:** `active_dpd_days > 0` OR `bureau_settled_36m == True` triggers Terminal Fail (`HARD_REJECT`). `credit_score < 650` triggers FAIL (requires Co-Applicant).

### Rule ID: R-02 (Person B Repayment Trust)
* **Source file:** `SCORECARD_FORMULAS.md`
* **Exact formula:** `IF verification_status IN [VERIFIED_CLEAN, VERIFIED_WITH_VARIANCE] THEN PASS ELSE FAIL`
* **Inputs:** `verification_status`
* **Outputs:** `PASS` or `HARD_REJECT`
* **Constraints:** Trust is strictly deferred to field verification.
* **Failure conditions:** `verification_status == FRAUD_DETECTED` triggers Terminal Fail (`HARD_REJECT`).

### Rule ID: R-03 (Livelihood Resilience)
* **Source file:** `SCORECARD_FORMULAS.md`
* **Exact formula:** `IF business_vintage_months >= 24 THEN PASS ELSE FAIL`
* **Inputs:** `business_vintage_months`
* **Outputs:** `PASS` or `HARD_REJECT`
* **Constraints:** None.
* **Failure conditions:** `business_vintage_months < 24` triggers Terminal Fail (`HARD_REJECT`). Missing artifact sets vintage to 0.

### Rule ID: R-04 (Person A Verification Gate)
* **Source file:** `SCORECARD_FORMULAS.md`
* **Exact formula:** `IF national_id_match_score >= 0.85 AND Account_Aggregator_Pull == SUCCESS THEN PASS ELSE FAIL`
* **Inputs:** `national_id_match_score`, AA status
* **Outputs:** `PASS` or `FAIL`
* **Constraints:** Matches fuzzy PAN logic.
* **Failure conditions:** `FAIL` prevents `VERIFIED` state transition.

### Rule ID: R-05 (Co-Applicant Trust)
* **Source file:** `ADR-021_COAPPLICANT_CONSTITUTION.md`
* **Exact formula:** `IF co_applicant_cibil >= 650 AND co_applicant_active_dpd_days == 0 AND co_applicant_bureau_settled_36m == False THEN PASS`
* **Inputs:** Co-Applicant Bureau Data
* **Outputs:** `PASS` or `HARD_REJECT`
* **Constraints:** Co-applicant is evaluated as a fully independent economic unit.
* **Failure conditions:** Breach of any condition leads to instant `NOT_READY_YET`.

### Rule ID: R-06 (Age Constraints)
* **Source file:** `ADR-021_COAPPLICANT_CONSTITUTION.md`
* **Exact formula:** `IF age >= 18 AND age <= 70 THEN PASS`
* **Inputs:** `age` (from KYC)
* **Outputs:** `PASS` or `HARD_REJECT`
* **Constraints:** Applies strictly and independently to both Primary and Co-Applicant.
* **Failure conditions:** Out of bounds triggers instant `NOT_READY_YET`.

## DECISION TABLES (Pathways Reconstruction)

### The READY Pathways (Approval)
Applicant achieves `READY` when all verifications pass and capacity mathematically supports the target EMI.
* `credit_score >= 650 OR -1`, `active_dpd_days == 0`, `bureau_settled_36m == False`, `business_vintage_months >= 24`, `verification_status == CLEAN/VAR` -> AND `available_capacity >= target_emi` (Without Co-Applicant).
* Same trust and vintage gates -> AND `total_available_capacity >= target_emi` (With Co-Applicant).

### The NEARLY_READY Pathways (Recovery Loops)
Applicant drops into `NEARLY_READY` when they have a recoverable shortfall.
* **Requires Co-Applicant Route:** Primary has `available_capacity <= 0` for an `INDIVISIBLE` purpose OR `credit_score < 650` (Trust failure but no active defaults).
* **Reduce Amount Route:** Primary has `0 < available_capacity < target_emi` for a `DIVISIBLE` purpose (Generates amount counter-offer).

### The NOT_READY_YET Pathways (Terminal Failures & Exhaustion)
Applicant enters `NOT_READY_YET` on policy breaches or mathematical exhaustion.
* **Policy Breach (Hard Reject):** `active_dpd_days > 0`, `bureau_settled_36m == True`, `FRAUD_DETECTED`, `business_vintage_months < 24`, Age < 18 or > 70.
* **Mathematical Wall:** `available_capacity <= 0` for an `INDIVISIBLE` asset AND Co-Applicant is already exhausted (`True`) OR Co-Applicant triggers a hard reject themselves. `total_available_capacity <= 0` (household insolvent).

## CO-APPLICANT ALGEBRA (Reverse Baseline Calculation)

To output `required_coapplicant_income_baseline` when a primary applicant is insolvent, the system reverse-engineers the Co-Applicant Available Capacity formula.
Because `co_app_available_capacity` must mathematically equal or exceed the `emi_shortfall`, and:
`co_app_available_capacity = MIN((co_app_income * 0.50), co_app_income - (BASE_RURAL_LINE * Multiplier))` *(Assuming zero existing EMI for the baseline prompt)*

The reverse algebraic formula (derived from ADR-024) is strictly:
`required_coapplicant_income_baseline = MAX( CEIL(emi_shortfall / MAX_DTI), emi_shortfall + (BASE_RURAL_LINE * Primary_Applicant_Pincode_Tier_Multiplier) )`

## MISSING INFORMATION & AMBIGUITIES

1. **PMT Interest Compounding Strategy:** `SCORECARD_FORMULAS.md` references `PMT(interest_rate, loan_term, loan_amount)` but does not mathematically specify if `interest_rate` (`SYSTEM_BASE_INTEREST_RATE` = 24%) is reduced to a monthly rate (`0.24 / 12`) for exact EMI computation. (Inferred to be monthly, but missing explicit formula definition).
2. **Pincode Tier Multipliers:** While ADR-024 states Tier 1 = 1.8, the actual values for Tier 2, Tier 3, etc. are NOT defined in `SCORECARD_FORMULAS.md` or `ADR-021`. (Missing dictionary).
3. **Co-Applicant `existing_emi` Assumption:** The reverse algebra for `required_coapplicant_income_baseline` implicitly assumes the Co-Applicant has `0` existing debt at the time of generating the prompt slider. This is missing an explicit confirmation.
4. **Target Capacity Buffer:** Does `total_available_capacity` need to strictly equal `target_emi` or is there a required buffer margin? (Formulas state `>=`, but industry standard often leaves a margin. Assumed absolute `>=`).

---
**CONFIDENCE SCORE:** 95/100 (High confidence on constraints and gates. 5 point deduction for missing Pincode definitions and exact PMT compounding specification).
