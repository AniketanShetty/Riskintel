# RiskIntel V2: Business Rules Traceability

*All mathematics and boolean checks must strictly map to these definitions. No other assumptions are allowed.*

## 1. Geographic Capacity Math
*   **Rule:** `Living_Cost = SYSTEM_BASE_SUBSISTENCE_LINE * Pincode_Tier_Multiplier`
*   **Constants:** `SYSTEM_BASE_SUBSISTENCE_LINE` (2500).
*   **Registries:** Pincode Tier CSV Mapping.
*   **Consumer:** Triage Engine & Scorecard Engine.

## 2. Product Pricing Math
*   **Rule:** `Target_EMI = PMT(SYSTEM_BASE_INTEREST_RATE / 12, loan_term, loan_amount)`
*   **Constants:** `SYSTEM_BASE_INTEREST_RATE` (0.24).
*   **Consumer:** Scorecard Engine.

## 3. Triage Engine Math
*   **Rule:** `Triage_Capacity = MIN( (Triage_Income * MAX_DTI) - Bureau_EMI, (Triage_Income - Living_Cost) - Bureau_EMI )`
*   **Constants:** `MAX_DTI` (0.50). `Triage_Income` extracts upper bound of integer bracket.
*   **Consumer:** State Machine (Gates `TRIAGE` to `PENDING_VERIFICATION`).

## 4. Tamper Evidence Security (ADR-025)
*   **Rule:** `tamper_evidence_pass = IF (SHA256(received) == expected_hash) THEN True ELSE False`
*   **Inputs:** `fo_visit_photo_hash`, `vintage_artifact_hash`.
*   **Consumer:** Decision Engine (Hard Stop if False).

## 5. Co-Applicant Normalization (ADR-025)
*   **Rule:** 
    *   If Person A: `national_id_match >= 0.85 AND AA_Pull == SUCCESS`
    *   If Person B: `verification_status IN [VERIFIED_CLEAN, VERIFIED_WITH_VARIANCE]`
*   **Outputs:** `co_app_canonical_verification_pass` (Boolean).
*   **Consumer:** Scorecard Engine (Replacing `co_applicant_verification_status`).

## 6. Co-Applicant Reverse Algebra (ADR-024)
*   **Rule:** `required_coapplicant_income_baseline = MAX( CEIL(emi_shortfall / MAX_DTI), emi_shortfall + (SYSTEM_BASE_SUBSISTENCE_LINE * Primary_Pincode_Multiplier) )`
*   **Consumer:** Optimization Engine (Fills the `NEARLY_READY` coaching payload).

## 7. Business Vintage Normalization (ADR-024)
*   **Rule:** `business_vintage_months = ((Current_Year - Issue_Year) * 12) + (Current_Month - Issue_Month)` (Floored at 0).
*   **Consumer:** Canonical Normalization Layer.

## 8. Divisibility Registry (ADR-024)
*   **Rule:** Medical, Education, Debt Consolidation, Two-Wheeler are strictly `INDIVISIBLE` (Cannot stretch loan amount downwards). Working Capital, Home Repair, Wedding are `DIVISIBLE`.
*   **Consumer:** Decision Engine.
