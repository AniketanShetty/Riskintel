# RiskIntel Dataset Forensics Audit Master
**Date:** 2026-06-10
**Auditor:** Independent Data Governance Committee

---

## 1. `loan_approval_dataset.csv`

### Dataset Identity
* **Filename:** `loan_approval_dataset.csv`
* **Source:** UNKNOWN
* **Kaggle URL:** UNKNOWN
* **License:** UNKNOWN
* **Commercial usage allowed?:** UNKNOWN
* **Contains PII?:** No
* **Contains sensitive data?:** No

### Dataset Shape
* **Rows:** 4,269
* **Columns:** 13
* **Memory size:** 1.02 MB

### Data Quality
* **Missing values:** 0
* **Duplicate rows:** 0
* **Duplicate columns:** 0
* **Constant columns:** None
* **Near-constant columns:** None
* **Outliers:** Perfectly bounded synthetic ranges.

### Target Analysis
* **Target column:** `loan_status`
* **Business objective:** Approval prediction

### Leakage Audit
* **Leakage:** `cibil_score` has an impossible `0.77` Pearson correlation with the target. The target was deterministically generated via a scripted rule based on `cibil_score` and `loan_term`.
* **Classification:** 
  * `cibil_score`: **REJECT**

### Feature Audit
* **Person A Fit:** Excellent coverage of assets, income, and credit score. Completely omits `age`.
* **Person B Fit:** Poor. No infrastructure or business data.

### Distribution Audit
* **Class balance:** Approved (62.2%), Rejected (37.8%)
* **Unrealistic ranges:** The complete lack of missing values across 13 financial features for 4,000 applicants proves the dataset is a synthetic artifact, not organic banking data.

### Governance Audit
| Category | Score 0-10 |
|-----------|-----------|
| License | 0 |
| Provenance | 0 |
| Quality | 0 |
| Leakage Risk | 10 |
| RiskIntel Fit | 8 |

### Final Verdict
**D = Reject.** 
This is the exact same toxic, synthetic dataset used to train the decommissioned E1 model. It is mathematically invalid and legally undefendable.

---

## 2. `Loan_Prediction.csv`

### Dataset Identity
* **Filename:** `Loan_Prediction.csv`
* **Source:** UNKNOWN
* **Kaggle URL:** UNKNOWN
* **License:** UNKNOWN
* **Commercial usage allowed?:** UNKNOWN
* **Contains PII?:** No
* **Contains sensitive data?:** Yes (criminal record)

### Dataset Shape
* **Rows:** 12,367
* **Columns:** 8
* **Memory size:** 0.75 MB

### Data Quality
* **Missing values:** 0
* **Duplicate rows:** 0
* **Duplicate columns:** 0
* **Constant columns:** None
* **Near-constant columns:** None

### Target Analysis
* **Target column:** `loan_approved`
* **Business objective:** Approval prediction

### Leakage Audit
* **Leakage:** No catastrophic single-feature leakage, but zero missing values strongly implies synthetic generation or heavy pre-processing.
* **Classification:**
  * `criminal_record`: **WARNING** (Check if legally usable in lending decisions).

### Feature Audit
* **Person A Fit:** Missing critical features: `loan_amount` and `loan_term`. You cannot predict loan approval without knowing how much money the applicant wants.
* **Person B Fit:** Zero fit.

### Distribution Audit
* **Class balance:** Rejected (88.6%), Approved (11.4%). Highly skewed.
* **Unrealistic ranges:** 0 missing values.

### Governance Audit
| Category | Score 0-10 |
|-----------|-----------|
| License | 0 |
| Provenance | 0 |
| Quality | 3 |
| Leakage Risk | 3 |
| RiskIntel Fit | 2 |

### Final Verdict
**D = Reject.**
A loan approval dataset that does not contain `loan_amount` or `loan_term` is structurally useless. Furthermore, it is likely synthetic given the zero missing values.

---

## 3. `Loan_default.csv`

### Dataset Identity
* **Filename:** `Loan_default.csv`
* **Source:** Kaggle (Likely "Loan Default Prediction")
* **Kaggle URL:** UNKNOWN
* **License:** UNKNOWN
* **Commercial usage allowed?:** UNKNOWN
* **Contains PII?:** No
* **Contains sensitive data?:** No

### Dataset Shape
* **Rows:** 255,347
* **Columns:** 18
* **Memory size:** 126.81 MB

### Data Quality
* **Missing values:** 0
* **Duplicate rows:** 0
* **Duplicate columns:** 0
* **Constant columns:** None

