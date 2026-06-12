# Optimization Engine Timing Challenge (Red Team Audit)
**Date:** 2026-06-11
**Auditor:** Hostile Red Team, UX Researcher, Fraud Investigator

---

## 1. The Challenge: Pre-Verification Optimization

Previously, the architecture assumed: `Intake -> Optimization Engine -> Offer Reveal -> Verification`. 

**This sequence is a fatal architectural error.**

### Attack 1: The "Bait-and-Switch" (False Hope)
If a borrower self-declares ₹25,000 in income, and the Optimization Engine instantly generates a slider saying *"Nearly Ready: We can approve you for ₹60,000,"* the borrower feels a massive psychological win.
When the subsequent verification (Account Aggregator or Field Visit) proves the real income is ₹15,000, that offer collapses. The bank revokes the ₹60,000 and drops it to ₹20,000. 
*   **The Result:** RiskIntel goes from being a "Coach" to a "Bait-and-Switch predator." Trust is permanently destroyed.

### Attack 2: The Fraud-Training Loop
We previously noted that allowing users to play with the Optimization Engine without verification turns it into a fraud-training loop. If the user inputs ₹15,000 income and sees an offer for ₹20k, they hit "Back," change income to ₹35,000, and see the offer jump to ₹60k. The system literally teaches the user exactly what number they need to fake to get the money they want. 

---

## 2. The Required Sequence Update

The Optimization Engine cannot be allowed to output optimized monetary amounts (Principal, EMI, Tenure) based on unverified declarations.

### The Staged Coaching Architecture

**Stage 1: The Hard-Stop Gate (Pre-Verification)**
The system evaluates the declared intake data and the Bureau (CIBIL) pull.
*   **What we CAN show:** 
    *   Hard Rejects: If they have a 90-DPD (Days Past Due) on CIBIL, they immediately get **Not Ready Yet** with the exact coaching explanation.
    *   Math Fails on Declared Data: If they ask for ₹1 Lakh but declare ₹2,000 income, we don't need to verify it. They get **Not Ready Yet**.
*   **What we CANNOT show:** 
    *   Specific Optimized Loan Amounts or counter-offers.

**Stage 2: The "Pending Verification" State**
If the borrower passes the initial rule-gates based on their self-declared data, the system enters a holding state.
*   **The UI:** *"Your profile looks strong! We just need to verify your income to generate your final personalized offer."*
*   **Action:** The user is pushed into the Account Aggregator flow (for Person A) or the Field Officer queue (for Person B).

**Stage 3: Optimization Reveal (Post-Verification)**
Only *after* the true income, rent, and obligations are locked via AA or Field Officer does the Optimization Engine run.
*   **The UI:** Generates the **Ready** or **Nearly Ready** verdict with the exact, mathematically guaranteed counter-offers (e.g., "Reduce to ₹60k").

---

## 3. Executive Summary & Verdict

*   **Should optimization happen before or after?** AFTER. Always.
*   **What must be hidden?** Any optimized numeric counter-offer (Loan Amount, Tenure adjustments) must be strictly hidden until Verification is complete.
*   **Verdict Impact:** We previously created the "Pending Verification" state solely for rural/cash borrowers. We must now **expand "Pending Verification" to be the universal staging state** for *all* borrowers before the Optimization Engine is allowed to generate a final counter-offer.

**Final Verdict:** The architecture has been successfully pivoted. By moving the Optimization Engine *behind* the Verification wall, we completely eliminate the "False Hope" UX disaster and permanently close the "Fraud-Training" loophole.

**Confidence Score:** 100%.
