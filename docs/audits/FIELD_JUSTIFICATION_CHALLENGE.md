# Field Justification Challenge (Hostile Audit)
**Date:** 2026-06-11
**Auditor:** Independent Architecture Review Board, Compliance Office

---

## 1. Special Challenge: Marital Status (The Bias Trap)
**The Attack:** A previous assumption stated that Marital Status correlates with Livelihood Resilience. While statistically true at a macro level (spouses often provide dual-income stability), using it for underwriting is a massive regulatory failure. 
*   **Observable Evidence?** No. Being married does not mathematically guarantee cash flow.
*   **Fair Lending Risk?** **Extreme.** Discriminating against single mothers, divorcees, or widows is a direct violation of ECOA (Equal Credit Opportunity Act) and global fair-lending standards.
*   **Alternative:** The `Sole Earner` status question perfectly captures the exact economic data we actually need (household financial resilience) without capturing the biased demographic data.
*   **Verdict:** **BANNED.** Marital status is permanently banned from RiskIntel scoring and intake.

## 2. Special Challenge: Housing Status (The Math Reality)
**The Attack:** Do we really need to add friction by asking about rent? Can't we just scrape it from the Account Aggregator later?
*   **The Reality:** For banked users, yes, we can scrape it. But RiskIntel explicitly targets unbanked, cash-only farmers and gig workers (Person B). They do not have Account Aggregators.
*   **Optimization Impact:** Rent is a mandatory fixed obligation (equivalent to an EMI). If we skip this question, the Optimization Engine calculates an Affordability Index that assumes zero housing costs. It will hallucinate a high "Nearly Ready" loan amount. When the manual Field Officer later discovers the borrower pays ₹8,000 in rent, the loan crashes, making the Optimization Engine look stupid and deceitful. 
*   **Verdict:** **KEEP.** It is mathematically required *before* the Optimization Engine runs.

---

## 3. Field-by-Field Ruthless Elimination

| Field | Verdict | Reason |
| :--- | :--- | :--- |
| **1. Loan Amount** | Keep | Without it, there is no mathematical constraint to optimize against. |
| **2. Loan Purpose** | Keep | Without it, the "Utility-Aware" logic fails (engine might reduce a loan for a fixed asset, creating useless coaching). |
| **3. Pincode** | Keep | Unlocks rural vs urban cost-of-living deduction for NTC borrowers. Without it, NTC Affordability fails. |
| **4. Primary Livelihood** | Keep | Sets the behavioral verification path (Farmer vs Salaried). |
| **5. Income** | Keep | Foundational metric for Affordability Index calculation. |
| **6. PAN** | Keep | The ultimate gateway. Without it, we cannot route Person A (Bureau) vs Person B (Thin-file). |
| **7. Housing Status / Rent**| Keep | Rent is identical to an EMI. Required *before* FOIR math and optimization can run safely. |
| **8. Sole Earner** | Keep | Dictates if adding a co-applicant is a mathematically viable optimization path. |
| **9. Informal Debt** | Keep | (NTC only). Because CIBIL is missing, skipping this hallucinates an empty balance sheet and guarantees default. |
| **10. Time in Livelihood** | **Collect Later** | This sets "Resilience", which is a binary pass/fail score. It does *not* change the Affordability math (Amount/Tenure optimization). Ask it only after presenting the provisional optimized terms to reduce upfront friction. |
| **11. Income Receipt Method**| **Collect Later** | Verification routing (AA vs Field Officer) is only needed *after* the borrower accepts the optimization terms. |
| **12. Local Reference** | **Collect Later** | Purely a field-officer recovery tool. Has absolutely zero impact on mathematical optimization or eligibility. |
| **13. Marital Status** | **Remove** | Banned for fair-lending violations. |

---

## 4. The Final Intake Architectures

### Minimum Viable Intake (8 Questions)
*The absolute smallest flow that provides the Optimization Engine with 100% of the mathematical constraints required to generate a safe, legally-compliant "Nearly Ready" counter-offer.*

1. Loan Amount
2. Loan Purpose
3. Pincode
4. Primary Livelihood
5. Income
6. Sole Earner (Yes/No)
7. Housing Status (Owned/Rented -> If Rented, Amount)
8. PAN
*(If PAN returns Thin-File, dynamically ask Q9: Informal Debt)*

### Recommended Intake (8 Questions + Post-Optimization Verification)
*   **Step 1: The 8-Question Triage** (Runs Optimization Engine).
*   **Step 2: Coaching Reveal** (User sees: "We can approve you for ₹X").
*   **Step 3: Verification Acceptance** (User clicks "Accept Terms" -> System asks `Time in Livelihood` and `Income Receipt Method` to finalize the backend dossier).

### Maximum Safe Intake (10 Questions Upfront)
The exact list defined in the previous challenge. While safe, it front-loads 2-3 questions that have zero impact on the immediate mathematical optimization, unnecessarily increasing the upfront drop-off rate.

---

## 5. Summary

*   **Major Flaws Discovered:** 
    *   Marital status is a critical ECOA fair-lending violation. 
    *   We were front-loading questions (`Time in Livelihood`, `Receipt Method`) that have zero impact on the Optimization Engine's mathematical output. They belong *after* the counter-offer is accepted.
*   **Architecture Changes Required:** We are moving 3 fields to a post-optimization "Acceptance" stage. We are permanently deleting Marital Status.
*   **Final Verdict:** We have successfully reigned in scope creep, reducing the immediate upfront intake funnel to an incredibly tight **8 questions**. This is the mathematically perfect floor.
