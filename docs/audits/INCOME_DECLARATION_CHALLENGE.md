# Income Declaration Challenge (Red Team Audit)
**Date:** 2026-06-11
**Auditor:** Hostile Red Team, Fraud Investigator, Operations Manager

---

## 1. The Contradiction of Self-Declared Income
The core principle we have established is: *"Do not ask for data that incentivizes lying and cannot be trusted."* 
We applied this to Dependents and Informal Debt. Does it apply to Income?

*   **Is it trustworthy?** Absolutely not. Income is the most systematically falsified data point in all of retail lending.
*   **The Fraud Loop:** If users know higher income increases eligibility, they will inflate it. Even if we hide the optimized offer until after verification, borrowers will eventually learn that declaring "₹50,000" gets them past the initial rejection gate, while declaring "₹10,000" gets them an instant rejection.
*   **The Dilemma:** "Why ask for a number we refuse to trust?"

## 2. Why We Cannot Simply Remove It (The Cost Reality)
If we completely remove the Income question, we rely 100% on the Verification step (Account Aggregator or Field Officer) to discover the borrower's capacity.
*   **The Problem:** Account Aggregator API pulls cost money (~₹5). Field Officer visits cost significant money and time (~₹200+). 
*   If a borrower only earns ₹3,000 a month but requests a ₹1,00,000 loan, it is mathematically impossible to approve them. If we don't ask for their income upfront, we will waste ₹200 sending a Field Officer to a hopeless application. 
*   **Conclusion:** We must ask for income purely as a **Triage Cost-Gate**, to filter out mathematically impossible applications before incurring verification costs.

## 3. The Resolution: Modify to "Income Bracket"

We must **MODIFY** the Income question. We should no longer ask for an exact numeric value.

1.  **Exact numbers create false precision and anxiety.** Gig workers and farmers do not know their exact monthly average.
2.  **Exact numbers create a "Fraud Mismatch" trap.** If a borrower honestly guesses ₹25,000, and the AA pull shows ₹22,000, legacy banking systems might flag this as "Fraud/Data Mismatch" and reject them. This punishes honest mistakes.

**The Update:** Change the Income question to a simple **Broad Range Dropdown** (e.g., `< ₹15k`, `₹15k - ₹30k`, `₹30k - ₹50k`, `> ₹50k`). 

## 4. Impact Summary

### 1. Impact on Intake Flow
Friction decreases. The user no longer has to calculate their exact monthly average and type it into a box. They simply select a broad bracket that feels right. 

### 2. Impact on Optimization Timing
Zero impact. Optimization remains strictly **Post-Verification**. The declared bracket is *never* fed into the Optimization Engine to calculate the actual loan amount. It is only used to see if the application passes the Triage Cost-Gate.

### 3. Impact on Fraud Resistance
Borrowers can still lie and select a higher bracket to pass triage. However, because the Optimization Engine is strictly bound to the *verified* data, the lie gains them nothing. If they select `> ₹50k` but the Field Officer verifies `₹15k`, the Optimization Engine runs math on `₹15k` and generates a safe counter-offer. The "Fraud Mismatch" trap for honest mistakes is completely eliminated by the use of broad brackets.

### 4. Is "Pending Verification" the correct default state?
**Yes. Emphatically.** The moment a borrower completes the 7-question triage, the system checks CIBIL and the Income Bracket. If they pass the baseline floor, they are instantly placed in **Pending Verification**. The system generates zero loan amount promises until the AA pull or Field Visit is complete.

---

## 5. Architecture Recommendation
**MODIFY.** I will update `PERSON_A_REQUIREMENTS_v2.md` to change the Income field from "Adaptive UI Exact Entry" to "Broad Bracket Selection", ensuring the system never demands a precise number it intends to verify anyway.
