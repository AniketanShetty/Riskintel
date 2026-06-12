# ADR-021: Co-Applicant Constitution
**Date:** 2026-06-11
**Status:** APPROVED
**Resolves:** Hostile Audit Cases 16 (Bad Co-Applicant), 44 (Co-Applicant Recursion), 49 (Co-Applicant Age Lock)

---

## 1. Permissibility
A Co-Applicant is **strictly a recovery mechanism, not a default intake option**. The system only permits the addition of a Co-Applicant if the Primary Applicant fails exactly one of the following constraints during the single-applicant flow:
1.  **Trust Failure:** Primary CIBIL < 650 (but > -1, and no active DPD).
2.  **Affordability Shortfall:** `available_capacity` is insufficient to cover the `target_emi` even after maximum tenure stretching.

## 2. Bureau & Trust Requirements
The Co-Applicant is mathematically treated as an independent economic unit for trust verification.
*   **Formula Check:** `co_applicant_cibil >= 650`
*   **Formula Check:** `co_applicant_active_dpd_days == 0`
*   **Formula Check:** `co_applicant_bureau_settled_36m == False`
*   *Note: If the Co-Applicant is Thin File (CIBIL -1), they must pass the Person B physical verification gate (`VERIFIED_CLEAN`).*

## 3. Age Requirements
The Regulatory Age Lock applies independently and strictly to the Co-Applicant.
*   **Formula Check:** `co_applicant_age >= 18 AND co_applicant_age <= 70` (Derived strictly from KYC National ID).

## 4. Affordability Calculations & Existing EMI
To prevent the recursion bug (Case 44), the Co-Applicant's existing debt is isolated and deducted *before* their capacity is exposed to the Optimization Engine.

**1. Co-Applicant Living Cost:**
`co_app_monthly_living_cost = BASE_RURAL_LINE * Co_App_Pincode_Tier_Multiplier`

**2. Co-Applicant Free Cash Flow (FCF):**
`co_app_fcf = co_app_verified_income - co_app_monthly_living_cost`

**3. Co-Applicant Available Capacity:**
`co_app_available_capacity = MIN((co_app_verified_income * MAX_DTI) - co_app_existing_emi, co_app_fcf - co_app_existing_emi)`

## 5. Capacity Aggregation
Capacity is strictly additive. If the Primary Applicant is mathematically insolvent (negative capacity), it bleeds the Co-Applicant's capacity.

**Formula:**
`total_available_capacity = primary_available_capacity + co_app_available_capacity`

## 6. Hard Reject Conditions
The application triggers an instant `NOT_READY_YET` if the Co-Applicant violates any immutable constraints:
1.  `co_applicant_active_dpd_days > 0`
2.  `co_applicant_cibil < 650` (A Co-Applicant cannot have a Co-Applicant).
3.  `co_applicant_age < 18 OR > 70`
4.  `total_available_capacity <= 0` (The combined household is over-leveraged).
5.  `co_applicant_verification_status == FRAUD_DETECTED`

## 7. Optimization Interactions
The Optimization Engine operates entirely downstream of the Capacity Aggregation phase. 
1.  The Engine receives `total_available_capacity`.
2.  If `target_emi > total_available_capacity`, the Engine slides the `Tenure` lever to maximum.
3.  If a shortfall persists:
    *   **If Divisible:** Engine reduces the `Loan Amount` until `target_emi == total_available_capacity`. Outputs `NEARLY_READY`.
    *   **If Indivisible:** Mathematical wall hit. Outputs `NOT_READY_YET`.

## 8. Implementation Consequences
1.  **Dual-Track API:** `POST /api/v2/intake_submission` and `POST /api/v2/verification_complete` must be updated to optionally accept a `co_applicant_profile` payload.
2.  **State Machine Branching:** If a Co-Applicant is added to recover a CIBIL < 650 drop, the State Machine must route the Co-Applicant through the Bureau Gate while freezing the Optimization Engine.
3.  **Recursion Immunity:** By deterministically defining `co_app_available_capacity` as net of `co_app_existing_emi`, the system mathematically proves that adding a Co-Applicant can never inadvertently increase the liability of the Primary Applicant.
