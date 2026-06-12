# RiskIntel V2 Constitution
**Version:** 3.0 (Pre-Implementation Architecture Frozen)
**Date:** 2026-06-11
**Status:** SUPREME SOURCE OF TRUTH

This document is the supreme source of truth for RiskIntel V2. It consolidates all red-team audits and explicitly flags contradictions found in legacy documentation. **Repository reality must override older audits.** No future challenge may modify the architecture without updating this document.

---

## 1. Mission
**"Help borrowers understand whether a loan is safe, useful, and realistically achievable while providing personalized pathways to approval."**
RiskIntel V2 is not a credit scoring system. It is a 100% deterministic, explainable Borrower Coaching System.

---

## 2. Non-Negotiable Principles
1.  **Do not ask for a number you do not trust.** (If a field incentivizes lying and cannot be instantly verified, ban it).
2.  **Optimize for truth, not preservation.** (Any component causing adverse selection must be killed, even if traditional banks use it).
3.  **Hide the backend math.** (No raw probabilities or scores are shown to the borrower. Show outcome and actions first).
4.  **Utility over Math.** (A partial loan is useless for an indivisible asset. Math distance != Business utility).

---

## 3. Fair Lending Constraints
1.  **Marital Status is BANNED.** Any schemas collecting `married` are invalid. `Sole Earner Status` is also banned as it acts as a shadow proxy for household size and marital status.
2.  **Occupation Stereotyping is BANNED.** Resilience is scored purely on observable cash-flow structure (diversification, vintage), not labels (e.g., `Tailor > Driver`).
3.  **Paternalism is BANNED.** The system cannot hard-reject a borrower for an indivisible asset just because it only approves a partial amount. It must offer the partial amount and coach them to use savings or add a co-applicant.
4.  **Direct Dependent Counting is BANNED.** Any schemas collecting `dependents`, `young_dependents`, or `old_dependents` are invalid to prevent cognitive friction and ECOA violations. 

---

## 4. Approved Architecture Decisions
*   **Unified Gateway Scorecard:** Person A (Banked) and Person B (Unbanked/NTC) evaluated through the same core 4-pillar logic.
*   **Utility-Aware Underwriting:** Underwriting mathematically respects `Loan Purpose`. For `[INDIVISIBLE]` assets (e.g., Medical, Vehicle), the `Loan Amount` lever is hard-locked; partial approvals are banned to prevent debt traps. For `[DIVISIBLE]` assets (Working Capital), the amount can slide.
*   **Pincode Cost Formula:** `Monthly_Living_Cost = Base_Subsistence_Line * Pincode_Tier_Multiplier`. (Tier 1 = 1.8, Tier 2 = 1.3, Tier 3/Rural/Unmapped = 1.0). The borrower is evaluated as an individual economic unit; household-level adjustments are banned.
*   **Universal Verification Pipeline:** Fast-Track (unverified optimization with a 50% haircut) is permanently banned. The pipeline is strictly: Intake → Bureau Gate → Triage Pass → Pending Verification → Verification → Optimization → Coaching Verdict.
*   **The "Verification Freeze":** Optimization Engine is strictly blocked from generating counter-offers on unverified data.

---

## 5. Rejected Architecture Decisions
*   **Synthetic ML Eligibility Models:** *[REJECTED]* Black-box ML models are incompatible with coaching.
*   **Pre-Verification Optimization / Fast-Track:** *[REJECTED]* Banned to prevent adverse selection and the fraud-training loop.
*   **"Informal Debt" Intake Question:** *[REJECTED]* A fraud trap. Must be derived via Account Aggregator or Field Officer.
*   **Exact Numeric Income Input (Upfront):** *[REJECTED]* Causes anxiety and errors. Replaced with broad brackets for Triage.
*   **Sole Earner / Household Scale Factor:** *[REJECTED]* A self-reported, unverifiable boolean that acts as a shadow proxy for dependents and marital status. Creates systematic over-approval (large sole-earner families) and under-approval (dual-income couples). Banned per hostile audit.

---

## 6. Optimization Engine Rules
1.  **Mutable Levers (Can Change):** `Loan Amount` (only if Divisible), `Tenure`.
2.  **Immutable Reality (Cannot Change):** `Income`, `Existing Debt`, `CIBIL Score`.
3.  **Targeted Requirement Outputs:** `Co-Applicant` is NOT a mutable lever. The Engine cannot hallucinate exogenous variables. It calculates the exact Affordability Shortfall and outputs a 'Required Co-Applicant Baseline Income' contract, assuming zero existing Co-Applicant debt.

