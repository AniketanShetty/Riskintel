# Informal Debt Challenge (Red Team Audit)
**Date:** 2026-06-11
**Auditor:** Fraud Investigator, Senior Credit Risk Officer

---

## 1. The Contradiction
The challenge: *"Why is self-reported informal debt acceptable if self-reported dependents were rejected as unreliable?"*

**The brutal truth: It isn't.** 

You have correctly identified a massive architectural hypocrisy. The logic we used to ban the "Dependents" question applies 100% to the "Informal Debt" question.

### Attack 1: The Identical Fraud Trap
Just like with dependents, microfinance borrowers understand that declaring high existing debt will destroy their Affordability Index and guarantee a rejection. 
*   **The Reality:** If asked on a digital form, the vast majority of borrowers will simply declare "₹0" informal debt, regardless of whether they owe ₹50,000 to a local moneylender. 
*   **Adverse Selection:** Honest borrowers who declare their debt will be rejected. Dishonest borrowers will be approved, leading to guaranteed defaults.

### Attack 2: The Hallucination of Precision
If the Optimization Engine incorporates a self-reported "₹0" informal debt into its Fixed Obligation to Income Ratio (FOIR), it calculates a mathematically "perfect" but entirely fictional maximum safe loan amount. We are lying to ourselves about the risk.

---

## 2. The Required Architecture Update

We cannot ask a question that actively incentivizes fraud and provides zero verifiable upfront truth. The "Informal Debt" question must be **KILLED** from the digital intake funnel.

### How do we protect against hidden leverage without asking?

**1. Banked NTC Borrowers (The Data Approach):**
For borrowers with no CIBIL but who have an active bank account/UPI, we use Account Aggregator (AA) data. We don't ask them if they have debt; the system scans their AA data for recurring, fixed-amount, un-tagged outbound transfers. If they send exactly ₹2,000 to the same person on the 5th of every month, the algorithm flags it as an "Implied Informal Obligation" and automatically adds it to their FOIR.

**2. Unbanked NTC Borrowers (The Physical Approach):**
For borrowers with zero digital footprint, we rely entirely on the previously established **"Verification Freeze"** protocol. 
*   Because they are 100% cash, the Optimization Engine is already blocked from making a final offer. 
*   The application routes to a Field Officer.
*   **The Field Officer** uses the "Local Reference" provided during intake to conduct physical/social underwriting to uncover hidden debts before un-freezing the application.

---

## 3. Executive Summary

**Verdict:** The Informal Debt question is a classic Model Risk Management failure. It is an unverified, easily falsified input that corrupts the Affordability math. 

I will immediately remove this from the intake funnel. By doing so, the absolute Minimum Viable Intake is reduced to an airtight **7 questions.**
