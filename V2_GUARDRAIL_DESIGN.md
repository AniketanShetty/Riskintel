# V2 Guardrail Design Audit

**Objective:** Design V2 deterministic banking guardrails to remediate adversarial failures in the RiskIntel API.
**Methodology:** Mathematical stress-testing of current ML and Readiness engine constraints against standard retail banking and microfinance realities.

---

## Part 1: Person A Failures (Credit-Aware Pipeline)

### 1. Extreme Loan-to-Income (LTI) Risk
* **Current Behavior:** The E1 Random Forest model evaluates `loan_amount` and `annual_income` probabilistically. A borrower requesting a 50 Million INR loan on a 100,000 INR income can still achieve a "Likely" verdict if their CIBIL score is extremely high (e.g., 850).
* **Why it fails banking reality:** Debt-to-Income (DTI) and Loan-to-Income (LTI) limits are non-negotiable regulatory constraints. An LTI of 500x guarantees default through unmanageable EMIs, regardless of historical credit perfection.
* **Industry Practice:** Hard caps at 4.0x to 6.0x gross annual income.
* **Mathematical Options:** 
  1. Add `LTI = loan_amount / annual_income` feature to ML model.
  2. Implement an orchestrator-level boolean override.
* **Pros/Cons:** Retraining ML on an explicit LTI feature risks model instability. An orchestrator override is perfectly deterministic and transparent.
* **False Positive Risk:** High-net-worth borrowers borrowing against liquid assets rather than income might be flagged.
* **False Negative Risk:** None.
* **Recommended V2 Approach:** `MAX_LTI_OVERRIDE` in `orchestrator.py`. Force `Unlikely` if `loan_amount / max(annual_income, 1) > 6.0`.

### 2. Age + Term Maturity Risk
* **Current Behavior:** The model assesses `age` and `loan_term` independently. A 90-year-old requesting a 20-year mortgage might be approved if their income and credit are stellar.
* **Why it fails banking reality:** Actuarial tables dictate that a loan must amortize during a borrower's expected income-generating lifespan.
* **Industry Practice:** The sum of `age + loan_term` cannot exceed the retirement age limit (typically 65-70 years).
* **Mathematical Options:** `maturity_age = age + loan_term`. 
* **Pros/Cons:** Mathematically simple, but requires exact knowledge of the `loan_term` unit (verified as Years). 
* **False Positive Risk:** Rejects extremely healthy elderly applicants.
* **False Negative Risk:** None.
* **Recommended V2 Approach:** `AGE_TERM_OVERRIDE` in `orchestrator.py`. Force `Unlikely` if `age + loan_term > 70`.

### 3. Low-Income Edge Cases
* **Current Behavior:** ML model processes very low incomes linearly.
* **Why it fails banking reality:** Lending to individuals below the subsistence line (e.g., 300k INR/year in urban India) triggers severe predatory lending alarms.
* **Industry Practice:** Manual underwriter escalation for poverty-line applicants to ensure loans are developmental (grants/micro-equipment) rather than exploitative.
* **Recommended V2 Approach:** `FLAG_LOW_INCOME_REVIEW` in `orchestrator.py`. Does *not* force a rejection, but flags the application for mentor intervention if `annual_income < 300000`.

---

## Part 2: Person B Failures (New-To-Credit Pipeline)

### 1. Readiness Score Compression
* **Current Behavior:** The final E5 score is a weighted linear sum: `0.35*Financial + 0.20*Housing + 0.15*Infrastructure + 0.15*Burden + 0.15*Business`. 
* **Why it fails banking reality:** Linear aggregation allows terrible financial health (e.g., Score: 20) to be "masked" by a perfect house, perfect business, and water access, pulling the final score into the "Moderately Ready" band. A borrower with failing finances is fundamentally not ready, regardless of housing.
* **Industry Practice:** Hard component floors. A critical failing grade in any major pillar limits the overall band.
* **Mathematical Options:** 
  1. Geometric mean instead of arithmetic mean.
  2. Sub-score component gates.
* **Pros/Cons:** Geometric mean is mathematically elegant but impossible to explain to a borrower via E4 rules. Component gates are highly transparent.
* **False Positive Risk:** Penalizes borrowers who are genuinely ready but suffer a temporary anomaly in one specific metric.
* **Recommended V2 Approach:** Expand the E5 Floor Override. Currently, E5 floors to 0 if `financial_health < 0.5`. V2 should cap the maximum `readiness_band` to `Needs Improvement` if `financial_health_score < 40` or `business_viability_score < 40`.

### 2. Extreme Debt Masking
* **Current Behavior:** In `readiness_engine.py`, `debt_burden_ratio_score` drops to 0 if `loan_income_ratio > 1.5`. However, this is averaged against `stability_ratio_score`. Thus, a massive debt request (LTI > 10.0x) only costs the applicant 17.5 total readiness points (50% of the 35% financial weight).
* **Why it fails banking reality:** Debt burdens are binary limits. Asking for 10x your income should completely halt the application.
* **Industry Practice:** Immediate rejection for absurd leverage ratios.
* **False Negative Risk:** The current engine frequently allows adversarial leverage attacks to achieve a passing band.
* **Recommended V2 Approach:** Implement `EXTREME_DEBT_FLOOR` inside `readiness_engine.py`. If `loan_income_ratio > 3.0`, force `financial_health_score = 0.0`. This will automatically trip the existing `FINANCIAL_HEALTH_FLOOR_THRESHOLD` override.

### 3. Loan Purpose Alignment Weaknesses
* **Current Behavior:** If `primary_business_macro` and `loan_purpose_macro` mismatch (e.g., an Agriculture business applying for a Business loan), the engine deducts 15 points from `business_viability_score`. This translates to a mere 2.25 point penalty on the final Readiness score.
* **Why it fails banking reality:** In microfinance, purpose misalignment is the #1 indicator of fund diversion, fraud, or desperate liquidity grabs.
* **Industry Practice:** Hard manual review for sector mismatch to ensure grant/loan funds are utilized for their approved macro-economic purpose.
* **Recommended V2 Approach:** Add a `FLAG_PURPOSE_MISMATCH` routing flag. If `is_misaligned` is true, the API should output an explicit warning for the loan officer, requiring manual verification of the business plan before funds are disbursed.
