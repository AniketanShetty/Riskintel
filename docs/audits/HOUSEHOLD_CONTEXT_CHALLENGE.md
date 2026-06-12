# Household Context Challenge
**Date:** 2026-06-11
**Auditor:** Senior Credit Risk Officer, Rural Field Officer, Behavioral Economist

---

## 1. The Challenge

While we successfully proved that asking "How many dependents?" is a fraud trap, we prematurely assumed that **all household context** was unnecessary. 

By replacing it with a generic Pincode Cost-of-Living index, we introduced a massive mathematical blindspot: **Housing Status**.

### Attack 1: The Rent Blindspot (Cash Flow Failure)
A standard Pincode index assumes an "average" living cost. However, in urban and semi-urban environments, the difference between a borrower who lives in a self-owned ancestral home and a borrower who rents is catastrophic to the Affordability Index.
*   **Borrower A:** Earns ₹20,000. Owns home. Disposable income = ₹15,000.
*   **Borrower B:** Earns ₹20,000. Pays ₹8,000 rent. Disposable income = ₹7,000.
*   *The Flaw:* If the system doesn't ask about housing context, it treats Borrower A and Borrower B identically. It will massively over-leverage Borrower B, treating their rent as disposable cash. Rent is an inflexible obligation mathematically identical to an EMI.

### Attack 2: The Stability Blindspot (Marital Status)
In microfinance, marital status is one of the strongest statistical predictors of Livelihood Resilience. A married borrower has a built-in household support network (even if the spouse isn't formally employed). A single migrant worker is significantly more vulnerable to sudden cash-flow shocks (illness, injury). By stripping household context, we lose a primary stability indicator.

---

## 2. Fraud Risk Comparison

Why is asking "Housing Status" safer than asking "Dependents"?
*   **Dependents is invisible:** A field officer cannot easily prove that your brother's child *doesn't* live with you.
*   **Housing Status is visible:** If a borrower claims they "Own" their house, but the field officer visits and sees they live in a rented chawl, the lie is instantly exposed. Furthermore, rent can often be verified via Account Aggregator (monthly fixed transfers) or utility bills. Because it is highly verifiable, borrowers are significantly less likely to falsify it.

---

## 3. The Required Architecture Update

We cannot abandon household context entirely. We must replace the subjective "Dependents" question with hard, verifiable structural questions.

**Additions to the Intake Flow:**
1.  **Housing Status:** "Do you live in an owned or rented house?"
    *   *If Rented:* Dynamically ask "What is your monthly rent?" -> This value is instantly added to their Existing Obligations (FOIR calculation) for the Affordability Index.
2.  **Marital Status:** "Are you Married or Single?"
    *   *Why?* Feeds directly into the Livelihood Resilience component.

### Executive Summary

**Verdict:** The previous challenge over-corrected. While counting dependents is a fraud trap, ignoring housing status destroys the mathematical safety of the Affordability Index. 

We must re-introduce Household Context, but pivot from *Demographic Headcounts* to *Structural Financial Obligations*. 

**Confidence Score:** 100%. I will now update the requirements to reflect these additions.
