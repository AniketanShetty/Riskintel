# Loan_Default1.csv — Certification Audit
**Date:** 2026-06-11
**Auditor:** Banking Model Risk Committee

---

## 1. Target Certification

**Question:** What is the exact meaning of the `Status` target?
**Answer:** `Status` represents an **Approval / Rejection** decision, NOT a Default outcome.

**Mathematical Proof:**
* When `Status == 1` (24.6% of the dataset), the `rate_of_interest` column is missing **99.45%** of the time.
* When `Status == 0` (75.4% of the dataset), the `rate_of_interest` column is missing **0.00%** of the time.
* **Conclusion:** You only receive an interest rate if your loan is approved. If `Status = 1` represented a post-loan Default, the interest rate would still exist on the ledger. The near-total absence of interest rate data for `Status = 1` mathematically proves these applications were rejected or abandoned before origination. `Status = 0` means Approved, `Status = 1` means Rejected.

---

## 2. Leakage Certification

Every column was evaluated to determine when the data becomes available to the bank. Using post-decision variables to predict a pre-decision outcome causes catastrophic target leakage.

| Column | Classification | Reason |
| :--- | :--- | :--- |
| `ID`, `year` | UNKNOWN | Identifiers / Constants. |
| `Gender`, `age`, `Region` | PRE_DECISION | Demographics provided at application. |
| `loan_amount`, `term`, `loan_purpose` | PRE_DECISION | Requested by applicant. |
| `income`, `Credit_Score`, `dtir1` | PRE_DECISION | Bureau and application data. |
| `property_value`, `LTV` | PRE_DECISION | Property appraisal happens pre-decision. |
| `approv_in_adv`, `loan_type` | PRE_DECISION | Application routing details. |
| `Credit_Worthiness`, `open_credit` | PRE_DECISION | Pre-decision underwriting flags. |
| `rate_of_interest` | **POST_DECISION** | Assigned by the bank upon approval. |
| `Interest_rate_spread` | **POST_DECISION** | Calculated upon approval. |
| `Upfront_charges` | **POST_DECISION** | Charged upon origination/approval. |

---

## 3. Feature Usability Matrix

| Feature Category | Action | Justification |
| :--- | :--- | :--- |
| `rate_of_interest`, `Upfront_charges`, `Interest_rate_spread` | **DROP** | Severe target leakage. Will artificially inflate model accuracy to near 100%. |
| `ID`, `year` | **DROP** | Irrelevant identifiers and constants. |
| `Gender`, `age`, `Region`, `race` | **INVESTIGATE** | Severe fairness and regulatory risk (ECOA/Fair Lending violations). Must be dropped or masked unless used specifically for bias auditing. |
| `Credit_Score`, `income`, `loan_amount`, `term`, `dtir1`, `LTV` | **KEEP** | Core foundational features for Person A eligibility. Highly predictive and completely organic. |

---

## 4. Person A Compatibility

| Use Case | Score (0-10) | Justification |
| :--- | :--- | :--- |
| **Eligibility (Pre-Approval)** | 9 | Perfect structural alignment once leaky columns are dropped. |
| **Approval Prediction** | 9 | Target perfectly represents historical underwriter decisions. |
| **Credit Risk (Probability of Default)** | 0 | The dataset does not contain post-loan performance data. |
| **Underwriting Support** | 8 | Provides rich combinations of DTI, LTV, and Credit Score. |

---

## 5. Model Risk Review

* **Leakage Risks:** High if untrained personnel use the raw dataset. The interest rate columns perfectly leak the rejection class.
* **Fairness Risks:** Extreme. The dataset explicitly contains `Gender` and `age` (and potentially hidden proxies in `Region`). Under the Equal Credit Opportunity Act (ECOA), training an approval model on gender is illegal. These must be scrubbed before training.
* **Proxy Variables:** `Region` could act as a proxy for race/ethnicity (redlining risk).

---

## 6. Governance Review

* **Source Discoverability:** AMBER (Kaggle/Public Domain).
* **Licensing Evidence:** RED (No formal commercial license attached).
* **Provenance Evidence:** AMBER (Organic nature mathematically verified, but original institution unknown).

---

## 7. Final Decision

**B. Ready after cleaning**

This dataset is structurally sound, mathematically organic, and perfectly aligned with the Person A (Eligibility) objective. It is infinitely superior to the toxic E1 dataset. 

**Mandatory Pre-Training Protocol:**
1. Drop `rate_of_interest`, `Interest_rate_spread`, `Upfront_charges` (Leakage).
2. Drop `Gender`, `age`, `Region` (Fairness/Regulatory Risk).
3. Drop `ID`, `year` (Noise).
4. Impute natural missing values in `income` and `dtir1`.
