# Forensic Audit: loan_data.csv
**Date:** 2026-06-11
**Auditor:** Banking Model Risk Committee

---

## 1. Basic Information
* **Row count:** 381
* **Column count:** 13
* **Memory usage:** ~0.17 MB
* **Target candidates:** `Loan_Status`
* **Missing value profile:** 75 missing values in total.
* **Duplicate profile:** 0 duplicates.
* **Cardinality profile:** Very low cardinality overall, highly categorical. Maximum unique continuous value is `ApplicantIncome` (322 uniques).

---

## 2. Schema Table

| Column | Datatype | Missing % | Unique Count |
| :--- | :--- | :--- | :--- |
| `Loan_ID` | `str` | 0.00% | 381 |
| `Gender` | `str` | 1.31% | 2 |
| `Married` | `str` | 0.00% | 2 |
| `Dependents` | `str` | 2.10% | 4 |
| `Education` | `str` | 0.00% | 2 |
| `Self_Employed` | `str` | 5.51% | 2 |
| `ApplicantIncome` | `int64` | 0.00% | 322 |
| `CoapplicantIncome` | `float64` | 0.00% | 182 |
| `LoanAmount` | `float64` | 0.00% | 101 |
| `Loan_Amount_Term` | `float64` | 2.89% | 10 |
| `Credit_History` | `float64` | 7.87% | 2 |
| `Property_Area` | `str` | 0.00% | 3 |
| `Loan_Status` | `str` | 0.00% | 2 |

---

## 3. Target Meaning & Outcomes

* **Target Variable:** `Loan_Status`
* **Class Balance:**
  * `Y` (Approved): 71.1%
  * `N` (Rejected): 28.9%
* **Approval Decision:** **Exists.** The target explicitly represents whether the loan application was approved or rejected.
* **Default Outcome:** **Does NOT exist.** There is no column indicating whether the borrower ultimately repaid or defaulted on the loan.
* **Target Meaning:** Because this dataset contains historical approval decisions but no default outcomes, a model trained on this dataset will only learn to *replicate the bank's previous credit policy*. It will not learn to *predict risk*.

---

## 4. Leakage & Survivor Bias Risks

* **Survivor Bias Risk:** **None.** Survivor bias occurs when you try to train a general approval model using only a dataset of people who were already approved (e.g., trying to use default outcome to predict eligibility). Since this dataset includes both approved and rejected applicants, it does not suffer from survivor bias for an approval task.
* **Target Leakage Risk:** **Low.** All features (Income, Dependents, Credit_History, LoanAmount) represent information known *prior* to the loan decision. Unlike `Loan_Default1.csv`, there are no post-approval leaky features like assigned interest rates or upfront charges.
* **Identifiers:** `Loan_ID` must be dropped.

**Top Feature Correlations (vs. `Loan_Status`):**
1. `Credit_History`: +0.453
2. `LoanAmount`: +0.041
3. `ApplicantIncome`: -0.010

---

## 5. Support Capabilities

Can this dataset support the following?

* **A. Approval model:** **Yes.** The dataset is structurally designed for binary approval classification.
* **B. Default model:** **No.** There is no default outcome data.
* **C. Risk score:** **No.** You cannot calculate a Probability of Default (PD) risk score without historical default data.
* **D. Person A eligibility:** **Structurally Yes, but Practically No.** It contains excellent Person A features (Income, LoanAmount, Credit_History), but with only 381 rows, it is vastly too small to train a modern, robust production machine learning model.

---

## 6. Scorecard

| Category | Score (0-10) | Justification |
| :--- | :--- | :--- |
| **Data Quality** | 7 | Organic missing values, but dataset size is impractically small. |
| **Governance** | 8 | No leakage. No survivor bias. Safe features. |
| **Modeling Suitability** | 1 | 381 rows is unacceptable for production modeling. |

---

## 7. Final Verdict

**Verdict: C = Research Only (Educational)**

**Recommendation:**
This is the classic "Loan Prediction Practice Problem" dataset often found in beginner hackathons (e.g., Analytics Vidhya). It is structurally clean, organic, and free of target leakage. However, it contains no actual default data (meaning it only trains you to mimic a human underwriter, not predict risk) and its row count (381) is far too small for production usage. It can be used for writing unit tests or UI demos, but cannot power a production model.
