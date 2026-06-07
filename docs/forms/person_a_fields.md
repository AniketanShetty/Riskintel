# Person A — Input Field Specifications

**Workflow:** Credit-Aware Borrower

**Engines Served:**
- Eligibility Engine (Dataset A)
- Risk Tier Engine (Dataset C)
- Archetype Engine (Dataset C)
- Recommendation Engine (Dataset C)

---

## Design Rationale

Person A has existing credit history and a bureau score. The form collects two categories of data:

1. **Basic profile + loan details** — feeds the Eligibility Engine (Dataset A) and provides context for all engines.
2. **Credit behavior features** — feeds the Risk Tier, Archetype, and Recommendation Engines (Dataset C).

Fields shared across datasets (income, loan amount, loan term) are collected once and mapped to both. Fields unique to the user's credit profile (EMI, utilization, delinquency) are marked optional where a typical applicant may not know the exact value — the backend applies defaults or estimates when omitted.

---

## Field Definitions

### Section 1 — Personal Information

| # | User Label | Internal Name | Data Type | Required | Validation Rules | Example Value | Dataset Source | Used By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Full Name | `full_name` | String | Required | Min 2 chars, max 100 chars. Letters, spaces, periods only. | Aniket Sharma | — (report only) | PDF Report Engine |
| 2 | Age | `age` | Integer | Required | Min: 18, Max: 70 | 34 | Dataset C: `Age` | Risk Tier, Archetype, Recommendation |
| 3 | Gender | `gender` | Select | Required | Allowed: `male`, `female`, `other` | male | Dataset A: `Gender` | Eligibility |
| 4 | Marital Status | `married` | Select | Required | Allowed: `yes`, `no` | yes | Dataset A: `Married` | Eligibility |
| 5 | Dependents | `dependents` | Select | Required | Allowed: `0`, `1`, `2`, `3+` | 2 | Dataset A: `Dependents` | Eligibility |
| 6 | Education | `education` | Select | Required | Allowed: `graduate`, `not_graduate` | graduate | Dataset A: `Education` | Eligibility |
| 7 | Employment Type | `self_employed` | Select | Required | Allowed: `yes`, `no` | no | Dataset A: `Self_Employed` | Eligibility |

---

### Section 2 — Income and Assets

| # | User Label | Internal Name | Data Type | Required | Validation Rules | Example Value | Dataset Source | Used By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 8 | Monthly Income | `applicant_income` | Integer | Required | Min: 0, Max: 10,000,000. No decimals. | 65000 | Dataset A: `ApplicantIncome`, Dataset C: `Income` | Eligibility, Risk Tier, Archetype, Recommendation |
| 9 | Co-applicant Monthly Income | `coapplicant_income` | Integer | Required | Min: 0, Max: 10,000,000. Enter 0 if none. | 0 | Dataset A: `CoapplicantIncome` | Eligibility |
| 10 | Total Asset Value | `asset_value` | Integer | Optional | Min: 0, Max: 100,000,000. Combined value of movable and immovable assets. | 2500000 | Dataset C: `Asset_Value` | Risk Tier, Archetype, Recommendation |

---

### Section 3 — Loan Details

| # | User Label | Internal Name | Data Type | Required | Validation Rules | Example Value | Dataset Source | Used By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 11 | Loan Amount Requested | `loan_amount` | Integer | Required | Min: 10,000, Max: 50,000,000 | 1500000 | Dataset A: `LoanAmount`, Dataset C: `Loan_Amount` | Eligibility, Risk Tier, Archetype, Recommendation |
| 12 | Loan Term | `loan_term` | Select | Required | Allowed values (months): `12`, `36`, `60`, `84`, `120`, `180`, `240`, `360` | 360 | Dataset A: `Loan_Amount_Term`, Dataset C: `Loan_Tenure` | Eligibility, Risk Tier |
| 13 | Loan Purpose | `loan_purpose` | Select | Required | Allowed: `home`, `education`, `personal`, `business`, `vehicle`, `medical` | home | — (context) | Report, Recommendation |
| 14 | Property Area | `property_area` | Select | Required | Allowed: `urban`, `semiurban`, `rural` | urban | Dataset A: `Property_Area` | Eligibility |