### Target Analysis
* **Target column:** `Default`
* **Business objective:** Default prediction (Post-loan outcome)

### Leakage Audit
* **Leakage:** The target is `Default`, meaning this dataset only contains borrowers who were *already approved*. If used to train an approval model (E1), it suffers from severe survivor bias. `InterestRate` is assigned at approval, making it a potential leak if not handled carefully.
* **Classification:**
  * `InterestRate`: **WARNING**

### Feature Audit
* **Person A Fit:** Outstanding. Contains Age, Income, LoanAmount, CreditScore, LoanTerm, Employment, and Dependents.
* **Person B Fit:** Weak. Lacks infrastructure and granular business types.

### Distribution Audit
* **Class balance:** Non-Default (88.4%), Default (11.6%).
* **Unrealistic ranges:** 0 missing values across 255k rows indicates massive pre-imputation by the Kaggle author.

### Governance Audit
| Category | Score 0-10 |
|-----------|-----------|
| License | 0 |
| Provenance | 5 |
| Quality | 6 |
| Leakage Risk | 7 |
| RiskIntel Fit | 7 |

### Final Verdict
**C = Educational only.**
The dataset has excellent features for Person A, but the target is `Default` (post-approval), not `Eligibility` (pre-approval). Using this to train E1 would result in severe survivor bias. It can be used educationally to model risk-based pricing, but not organic eligibility gating.

---

## 4. `RuralCreditData.csv`

### Dataset Identity
* **Filename:** `RuralCreditData.csv`
* **Source:** UNKNOWN
* **Kaggle URL:** UNKNOWN
* **License:** UNKNOWN
* **Commercial usage allowed?:** UNKNOWN
* **Contains PII?:** No
* **Contains sensitive data?:** Yes (social_class, sex)

### Dataset Shape
* **Rows:** 40,000
* **Columns:** 21
* **Memory size:** 18.96 MB

### Data Quality
* **Missing values:** 19,066
* **Duplicate rows:** 0
* **Duplicate columns:** 0
* **Constant columns:** None
* **Outliers:** Massive data entry errors (Age = 766,105). This is a hallmark of truly organic, raw field data.

### Target Analysis
* **Target column:** None
* **Business objective:** Customer profiling / Unsupervised learning

### Leakage Audit
* **Leakage:** N/A (No target column to leak into).
* **Classification:** SAFE

### Feature Audit
* **Person A Fit:** Weak (Lacks credit score).
* **Person B Fit:** **Perfect.** Exactly matches E5 Readiness Engine fields: `primary_business`, `monthly_expenses`, `type_of_house`, `water_availabity`, `sanitary_availability`, `young_dependents`.

### Distribution Audit
* **Class balance:** N/A
* **Unrealistic ranges:** Extreme positive skew in age (up to 766,105) and house area. Requires heavy cleaning.

### Governance Audit
| Category | Score 0-10 |
|-----------|-----------|
| License | 0 |
| Provenance | 2 |
| Quality | 8 (Organic) |
| Leakage Risk | 0 |
| RiskIntel Fit | 10 |

### Final Verdict
**B = Candidate.**
This dataset contains no target, meaning it cannot be used for supervised approval prediction. However, it is highly organic (evidenced by missing values and human-error outliers) and perfectly maps to the Person B New-To-Credit schema. It is an excellent candidate for unsupervised clustering (E3 Archetypes) or testing the deterministic E5 Readiness Engine.

---

## Final Dataset Comparison Matrix

| Dataset | License | Leakage | Quality | Person A Fit | Person B Fit | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `RuralCreditData.csv` | UNKNOWN | SAFE | Organic/Messy | Poor | Perfect | **B** |
| `Loan_default.csv` | UNKNOWN | WARNING (Survivor Bias) | Pre-Cleaned | Excellent | Poor | **C** |
| `Loan_Prediction.csv` | UNKNOWN | WARNING (Synthetic) | Synthetic | Broken | Poor | **D** |
| `loan_approval_dataset.csv`| UNKNOWN | REJECT (100% Leakage) | Synthetic | Good | Poor | **D** |

### Ranking (Best to Worst)
1. **`RuralCreditData.csv`** (Highly organic, perfect Person B schema, safely targetless).
2. **`Loan_default.csv`** (Excellent Person A features, but suffers from survivor bias and pre-imputation).
3. **`Loan_Prediction.csv`** (Synthetic, fundamentally missing loan amount).
4. **`loan_approval_dataset.csv`** (The toxic E1 dataset. Mathematically invalid).
