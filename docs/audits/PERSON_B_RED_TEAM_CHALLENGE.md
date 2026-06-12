# Person B Framework: Red Team Challenge
**Date:** 2026-06-11
**Auditor:** Independent Architecture Review Board

---

## 1. Critical Flaws & Attack Analysis

### Attack 1: The Standardized Living Deduction (Fails on Nuance)
*   **The Flaw:** If we assume everyone is a single migrant worker, we over-lend to a father of 6, creating a debt trap. If we assume a family of 6, we under-lend to the single worker, losing business.
*   **The Resolution:** Use the **Pincode (from Triage)** combined with state-level minimum wage or rural/urban poverty indexes. Assume a conservative baseline (e.g., household of 3). It is mathematically safer to under-lend to a single worker than to over-leverage a family. No extra questions required.

### Attack 2: Income Verification Gap (Gaming Risk)
*   **The Flaw:** "Implied Capacity" is meaningless if the "Declared Income" is a lie. NTC borrowers will realize they need a higher income to get approved and inflate the number.
*   **The Resolution (Verification Hierarchy):**
    *   *Tier 1 (100% accepted):* Account Aggregator (Bank data), Platform APIs (Swiggy/Ola payouts), GST records.
    *   *Tier 2 (75% accepted):* Consistent UPI inbound transfers (QR code merchants), Formal SHG ledger history.
    *   *Tier 3 (50% haircut):* Self-declared cash. The engine automatically slashes declared cash income by 50% for capacity calculations *unless* manually overridden by a physical Field Verification.

### Attack 3: Economic Consistency (Anti-Poor Bias Risk)
*   **The Flaw:** Measuring "Continuous Months" actively punishes seasonal farmers, migrant laborers, and women re-entering the workforce. It equates *tenure* with *risk*, which is a white-collar banking bias.
*   **The Resolution:** Replace Consistency with **Livelihood Resilience**. A migrant daily-wage laborer has excellent resilience because their manual labor skill is instantly transportable, even if they change employers weekly. We map the `User Type` (Gig, Farmer, Business) to a predefined Resilience Matrix based on local macro-economics, not continuous tenure.

### Attack 4: Financial Discipline (Naming Fallacy)
*   **The Flaw:** Having a UPI account or a bank account is proof of *Access*, not *Discipline*. An irresponsible borrower can easily open a bank account. 
*   **The Resolution:** Rename to **Formal Traceability**. We are not grading their moral discipline; we are grading our ability to legally track them, collect ACH payments, and recover the loan.

### Attack 5: "Nearly Ready" Boundary (UX Insult)
*   **The Flaw:** If a borrower asks for ₹1,00,000 and the Optimization Engine says "Approved for ₹15,000", calling them "Nearly Ready" is patronizing and mathematically absurd.
*   **The Resolution (Explicit Bounds):** 
    *   *Nearly Ready:* Optimization requires <= 30% reduction in loan amount OR <= 6 months tenure extension.
    *   *Not Ready Yet:* Optimization requires > 30% reduction. The output shifts to: *"We cannot safely grant your requested ₹1 Lakh. However, if you only need ₹15,000, we can approve that immediately."*

### Attack 6: Architecture Divergence (Technical Debt)
*   **The Flaw:** Maintaining one set of logic for Person A and a completely different set for Person B creates two codebases, two scorecards, and a maintenance nightmare.
*   **The Resolution:** A Unified Architecture.

---

## 2. Revised Unified Architecture

We merge Person A and Person B into a single, unified "Action-Oriented Scorecard." The only difference is the *data source*, not the mathematical components.

| Component | Person A (Bureau Data Available) | Person B (NTC / Thin File) |
| :--- | :--- | :--- |
| **1. Repayment Trust** | CIBIL Score & DPD history. | Defaults to "No Negative History" (Neutral pass). |
| **2. Affordability Index** | Uses Bureau-verified FOIR + Bank Income. | Uses (Haircut/Verified Income - Pincode Living Cost) / EMI. |
| **3. Livelihood Resilience**| Derived from employer type / industry. | Derived from primary livelihood type / industry. |
| **4. Traceability** | Bureau proves deep systemic footprint. | Bank Account, UPI usage, or SHG participation. |
| **5. Verification Strength**| Auto-verified via Bureau cross-check. | Requires Account Aggregator, UPI, or Manual Field Visit. |

---

## 3. Final Verdict

**Verdict: The Initial Framework was flawed. The Revised Unified Architecture is APPROVED.**

**Why the Revision Wins:**
1.  **Eliminates Technical Debt:** We no longer have "Person A" and "Person B" scorecards. We have one Unified Scorecard that dynamically falls back to "Person B" logic when the CIBIL API returns a thin file.
2.  **Solves the Income Gaming Risk:** By enforcing the Verification Hierarchy, we mathematically penalize unverified cash claims (50% haircut) without instantly rejecting the borrower.
3.  **Removes Tenure Bias:** Replacing "Tenure" with "Livelihood Resilience" legally protects us from Disparate Impact claims against gig workers and seasonal farmers. 
4.  **Limits Optimization Insults:** Hard-capping the "Nearly Ready" distance to 30% prevents the engine from generating absurd recommendations.
