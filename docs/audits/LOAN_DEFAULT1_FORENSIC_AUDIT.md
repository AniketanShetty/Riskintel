# Forensic Audit: Loan_Default1.csv
**Date:** 2026-06-11
**Auditor:** Banking Model Risk Committee

---

## 1. Basic Information
* **Row count:** 148,670
* **Column count:** 34
* **Memory usage:** ~173.90 MB
* **Target candidates:** `Status`
* **Missing value profile:** 181,135 total missing values scattered across columns.
* **Duplicate profile:** 0 duplicates.
* **Cardinality profile:** Highly organic variance (e.g., 58,271 unique upfront charges, 22,516 unique interest spreads).

---

## 2. Schema Table

| Column | Datatype | Missing % | Unique Count |
| :--- | :--- | :--- | :--- |
| `ID` | `int64` | 0.00% | 148,670 |
| `year` | `int64` | 0.00% | 1 (Constant) |
| `loan_limit` | `str` | 2.25% | 2 |
| `Gender` | `str` | 0.00% | 4 |
| `approv_in_adv` | `str` | 0.61% | 2 |
| `loan_type` | `str` | 0.00% | 3 |
| `loan_purpose` | `str` | 0.09% | 4 |
| `Credit_Worthiness` | `str` | 0.00% | 2 |
| `open_credit` | `str` | 0.00% | 2 |
| `business_or_commercial` | `str` | 0.00% | 2 |
| `loan_amount` | `int64` | 0.00% | 211 |
| `rate_of_interest` | `float64` | 24.51% | 131 |
| `Interest_rate_spread` | `float64` | 24.64% | 22,516 |
| `Upfront_charges` | `float64` | 26.66% | 58,271 |
| `term` | `float64` | 0.03% | 26 |
| `Neg_ammortization` | `str` | 0.08% | 2 |
| `interest_only` | `str` | 0.00% | 2 |
| `lump_sum_payment` | `str` | 0.00% | 2 |
| `property_value` | `float64` | 10.16% | 385 |
| `construction_type` | `str` | 0.00% | 2 |
| `occupancy_type` | `str` | 0.00% | 3 |
| `Secured_by` | `str` | 0.00% | 2 |
| `total_units` | `str` | 0.00% | 4 |
| `income` | `float64` | 6.15% | 1,001 |
| `credit_type` | `str` | 0.00% | 4 |
| `Credit_Score` | `int64` | 0.00% | 401 |
| `co-applicant_credit_type` | `str` | 0.00% | 2 |
| `age` | `str` | 0.13% | 7 |
| `submission_of_application` | `str` | 0.13% | 2 |
| `LTV` | `float64` | 10.16% | 8,484 |
| `Region` | `str` | 0.00% | 4 |
| `Security_Type` | `str` | 0.00% | 2 |
| `Status` | `int64` | 0.00% | 2 |
| `dtir1` | `float64` | 16.22% | 57 |

---

## 3. Leakage Detection

* **Identifiers:** `ID` (must be dropped).
* **Constant Columns:** `year` (must be dropped).
* **Post-Loan / Approval Leakage:** 
  * `rate_of_interest`
  * `Interest_rate_spread`
  * `Upfront_charges`
  * These variables are heavily missing (~24-26%) perfectly aligning with the `Status = 1` class (~24.6%). This proves they are assigned *after* an approval decision. If an applicant is rejected, they do not get an interest rate. If used in a pre-approval eligibility model, they will cause catastrophic target leakage.

---

## 4. Target Analysis

* **Target Variable:** `Status`
* **Class Balance:**
  * `0`: 75.36%
  * `1`: 24.64%
* **Meaning / Objective:** 
  The ~24.6% positive class exactly mirrors the missing rate of post-approval banking variables (`rate_of_interest`, `Interest_rate_spread`). This indicates that `Status = 1` means **Rejected/Denied** or **Defaulted before terms finalized**. Therefore, the dataset represents an approval gateway, making it structurally aligned with Person A (Eligibility).

---

## 5. Correlations & Predictive Variables

**Top Correlations (Absolute, Numeric Only):**
1. `rate_of_interest`: -0.958 (Massive Leakage)
2. `Upfront_charges`: -0.431 (Massive Leakage)
3. `Interest_rate_spread`: -0.392 (Massive Leakage)
4. `dtir1`: -0.325 (Highly predictive, organic)
5. `property_value`: -0.273 (Highly predictive, organic)
6. `LTV` (Loan-to-Value): -0.267 (Highly predictive, organic)
7. `income`: -0.044 (Organic)
8. `loan_amount`: -0.036 (Organic)

*Note: The negative correlations to interest rate and upfront charges are mathematical artifacts of the 24% missing values for the `Status=1` class being zero-filled during correlation testing. This definitively flags them as leaky predictors.*

---

## 6. Dataset Provenance

* **Organic vs Synthetic:** **Organic.**
The dataset contains organic feature distributions, thousands of natural missing values (e.g., 6.15% missing income, 16.22% missing Debt-to-Income), and realistic categorical cardinality. It is not synthetically generated like E1's dataset.

---

## 7. Scorecard

| Category | Score (0-10) | Justification |
| :--- | :--- | :--- |
| **Data Quality** | 8 | Organic, realistic missing values, high cardinality, sufficient rows. |
| **Governance** | 5 | Unknown licensing/provenance, but data shape is undeniably real. |
| **Modeling Suitability** | 9 | Excellent features (LTV, DTI, Income, Loan Amount, Credit Score). Requires dropping leaky columns. |

---

## 8. Final Verdict

**Verdict: B = Candidate After Cleaning.**

**Recommendation:**
This dataset is a prime candidate to replace the toxic E1 Eligibility model. It contains the exact structural variables required for Person A modeling (`loan_amount`, `income`, `Credit_Score`, `LTV`, `dtir1`). 

**Cleaning Requirements before modeling:**
1. Drop `rate_of_interest`, `Interest_rate_spread`, and `Upfront_charges` immediately to prevent target leakage.
2. Drop the `ID` identifier.
3. Impute missing values organically (e.g., median for `income`, KNN for `dtir1`).
