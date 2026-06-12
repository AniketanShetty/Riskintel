# Model Replacement Feasibility Audit: Loan_Default1.csv
**Date:** 2026-06-11
**Auditor:** Banking Model Risk Committee

---

## 1. Target Semantics Verification
**Target Column:** `Status` (Binary: 0 = 75.4%, 1 = 24.6%)
We must interpret what `Status` means without relying on anonymous Kaggle documentation. We use the missingness of post-origination financial metrics (`rate_of_interest`, `Upfront_charges`) as our evidence base.

| Interpretation | Confidence | Evidence |
| :--- | :--- | :--- |
| **Rejection / Denial** | **99%** | When `Status=1`, interest rate is missing 99.45% of the time. You do not get an interest rate if you are rejected. When `Status=0`, it is missing 0.00% of the time. |
| **Abandonment / Cancellation** | **80%** | Borrowers who apply but abandon the process before locking terms would also lack an interest rate. `Status=1` likely contains a mix of formal rejections and applicant abandonments. |
| **Default** | **5%** | If a loan defaults, it must have been originated first. Originated loans have assigned interest rates on the ledger. `Status=1` lacks interest rates, making "Default" mathematically illogical. |
| **Post-Loan Delinquency** | **5%** | Same as above. You cannot be delinquent on a loan that never received an interest rate or upfront charge. |
| **Approval** | **0%** | If `Status=1` meant Approval, it would have the interest rates, and the 75% class would have the missing values. The inverse is true. |

**Conclusion:** `Status=0` = Approved/Originated. `Status=1` = Rejected/Abandoned.

---

## 2. Feature Timeline Table
To prevent target leakage, every column is classified by *when* the data becomes available to the bank.

| Feature | Timeline Classification | Leakage Risk |
| :--- | :--- | :--- |
| `Gender`, `age`, `Region` | Pre-application | Low (but High Regulatory Risk) |
| `loan_amount`, `term`, `loan_purpose` | Application-time | Low |
| `income`, `Credit_Score`, `dtir1` | Underwriting-time | Low |
| `property_value`, `LTV` | Underwriting-time | Low (post-appraisal) |
| `Credit_Worthiness`, `approv_in_adv` | Underwriting-time | Low (pre-approval indicators) |
| `rate_of_interest` | **Post-approval** | **SEVERE LEAKAGE** |
| `Interest_rate_spread` | **Post-approval** | **SEVERE LEAKAGE** |
| `Upfront_charges` | **Post-origination** | **SEVERE LEAKAGE** |

---

## 3. Person A Compatibility Matrix
Can this dataset replace the E1 Eligibility Engine?

| Use Case | Score (0-10) | Justification |
| :--- | :--- | :--- |
| **Eligibility Decisions** | 9 | Dataset perfectly mirrors the pre-approval gateway logic required by Person A. |
| **Approval Prediction** | 9 | Target explicitly represents historical underwriter approval/rejection. |
| **Underwriting Support** | 8 | Rich interactions between DTI, LTV, and Credit Score for rules generation. |
| **Risk Scoring (PD)** | 0 | No post-loan default outcomes exist in this dataset. |
| **Probability of Default** | 0 | Same as above. |
| **Recommendation Generation** | 8 | Clear numeric boundaries (LTV, DTI) allow for "reduce loan amount" recommendations. |

---

## 4. Fairness Audit
Under the Equal Credit Opportunity Act (ECOA), an eligibility model cannot legally discriminate based on protected attributes.

* **Protected Attributes Present:** `Gender`, `age`.
* **Proxy Variables Present:** `Region` (Highly likely to act as a proxy for racial redlining or geographic discrimination).
* **Features That Must NEVER Be Used For Training:** `Gender`, `age`, `Region`. 

If these features are left in the training matrix, the resulting Person A model will be fundamentally illegal for U.S. banking deployment.

---

## 5. Monotonicity Suitability Audit
RiskIntel requires monotonic constraints to ensure mathematical defensibility (e.g., higher income should never lower your chances of approval, holding all else equal).

| Feature | Present? | Monotonic Constraint Suitability |
| :--- | :--- | :--- |
| **Income** (`income`) | YES | Positive (Higher income = Higher approval chance) |
| **Loan Amount** (`loan_amount`) | YES | Negative (Higher amount = Lower approval chance) |
| **Credit Score** (`Credit_Score`) | YES | Positive (Higher score = Higher approval chance) |
| **LTV** (`LTV`) | YES | Negative (Higher LTV = Lower approval chance) |
| **DTI** (`dtir1`) | YES | Negative (Higher DTI = Lower approval chance) |

**Conclusion:** The dataset is fully equipped to support a rigorously constrained, monotonic XGBoost or LightGBM model.

---

## 6. Final Verdict

**B = Candidate After Cleaning**

**Summary Justification:**
Mathematically and structurally, `Loan_Default1.csv` is the perfect candidate to replace the toxic E1 Eligibility model. It supports monotonic constraints, provides the exact features required for Person A, and its target explicitly maps to approval/rejection. 

However, as determined in the provenance audit, its **Governance is Weak** and its **Production Use is Questionable**. It is a public Kaggle dataset with anonymous origins and no commercial license. 

**Model Risk Committee Ruling:**
We approve `Loan_Default1.csv` as the foundational dataset for the *next iteration* of the RiskIntel Person A model (Proof of Concept / Candidate phase) **strictly contingent** upon the following cleaning steps:
1. All leaky variables (`rate_of_interest`, `Interest_rate_spread`, `Upfront_charges`) are permanently dropped.
2. All protected variables (`Gender`, `age`, `Region`) are permanently dropped.
3. The model is explicitly tagged as `NON-COMMERCIAL RESEARCH ORIGIN`.
