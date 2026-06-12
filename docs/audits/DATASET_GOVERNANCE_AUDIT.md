# RiskIntel Dataset Governance Audit
**Date:** 2026-06-11
**Auditor:** Independent Data Governance Committee

---

## Executive Summary
A comprehensive data governance audit was conducted on the six primary datasets located in `data/raw/`. The repository demonstrates a severe reliance on synthetic, pre-cleaned, and mathematically compromised datasets. Out of the six datasets, only one (`Loan_Default1.csv`) exhibits the natural variance and missing-value distribution expected of organic banking data. The foundational datasets used to train E1 (`loan_approval_dataset.csv`) and E3 (`External_Cibil_Dataset.csv`) must be strictly banned from production use.

---

## 1. Dataset Profiles

### `Loan_Default1.csv`
1. **Row count:** 148,670
2. **Column count:** 34
3. **Candidate targets:** `Status` (Verified meaning: Approval/Rejection)
4. **Missing value profile:** 181,135 missing values scattered across columns.
5. **Duplicate profile:** 0 duplicates.
6. **Leakage columns:** `rate_of_interest`, `Interest_rate_spread`, `Upfront_charges` (Assigned during/after approval).
7. **Synthetic-data indicators:** Low. The massive missing value count and rich feature set indicate raw, organic field data.
8. **Licensing evidence:** UNKNOWN.
9. **Source provenance evidence:** UNKNOWN.
10. **Intended modeling use:** Research Scaffolding Only (Failed Domain Alignment: Formal Mortgage Lending, mismatched for Microfinance).

### `Loan_default.csv`
1. **Row count:** 255,347
2. **Column count:** 18
3. **Candidate targets:** `Default`
4. **Missing value profile:** 0 missing values.
5. **Duplicate profile:** 0 duplicates.
6. **Leakage columns:** `InterestRate`
7. **Synthetic-data indicators:** Medium. 0 missing values across 255k rows indicates heavy pre-imputation by the author.
8. **Licensing evidence:** UNKNOWN (Kaggle).
9. **Source provenance evidence:** Kaggle.
10. **Intended modeling use:** Post-approval Default Prediction.

### `Loan_Prediction.csv`
1. **Row count:** 12,367
2. **Column count:** 8
3. **Candidate targets:** `loan_approved`
4. **Missing value profile:** 0 missing values.
5. **Duplicate profile:** 0 duplicates.
6. **Leakage columns:** None catastrophic.
7. **Synthetic-data indicators:** High. 0 missing values and structurally broken (missing `loan_amount` and `loan_term`).
8. **Licensing evidence:** UNKNOWN.
9. **Source provenance evidence:** UNKNOWN.
10. **Intended modeling use:** Approval prediction (fundamentally flawed due to missing loan amount).

### `loan_data.csv`
1. **Row count:** 381
2. **Column count:** 13
3. **Candidate targets:** `Loan_Status`
4. **Missing value profile:** 75 missing values.
5. **Duplicate profile:** 0 duplicates.
6. **Leakage columns:** None.
7. **Synthetic-data indicators:** Low (Organic).
8. **Licensing evidence:** UNKNOWN.
9. **Source provenance evidence:** Classic Analytics Vidhya Hackathon dataset.
10. **Intended modeling use:** Educational binary classification. Too small for production.

### `loan_approval_dataset.csv`
1. **Row count:** 4,269
2. **Column count:** 13
3. **Candidate targets:** `loan_status`
4. **Missing value profile:** 0 missing values.
5. **Duplicate profile:** 0 duplicates.
6. **Leakage columns:** `cibil_score` (Target generated perfectly from CIBIL).
7. **Synthetic-data indicators:** 100% Synthetic (Script generated).
8. **Licensing evidence:** UNKNOWN.
9. **Source provenance evidence:** UNKNOWN.
10. **Intended modeling use:** E1 Eligibility Model (Failed).

### `External_Cibil_Dataset.csv`
1. **Row count:** 51,336
2. **Column count:** 62
3. **Candidate targets:** `Approved_Flag`
4. **Missing value profile:** 0 missing values.
5. **Duplicate profile:** 0 duplicates.
6. **Leakage columns:** Extensive post-disbursement delinquency columns.
7. **Synthetic-data indicators:** High. 0 missing values across 62 complex delinquency/bureau metrics is practically impossible in raw banking data without massive synthetic imputation.
8. **Licensing evidence:** UNKNOWN.
9. **Source provenance evidence:** UNKNOWN.
10. **Intended modeling use:** E3 Archetype Clustering.

---

## 2. Dataset Inventory Table

| Dataset | Keep | Reject | Investigate |
|----------|--------|--------|--------|
| `Loan_Default1.csv` | | **X** | |
| `Loan_default.csv` | | | **X** |
| `loan_data.csv` | **X** | | |
| `RuralCreditData.csv` | **X** | | |
| `Loan_Prediction.csv` | | **X** | |
| `External_Cibil_Dataset.csv` | | **X** | |
| `loan_approval_dataset.csv` | | **X** | |

---

## 3. Suitability Matrix

| Use Case | Suitable Datasets |
|-----------|------------------|
| **Eligibility Modeling** | None (Domain mismatches and synthetic contamination) |
| **Default Prediction** | `Loan_default.csv` |
| **Risk Scoring** | `Loan_default.csv` |
| **Person B Validation** | `RuralCreditData.csv` |
| **Demo Only** | `loan_data.csv` |
| **Archive Only** | `loan_approval_dataset.csv`, `External_Cibil_Dataset.csv`, `Loan_Prediction.csv` |

---

## 4. Governance Scorecard

| Dataset | Provenance Score (0-10) | Licensing Score (0-10) | Data Quality Score (0-10) | Production Readiness Score (0-10) |
| :--- | :--- | :--- | :--- | :--- |
| `Loan_Default1.csv` | 2 | 0 | 8 (Organic) | 2 (Wrong Domain) |
| `RuralCreditData.csv` | 2 | 0 | 8 (Organic) | 7 (Needs cleaning) |
| `Loan_default.csv` | 5 | 0 | 6 (Pre-imputed) | 5 (Survivor bias) |
| `loan_data.csv` | 8 | 0 | 7 | 1 (Too small) |
| `Loan_Prediction.csv` | 0 | 0 | 2 (Broken) | 0 |
| `External_Cibil_Dataset.csv`| 0 | 0 | 1 (Suspiciously dense) | 0 |
| `loan_approval_dataset.csv` | 0 | 0 | 0 (Toxic) | 0 |

---

## 5. Final Recommendation

**A = Strategic Asset**
* *(None currently qualify due to lack of licensing evidence).*

**B = Useful**
* `RuralCreditData.csv`: Highly organic profiling data. Perfect schema for Person B verification.
* `Loan_default.csv`: Can be used for Risk-Based Pricing or PD modeling, but NOT for pre-approval eligibility.

**C = Educational Only**
* `loan_data.csv`: A classic 381-row hackathon dataset. Good for writing unit tests but not for production training.

**D = Reject**
* `Loan_Default1.csv`: Failed domain alignment (Formal Western Mortgage Data). Irrelevant for Indian Microfinance. Scaffolding only.
* `Loan_Prediction.csv`: Synthetic and missing fundamental features (`loan_amount`).
* `External_Cibil_Dataset.csv`: Highly suspicious 0-missing density across 62 fields. Used for the cosmetic E3 engine.

**F = Toxic**
* `loan_approval_dataset.csv`: 100% synthetic, complete target leakage. Must be banned from the repository.
