# RiskIntel V2 Credit Policy

**Role Author:** Chief Risk Officer & Fintech Product Lead
**Date:** 2026-06-10
**Status:** DRAFT (Thresholds pending Risk Committee approval)

---

## 1. Lending Philosophy
RiskIntel operates on a hybrid decision-making architecture. We leverage advanced Machine Learning (E1) and demographic clustering (E3, E5) to evaluate the nuanced probabilistic risk of applicants. However, probabilistic models are inherently blind to hard regulatory, legal, and biological constraints. 

Our V2 Credit Policy establishes a robust, deterministic guardrail layer that sits strictly *above* the ML models. This layer acts as the final "Conflict Resolution" authority to prevent predatory lending, ensure regulatory compliance, and mitigate extreme adversarial attacks, without corrupting the underlying ML inference.

---

## 2. Person A Credit Policy (Credit-Aware Pipeline)

### A. Loan-to-Income (LTI) Caps
1. **Why banks use it:** To ensure the requested principal translates to an Equated Monthly Installment (EMI) that the borrower can actually afford from their cash flow.
2. **Risks prevented:** Guaranteed default through mathematical unaffordability; adversarial attacks (e.g., $1M loan on $1k income).
3. **Fairness concerns:** Disadvantages younger or lower-income borrowers who may have high earning potential but currently low salaries.
4. **False positive risks:** High rejection rate for asset-rich, income-poor retirees who intend to service the loan via liquid capital.
5. **False negative risks:** Approving borderline cases where the borrower has massive unreported debts outside the CIBIL system.
6. **Industry alternatives:** Debt-to-Income (DTI), which factors in existing EMI obligations rather than just the new requested loan.
7. **Recommended RiskIntel V2 direction:** Implement a hard Orchestrator Override for extreme LTI ratios (e.g., > 6.0x) to block mathematically impossible loans before human review.

### B. Age and Maturity Risk
1. **Why banks use it:** Loans must amortize during a borrower's expected income-generating lifespan.
2. **Risks prevented:** Mortality risk; passing unserviceable debt to an estate or next-of-kin.
3. **Fairness concerns:** Age discrimination laws in certain jurisdictions must be navigated carefully; policies must be actuarially sound.
4. **False positive risks:** Rejecting exceptionally healthy elderly applicants or those with substantial inheritable assets backing the loan.
5. **False negative risks:** None. A hard biological cap is deterministic.
6. **Industry alternatives:** Requiring life insurance assignment or a younger co-applicant/guarantor.
7. **Recommended RiskIntel V2 direction:** Enforce `Maturity Age = age + loan_term`. Hard reject if it exceeds the standard retirement ceiling.

### C. Income Adequacy (Subsistence Floor)
1. **Why banks use it:** Lending to individuals below the poverty line often traps them in a debt spiral.
2. **Risks prevented:** Predatory lending accusations, reputational damage, and massive default rates in impoverished cohorts.
3. **Fairness concerns:** It systematically restricts credit access to the most economically vulnerable populations.
4. **False positive risks:** Rejecting applicants whose documented income is low, but who have substantial undocumented cash income.
5. **False negative risks:** A destitute applicant slipping through due to an unusually high historical CIBIL score.
6. **Industry alternatives:** Micro-grants, subsidized developmental loans.
7. **Recommended RiskIntel V2 direction:** Flag applications for manual review rather than hard rejection, allowing a human underwriter to determine if the loan is developmental or exploitative.

### D. Credit Score Policies (The P4 Problem)
1. **Why banks use it:** Historical behavior is the strongest predictor of future behavior.
2. **Risks prevented:** Habitual defaulters stacking new debt.
3. **Fairness concerns:** Credit bureaus can contain errors or penalize individuals for systematic socioeconomic disadvantages.
4. **False positive risks:** Punishing someone who has entirely rehabilitated their finances but whose score hasn't caught up.
5. **False negative risks:** An applicant passing ML checks because other features (high income) temporarily mask their terrible payment habits.
6. **Industry alternatives:** Alternative data scoring (utility bills, rent).
7. **Recommended RiskIntel V2 direction:** Maintain the existing V1 P4 Override. If Risk Tier == P4, force rejection regardless of ML output.

### E. Asset Considerations
1. **Why banks use it:** Assets represent collateral and secondary fallback routes for loan recovery.
2. **Risks prevented:** Complete loss of principal upon default.
3. **Fairness concerns:** Heavily favors established wealth over upwardly mobile, younger applicants.
4. **False positive risks:** Undervaluing informal or community-shared assets.
5. **False negative risks:** Over-relying on illiquid assets (e.g., rural land) that cannot actually be sold to recover the debt.
6. **Industry alternatives:** Cash-flow-based lending (analyzing bank statements).
7. **Recommended RiskIntel V2 direction:** Treat assets strictly as positive ML features. Do not establish deterministic policies around them unless transitioning to a formal Person C (Asset-Backed) pipeline.

---

## 3. Person B Credit Policy (New-To-Credit Pipeline)