---

### Section 4 — Credit Profile

| # | User Label | Internal Name | Data Type | Required | Validation Rules | Example Value | Dataset Source | Used By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 15 | Credit Score (CIBIL) | `credit_score` | Integer | Required | Min: 300, Max: 900 | 742 | Dataset C: `CIBIL_Score` | Risk Tier, Archetype, Recommendation |
| 16 | Credit History | `credit_history` | Select | Required | Allowed: `1` (meets guidelines), `0` (does not meet guidelines) | 1 | Dataset A: `Credit_History` | Eligibility |
| 17 | Existing Monthly EMI | `existing_emi` | Integer | Optional | Min: 0, Max: 1,000,000. Total of all current EMI payments. Enter 0 if no active loans. | 12000 | Dataset C: `Existing_EMI` | Risk Tier, Archetype, Recommendation |
| 18 | Number of Active Loans | `number_of_loans` | Integer | Optional | Min: 0, Max: 20 | 2 | Dataset C: `Number_of_Loans` | Risk Tier, Archetype, Recommendation |
| 19 | Months of Past Delinquency | `delinquent_months` | Integer | Optional | Min: 0, Max: 120. Number of months with missed or late payments in the last 5 years. | 0 | Dataset C: `Delinquent_Months` | Risk Tier, Archetype, Recommendation |
| 20 | Credit Utilization (%) | `credit_utilization` | Integer | Optional | Min: 0, Max: 100. Percentage of available credit currently used. | 35 | Dataset C: `Credit_Utilization` | Risk Tier, Archetype, Recommendation |

---

## Field Count Summary

| Category | Required | Optional | Total |
| :--- | :--- | :--- | :--- |
| Personal Information | 7 | 0 | 7 |
| Income and Assets | 2 | 1 | 3 |
| Loan Details | 4 | 0 | 4 |
| Credit Profile | 2 | 4 | 6 |
| **Total** | **15** | **5** | **20** |

---

## Engine Coverage Map

This table confirms every engine has at least the minimum required fields to produce its output.

| Engine | Required Fields Used | Optional Fields Used |
| :--- | :--- | :--- |
| **Eligibility Engine** | `gender`, `married`, `dependents`, `education`, `self_employed`, `applicant_income`, `coapplicant_income`, `loan_amount`, `loan_term`, `credit_history`, `property_area` (11 fields) | — |
| **Risk Tier Engine** | `age`, `applicant_income`, `loan_amount`, `loan_term`, `credit_score` (5 fields) | `asset_value`, `existing_emi`, `number_of_loans`, `delinquent_months`, `credit_utilization` (5 fields) |
| **Archetype Engine** | `age`, `applicant_income`, `loan_amount`, `credit_score` (4 fields) | `asset_value`, `existing_emi`, `number_of_loans`, `delinquent_months`, `credit_utilization` (5 fields) |
| **Recommendation Engine** | `applicant_income`, `loan_amount`, `credit_score` (3 fields) | `asset_value`, `existing_emi`, `number_of_loans`, `delinquent_months`, `credit_utilization` (5 fields) |
| **PDF Report Engine** | `full_name` + all assessment outputs | All fields included in report |

---

## Default Values for Optional Fields

When an optional field is omitted, the backend applies these defaults during preprocessing:

| Field | Default Value | Rationale |
| :--- | :--- | :--- |
| `asset_value` | `0` | Conservative: assume no declared assets |
| `existing_emi` | `0` | Assume no current EMI obligations |
| `number_of_loans` | `0` | Assume no active loans |
| `delinquent_months` | `0` | Assume clean payment history |
| `credit_utilization` | `30` | Industry median utilization |

---

## Frontend Grouping

Fields should be presented to the user in four sections matching the table structure above:

1. **Personal Information** — Quick demographic capture
2. **Income & Assets** — Financial standing
3. **Loan Details** — What they are applying for
4. **Credit Profile** — Bureau and repayment history

This ordering follows a natural progression from "who are you" → "what do you earn" → "what do you want" → "what is your credit history."
