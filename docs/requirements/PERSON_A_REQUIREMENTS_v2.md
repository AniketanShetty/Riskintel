# Person A Requirements V2
**Date:** 2026-06-11
**Status:** DRAFT

## Mission
To provide a 100% deterministic, highly explainable underwriting gateway for microfinance and small-ticket borrowers, paired with an Optimization Engine that mathematically guarantees a path to approval whenever structurally possible. We solve the problem of opaque credit rejections by shifting the focus from *predicting default* to *coaching for approval*.

## User Types
1. Salaried
2. Self-employed
3. Student
4. New-to-credit *(Routes to Person B logic)*
5. Homemaker
6. Gig worker
7. Farmer
8. Small business owner

## Intake Questions

### Stage 1: The 7-Question Triage (Pre-Optimization)
1. Requested Loan Amount
2. Loan Purpose (Triggers Utility-Aware logic)
3. Pincode (Unlocks geographic cost-of-living and traceability)
4. Housing Status (Owned vs Rented. If Rented, asks for Monthly Rent to add to FOIR)
5. Primary User Type (Livelihood)
6. Income Bracket (Broad range selection, e.g., <₹15k, ₹15k-30k. Used only for triage, never optimization)
7. Sole Earner Status (Yes/No) (Protects against joint-family fraud and feeds Resilience)
8. PAN / Aadhaar (Triggers Bureau Gate)

### Stage 2: Post-Optimization Verification (Asked only if terms are accepted)
* Time in Livelihood (Feeds Resilience)
* Income Receipt Method (Bank/Cash/Wallet)
* Local Reference (Asked dynamically only if unbanked/no digital footprint)

## Dynamic Questions
Questions dynamically displayed based on the selected User Type to accurately assess Capacity and Stability.

*   **If Salaried:**
    *   Employer type (Government, MNC, Private, Informal)
    *   Monthly in-hand salary
    *   Years at current employer
*   **If Self-Employed / Small Business Owner / Gig Worker:**
    *   Business / Gig platform age
    *   Average monthly gross revenue
    *   Average monthly business expenses
*   **If Farmer:**
    *   Primary crop cycle (Cash crop vs Subsistence)
    *   Estimated annual agricultural income
    *   Non-farm secondary household income
*   **If Student / Homemaker:**
    *   Primary household earner's monthly income
    *   Presence of a formal guarantor

## Component Scores
The V2 Scorecard is decomposed into 5 transparent pillars.

1.  **Capacity Score:** Measures cash-flow availability. Evaluates Income against proposed EMI.
2.  **Stability Score:** Measures income consistency and residential permanence (e.g., years in job, business age).
3.  **Debt Score:** Measures existing leverage. Evaluates FOIR (Fixed Obligation to Income Ratio) and existing outstanding debt limits.
4.  **Credit Score:** Measures historical repayment behavior. Translates raw CIBIL scores and historical DPDs (Days Past Due) into a tier.
5.  **Documentation Score:** Measures the strength of verification. (e.g., Bank-statement verified income scores higher than self-declared income).

## Verdict System
The binary "Approve/Reject" is replaced with a coaching-centric scale.

*   **Pending Verification:** The borrower passes initial self-declared checks, but actual income/rent is not yet verified. The Optimization Engine is strictly **blocked** from generating optimized counter-offers until Verification (AA or Field) is complete.
*   **Ready (Post-Verification):** The borrower's *verified* data passes all constraints on their original terms.
*   **Nearly Ready (Post-Verification):** The borrower's *verified* data fails on their requested terms, BUT the Optimization Engine successfully finds a path to approval.
*   **Not Ready Yet (Pre or Post-Verification):** The borrower fails immutable constraints (e.g., major recent default, extreme over-leverage on declared data) and no mathematical tweak can salvage the application today.

## Optimization Engine

**Which variables may be changed? (Mutable Levers)**
*   `loan_amount` (The engine can simulate reducing the request)
*   `tenure` (The engine can simulate extending the term to lower the EMI)
*   `co_applicant_income` (The engine can suggest adding a co-borrower)

**Which variables are FORBIDDEN to change? (Immutable Reality)**
*   `income` (Telling a user to "make more money" to get approved today encourages application fraud).
*   `existing_emi` (They cannot instantly dissolve existing debt at the moment of application).
*   `cibil_score` (Credit history is locked at the time of pull).

## Coaching Outputs

*   **Pending Verification user gets:** *"Your profile looks strong! We just need to verify your income/business to generate your final personalized offer."* (Routes to AA or Field Officer).
*   **Ready user gets:** Celebration UI. A clear explanation of their approved tier, mapped directly to their verified Component Scores.
*   **Nearly Ready user gets:** Interactive slider UI powered by the Optimization Engine. *"Based on your verified income, we cannot approve ₹1,00,000. However, we can instantly approve ₹75,000."*
*   **Not Ready Yet user gets:** A roadmap. (e.g., "Your Credit Score shows a recent missed payment. We need 6 months of clean history.").

## Loan Officer View

*   **What should the officer see?** The complete application, the 5 Component Scores, the exact rule-grid showing Passes and Fails, and the mathematical paths calculated by the Optimization Engine.
*   **What override powers exist?** Officers can override the **Stability Score** and **Documentation Score** based on manual field verification (e.g., visiting a business). Officers *cannot* override systemic hard-stops on the **Credit Score** (recent defaults) or extreme **Debt Score** breaches (FOIR > 70%).
*   **What explanation is shown?** A deterministic audit log: "Borrower rejected because FOIR was 55% (Limit: 50%). Optimization engine calculated that extending tenure from 12 to 24 months drops FOIR to 48%, triggering a 'Nearly Ready' state."
