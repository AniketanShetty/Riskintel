# Domain Alignment Audit: Loan_Default1.csv
**Date:** 2026-06-11
**Auditor:** Banking Model Risk Committee

---

## Objective
Determine whether `Loan_Default1.csv` is solving the correct underwriting problem for RiskIntel, or if it is merely a high-quality dataset representing the wrong lending universe.

---

## Part 1 — Lending Domain Identification

**Most Likely Lending Domain: Formal Mortgage / Housing Finance (Western/U.S. Context)**
**Confidence Score: 99%**

**Evidence Columns:**
1. `property_value`: Formal real estate appraisals.
2. `LTV` (Loan-to-Value): The definitive metric of mortgage lending (loan amount divided by property value).
3. `occupancy_type`: Standard mortgage categorization (e.g., Primary Residence, Investment Property, Second Home).
4. `construction_type`: Standard mortgage categorization (e.g., Site-built vs. Manufactured housing).
5. `total_units`: Indicates single-family vs. multi-family (duplex/triplex) housing.
6. `Secured_by`: Indicates collateral-backed lending.
7. `Neg_ammortization` & `interest_only`: Complex mortgage repayment structures common in advanced Western financial markets (e.g., Adjustable Rate Mortgages).

**Competing Hypotheses:**
* *Personal / Consumer Lending:* Rejected. Personal loans are unsecured and do not have LTV, construction types, or property values.
* *Vehicle Finance:* Rejected. Vehicle finance does not use "total units" or "construction type".
* *Microfinance:* Rejected. Microfinance is predominantly unsecured, cash-flow-based, or peer-liability lending, completely lacking formal real estate collateral.

---

## Part 2 — RiskIntel Fit Analysis

**RiskIntel Mission:** Explainable underwriting for the Indian microfinance, small-ticket, and new-to-credit (NTC) ecosystem.

**Analysis:**
A model trained on `Loan_Default1.csv` would learn **mortgage underwriting behavior**, not microfinance behavior. 

1. **Indian Microfinance:** Fails completely. Microfinance borrowers typically lack formal real estate collateral. A mortgage model would instantly reject these borrowers because their `property_value` is zero or missing, and `LTV` cannot be calculated.
2. **Small-ticket business loans:** Fails. This data is optimized for evaluating 30-year property collateral, not 12-month working capital limits.
3. **Rural borrowers:** Fails. The formal DTI (`dtir1`) calculations in this dataset assume formal, verifiable, documented W2/salaried income. Rural Indian borrowers rely heavily on informal, seasonal, and agricultural income.
4. **New-to-credit borrowers:** Fails. Mortgage underwriting strictly requires deep bureau history. NTC borrowers are completely excluded from this dataset's distribution.
5. **Livelihood-based underwriting:** Fails. There are no fields here for business type, daily cash flow, or household livelihood composition.

---

## Part 3 — Feature Transferability Matrix

| Feature | Action | Justification |
| ------- | ---- | ----- |
| `Credit_Score` | **Keep** | Universal credit-risk feature. |
| `income` | **Keep** | Universal capacity feature (though scaling differs vastly from microfinance). |
| `loan_amount` | **Keep** | Universal exposure feature. |
| `property_value` | **Reject** | Microfinance is unsecured. Borrowers do not have appraised real estate. |
| `LTV` | **Reject** | Irrelevant without formal collateral. |
| `occupancy_type` | **Reject** | Mortgage-specific feature. |
| `construction_type`| **Reject** | Mortgage-specific feature. |
| `dtir1` | **Adapt** | Debt-to-Income is universal in concept, but microfinance calculates informal DTI using household cash flow, not formal tax returns. |
| `Neg_ammortization`| **Reject** | Complex Western mortgage structure. Irrelevant to microfinance. |
| `total_units` | **Reject** | Mortgage-specific feature. |

---

## Part 4 — Hidden Assumption Attack

**Target Statement for Attack:** *"Loan_Default1 should replace E1."*

**The Attack (Model Risk Committee Critique):**
While `Loan_Default1` is mathematically organic and clean, deploying it as the foundation for RiskIntel is a **strategic failure and a massive domain mismatch.**

1. **Lending Product Mismatch:** RiskIntel is building an unsecured microfinance system. `Loan_Default1` is a highly-collateralized mortgage dataset. If we train an AI on this data, it will learn that collateral (`property_value`) is the primary driver of risk reduction. When deployed in the real world, it will unfairly reject every unbanked microfinance applicant who lacks formal real estate.
2. **Geographic / Economic Mismatch:** The presence of fields like `dtir1` and `Neg_ammortization` strongly suggest a U.S. or Western housing market origin. Training on Western macro-economic housing data to underwrite Indian micro-entrepreneurs is mathematically indefensible.
3. **The "Data-First" Fallacy:** Choosing this dataset falls into the classic trap of prioritizing data cleanliness over business reality. We are trying to build an engine for Person A (small-ticket credit) and Person B (livelihood). A clean dataset solving the *wrong* problem is actively harmful. It is worse than having no model at all, because it will produce mathematically confident but logically absurd microfinance recommendations (e.g., "Your application was rejected because your property construction type is unknown").

---

## Part 5 — Final Verdict

**Verdict: D. Wrong lending universe**

**Answers to strategic questions:**
1. **Can Loan_Default1 replace E1 immediately?** No. It solves an entirely different banking problem (Mortgage Origination).
2. **Can it be used only as a temporary research dataset?** Yes, strictly as a temporary scaffolding dataset to test MLOps pipelines or API contracts, but it must **never** be used to evaluate a real microfinance applicant. 
3. **Would collecting a smaller but domain-correct microfinance dataset be strategically better?** Absolutely. A 2,000-row organic dataset of true unsecured microfinance loans is infinitely more valuable to RiskIntel than 148,000 rows of US mortgage data. 

**Conclusion:**
`Loan_Default1.csv` is a statistically excellent dataset for a mortgage lender. It is the wrong foundation for an Indian microfinance system. We should demote it from "Person A Candidate" to "Research Scaffolding Only" and prioritize acquiring a domain-correct unsecured lending dataset.