### A. Extreme Debt Requests
1. **Why banks use it:** New-to-credit individuals lack the demonstrated discipline to manage massive leverage.
2. **Risks prevented:** "Lottery ticket" applications where NTC borrowers request impossible sums.
3. **Fairness concerns:** Universal enforcement across all demographics.
4. **False positive risks:** Blocking NTC entrepreneurs requesting legitimately large startup capital.
5. **False negative risks:** Score compression masking the leverage ratio behind a good housing score.
6. **Industry alternatives:** Graduated credit lines (starting small and expanding).
7. **Recommended RiskIntel V2 direction:** Implement an `EXTREME_DEBT_FLOOR` in the E5 engine. If `loan_income_ratio > X`, immediately force `financial_health = 0`.

### B. Financial Health Floors
1. **Why banks use it:** A borrower fundamentally cannot afford a loan if their monthly expenses already consume their income.
2. **Risks prevented:** Algorithmic masking, where excellent secondary metrics (e.g., pucca housing) average out disastrously unstable finances.
3. **Fairness concerns:** Accurately measuring informal expenses is notoriously difficult.
4. **False positive risks:** Penalizing seasonal workers applying during their off-season.
5. **False negative risks:** None.
6. **Industry alternatives:** Analyzing volatile vs fixed expenses.
7. **Recommended RiskIntel V2 direction:** Expand the current V1 floor. If financial health is critically low, cap the maximum final E5 Readiness band to "Needs Improvement".

### C. Business Purpose Alignment
1. **Why banks use it:** Microfinance loans are often subsidized or restricted to specific developmental sectors.
2. **Risks prevented:** Fund diversion (e.g., taking an agricultural loan to buy a personal vehicle).
3. **Fairness concerns:** Borrowers may lack the financial vocabulary to correctly categorize their loan purpose.
4. **False positive risks:** Flagging legitimately diversified entrepreneurs (e.g., a farmer opening a retail stall).
5. **False negative risks:** Minor point deductions failing to halt outright fraud.
6. **Industry alternatives:** Post-disbursement physical audits.
7. **Recommended RiskIntel V2 direction:** Output a `PURPOSE_MISMATCH` flag for manual underwriter review rather than deducting superficial points from the total score.

### D. Household Burden
1. **Why banks use it:** Large numbers of dependents radically restrict disposable income available for EMIs.
2. **Risks prevented:** Overestimating a borrower's repayment capacity.
3. **Fairness concerns:** Penalizes multi-generational households common in rural areas.
4. **False positive risks:** Ignoring the informal economic contributions of older dependents or older children.
5. **False negative risks:** Assuming a single income can support 10 people while servicing a loan.
6. **Industry alternatives:** Household-level income assessment rather than individual.
7. **Recommended RiskIntel V2 direction:** Keep as an E5 sub-component. Do not establish hard overrides, as multi-generational financial dynamics are too complex for rigid binary rules.

---

## 4. Manual Review Framework
Rather than rejecting every borderline applicant, RiskIntel V2 utilizes **Manual Review Triggers**. When an application is flagged (e.g., `FLAG_LOW_INCOME_REVIEW` or `FLAG_PURPOSE_MISMATCH`), the Orchestrator passes a "Hold" or "Review" status to the UI.

**Underwriter Guidelines:**
* **Low Income:** Verify if the loan is developmental (e.g., buying a sewing machine to increase income) or consumption-based (e.g., a wedding). Approve the former, reject the latter.
* **Purpose Mismatch:** Call the applicant to clarify exactly how the funds will be used. Manually update the sector code if it was a data-entry error.

---

## 5. Override Framework
All deterministic policies must be executed in `backend/app/orchestrator.py` during the Conflict Resolution phase.
* The ML models (E1, E3, E5) will calculate their outputs mathematically and immutably.
* The Orchestrator will evaluate the payload against this Credit Policy.
* If a policy is violated, the Orchestrator will overwrite the `final_verdict` and append the corresponding string to the `policy_override_flags` list.
* This guarantees 100% fail-closed audit traceability in `riskintel.db` without corrupting the mathematical ML invariant.

---

## 6. Explainability Requirements
The Recommendation Engine (E4) is legally required to explain rejections clearly to the borrower or loan officer.
* When multiple overrides fire simultaneously, E4 must sort them strictly by legal/banking priority.
* **Priority 1 (Biological/Legal):** Age & Maturity violations.
* **Priority 2 (Credit History):** CIBIL P4 violations.
* **Priority 3 (Affordability):** LTI violations.
* Generic ML negative features (e.g., high dependents) must never overshadow a hard policy rejection in the user interface.

---

## 7. Open Questions
*What thresholds should be utilized for V2?*
1. **MAX_MATURITY_AGE:** (Options: 65, 70, 75)
2. **MAX_LTI:** (Options: 4.5x, 6.0x, 8.0x)
3. **SUBSISTENCE_INCOME_FLOOR:** (Options: 250k INR, 300k INR)
4. **EXTREME_DEBT_RATIO (NTC):** (Options: > 3.0x, > 5.0x)

*(End of Policy Document)*
