# Component Score Architecture Challenge
**Date:** 2026-06-11
**Auditor:** Independent Architecture Review Board

---

## 1. Architecture A: The "5 C's of Credit" (The Banking Classic)

**Components:**
1. Character (Credit History / Repayment behavior)
2. Capacity (Income vs Proposed EMI)
3. Capital (Savings / Down payment - rarely applicable in microfinance)
4. Collateral (Assets securing the loan)
5. Conditions (Loan purpose, macro-economic environment)

**Evaluation:**
*   **Pros:** The oldest, most battle-tested framework in banking. Universally understood by traditional underwriters.
*   **Cons:** Fundamentally breaks down in unsecured microfinance. Capital and Collateral will almost always score zero. "Character" is a dangerous, subjective word in algorithmic underwriting.
*   **Explainability:** Low. Explaining a low "Conditions" score is difficult for an algorithm.
*   **Borrower usefulness:** Very Low. Borrowers cannot action "Conditions".
*   **Loan officer usefulness:** Medium. Comforting familiarity, but lacks microfinance precision.
*   **Regulatory defensibility:** High. Regulators are deeply comfortable with the 5 C's.
*   **Optimization-engine compatibility:** Poor. You cannot mathematically optimize "Character" or "Conditions" in a simulator.

---

## 2. Architecture B: The Temporal Framework (Past, Present, Future)

**Components:**
1. Historical Trust (CIBIL Score, DPDs, Default History)
2. Current Capability (Income, Current Debt, Proposed EMI - all merged)
3. Structural Resilience (Years at job, Business age, Industry sector)

**Evaluation:**
*   **Pros:** Incredibly simple mental model for the borrower. It tells a chronological story.
*   **Cons:** Overly aggregated. By merging Income and Debt into "Current Capability," it masks the exact cause of failure (e.g., "Do I need to make more money, or pay down my credit card?").
*   **Explainability:** Medium. The concepts are easy, but the underlying math is too dense inside the "Present" bucket.
*   **Borrower usefulness:** Medium.
*   **Loan officer usefulness:** Low. Officers need granularity between debt burdens and income levels.
*   **Regulatory defensibility:** Medium.
*   **Optimization-engine compatibility:** Medium. The engine has to untangle "Current Capability" to figure out which lever to pull.

---

## 3. Architecture C: The Microfinance Coaching Framework

**Components:**
1. Repayment Trust (Bureau score, past defaults)
2. Cash Flow Availability (Take-home income vs proposed EMI)
3. Existing Leverage (Current outstanding debt, FOIR)
4. Income Permanence (Time in job, business vintage, sector stability)
5. Verification Confidence (Bank statement vs Self-declared, KYC strength)

**Evaluation:**
*   **Pros:** Hyper-specific to the microfinance reality. Explicitly separates the two biggest causes of rejection (Not enough cash flow vs Too much existing debt).
*   **Cons:** Jargon-heavy. Requires good UX translation for the borrower.
*   **Explainability:** Perfect. Every score maps to a specific mathematical calculation.
*   **Borrower usefulness:** Perfect. "Your Existing Leverage is too high" is exact and actionable.
*   **Loan officer usefulness:** Perfect. Officers can clearly see if the borrower is safe but simply lacks "Verification Confidence" (an overrideable state).
*   **Regulatory defensibility:** High. Mathematically objective.
*   **Optimization-engine compatibility:** Perfect. The engine can isolate Cash Flow (by tweaking loan amount) without touching Leverage.

---

## 4. Recommendation & Attack

**Recommendation:** I recommend **Architecture C: The Microfinance Coaching Framework**. It is vastly superior to the initial V2 draft because it explicitly renames abstract banking terms (like "Debt") into precise coaching targets ("Existing Leverage"). It also formalizes "Documentation" into "Verification Confidence," which directly maps to Loan Officer override powers.

### Attacking My Own Recommendation

*The Committee's Critique of Architecture C:*

**Attack 1: The "Optimization Engine" Paradox**
You claim Architecture C is "Perfect" for the Optimization Engine because it isolates Cash Flow Availability from Existing Leverage. However, mathematically, FOIR (Fixed Obligation to Income Ratio) calculation *combines* proposed EMI and existing EMI. If a borrower extends their loan tenure (a common Optimization Engine tactic), it lowers the proposed EMI. This improves their Cash Flow Availability. However, it also lowers their total FOIR. Therefore, the Optimization Engine cannot actually isolate these two scores—tweaking tenure dynamically changes both scores simultaneously. Presenting them as independent scores to the borrower is a mathematical illusion that will break the UX when one slider moves two different progress bars.

**Attack 2: Punishing Poverty vs Risk**
"Income Permanence" inherently punishes the gig economy and seasonal farmers. By separating it into its own score, you are hardcoding a systemic penalty against the exact demographic RiskIntel is trying to serve. A gig worker will mathematically never achieve a high Income Permanence score, ensuring they are always categorized as "High Risk," even if their Cash Flow Availability is excellent. This is a severe Disparate Impact violation waiting to happen.

### Final Conclusion after Attack

The attack on the FOIR mathematical entanglement is fatal to Architecture C's UX design. If a user tweaks the loan amount, and *both* Cash Flow and Leverage scores move, the UI feels broken.

**Final Revised Architecture (The "Action-Oriented" Framework):**
We must collapse Cash Flow and Existing Leverage into a single unified score to prevent slider entanglement, and soften the permanence penalty.

1. **Repayment History** (Locked: Past behavior)
2. **Affordability Index** (Mutable: Combines FOIR, DTI, and Proposed EMI into one optimization bar)
3. **Livelihood Stability** (Replaces permanence; scores the *type* of gig/farming rather than just tenure duration, removing the anti-poor penalty)
4. **Verification Strength** (Overrideable by human)

This solves the mathematical entanglement for the Optimization Engine and fixes the regulatory bias against gig workers.