---

## 7. Verification Rules
1.  **Digital Traceability (Person A):** Traced via Account Aggregator and Bureau pull.
2.  **Physical Traceability (Person B):** Traced via Field Officer visit.
3.  **Field Verification Contract:** Verification outputs an exact numeric income which permanently destroys the categorical intake bracket. Probabilities and confidence scores are banned. Mandatory fields returned must include `verified_monthly_cash_income`, `business_vintage_months`, `physical_address_verified`, and a tamper-evident `fo_visit_photo_hash`. The FO must collect a `secondary_contact_number` strictly as a skip-tracing/fraud-anchor, not as a qualitative trust metric. Valid outcomes are `VERIFIED_CLEAN`, `VERIFIED_WITH_VARIANCE`, `FRAUD_DETECTED`, and `UNREACHABLE`.

---

## 8. Intake Rules (The 5-Question Floor)
The upfront funnel is mathematically locked. No fields may be added without a Hostile Audit.
1.  Requested Loan Amount
2.  Loan Purpose
3.  Pincode
4.  Income Bracket (Broad Range)
5.  PAN / Aadhaar (Triggers KYC Age Extraction and Bureau Gate)

*   **The Optimization Isolation Rule:** Intake brackets are used exclusively for the Pre-Verification Triage Pass (using the upper bound with 0% haircut to prevent false negatives). The Optimization Engine is strictly banned from ingesting categorical brackets.
*   **Dynamic Routing:** `Secondary Contact` is explicitly banned from the Universal Intake. It is dynamically collected strictly by the Field Officer during physical verification for skip-tracing, not for character evaluation.

---

## 9. Immutable Constraints (Hard Rejects)
The following conditions bypass the Optimization Engine and trigger an instant `Not Ready Yet`:
1.  **Repayment Trust:** Sub-prime Bureau Hit (Person A) or Field Officer `FRAUD_DETECTED` (Person B). For Person B, Repayment Trust is deferred to the Verification gate rather than granted by default.
2.  **Affordability:** Negative Available Capacity (Existing Debt >= Max DTI * Verified Income) AND Loan Purpose is INDIVISIBLE. If Loan Purpose is DIVISIBLE, negative capacity routes to Optimization Engine to attempt amount reduction.
3.  **Verification Strength:** Refusal of verification options (Account Aggregator failure + Field Visit refusal). `UNREACHABLE` state triggers a 14-day retry window (max 2 attempts) before escalating to hard reject. Missing secondary contact triggers a re-prompt, not a terminal reject.
4.  **Livelihood Resilience:** Regulatory Age Lock (<18 or >Policy Max, derived strictly from KYC National ID Verification) or Banned Loan Purpose.

---

## 10. Coaching Rules (Verdicts)
*   **Pending Verification (Default State):** *"We need to verify your income to generate your final personalized offer."* (Optimization Engine is paused).
*   **Ready (Post-Verification):** Approved on requested terms. Celebration UI.
*   **Nearly Ready (Post-Verification):** Fails requested terms, but Engine found a path. Shows interactive slider UI with guaranteed, non-revocable counter-offer or Co-Applicant requirement.
*   **Not Ready Yet:** Fails immutable constraints. Shows a recovery roadmap explicitly identifying the failing Component Score.

---

## 11. Architecture Modules Mapping
*   **The 4-Pillar Framework** (Repayment Trust, Affordability Index, Livelihood Resilience, Verification Strength) is the supreme UX and Business Logic layer. 
*   **Backend Models** (Readiness Engine, Risk Tier Engine, Eligibility Engine, Livelihood Archetype Engine) are preserved strictly as implementation modules. Their outputs must be 100% deterministic and map explicitly to the 4 Pillars. ML classification is banned. The `Livelihood Archetype Engine` is used strictly for contextual UX/Report generation and Loan Purpose compatibility; it is explicitly banned from altering the Livelihood Resilience math matrix to prevent occupation stereotyping.

---

## 12. Change Log
*   **2026-06-11:** Pre-Implementation Architecture Frozen. Final resolutions implemented: Fast-track banned, Universal flow enforced, Utility-Aware Underwriting locked, Pincode constraints formalized, Co-Applicant redefined as a requirement output.
