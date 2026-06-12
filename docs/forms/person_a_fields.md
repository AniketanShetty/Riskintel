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

Fields shared across datasets (loan amount, loan term) are collected once and mapped to both. Fields unique to the user's credit profile (EMI, utilization, delinquency) are marked optional where a typical applicant may not know the exact value — the backend applies defaults or estimates when omitted.

*Note: Per V2 Constitution, exact numeric income, marital status, direct dependent counting, and sole earner status are explicitly banned. Income is collected as a broad bracket for Triage only. Age is strictly derived via KYC, not manual input.*

---

## Field Definitions

### Section 1 — Personal Information

| # | User Label | Internal Name | Data Type | Required | Validation Rules | Example Value | Dataset Source | Used By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Full Name | `full_name` | String | Required | Min 2 chars, max 100 chars. Letters, spaces, periods only. | Aniket Sharma | — (report only) | PDF Report Engine |

---

### Section 2 — Income and Assets

| # | User Label | Internal Name | Data Type | Required | Validation Rules | Example Value | Dataset Source | Used By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2 | Income Bracket | `income_bracket` | Select | Required | Standard predefined ranges (e.g., `20k-30k`). | 40k-50k | Intake | Triage Engine |

---

### Section 3 — Loan Details

| # | User Label | Internal Name | Data Type | Required | Validation Rules | Example Value | Dataset Source | Used By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 3 | Loan Amount Requested | `loan_amount` | Integer | Required | Min: 10,000, Max: 50,000,000 | 1500000 | Dataset A: `LoanAmount`, Dataset C: `Loan_Amount` | Eligibility, Risk Tier, Archetype, Recommendation |
| 4 | Loan Term | `loan_term` | Select | Required | Allowed values (months): `12`, `36`, `60`, `84`, `120`, `180`, `240`, `360` | 360 | Dataset A: `Loan_Amount_Term`, Dataset C: `Loan_Tenure` | Eligibility, Risk Tier |
| 5 | Loan Purpose | `loan_purpose` | Select | Required | Allowed: `home`, `education`, `personal`, `business`, `vehicle`, `medical` | home | — (context) | Report, Recommendation |

---

### Section 4 — Credit Profile & KYC Gates

| # | User Label | Internal Name | Data Type | Required | Validation Rules | Example Value | Dataset Source | Used By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 6 | PAN / Aadhaar | `national_id` | String | Required | Standard India ID format | ABCDE1234F | Intake | Bureau Gate |
| 7 | Age | `age` | Integer | Required | Min: 18, Max: 70 (Derived via KYC) | 34 | Dataset C: `Age` | Risk Tier, Archetype, Recommendation |
| 8 | Credit Score (CIBIL) | `credit_score` | Integer | Required | Min: 300, Max: 900 (Fetched via Bureau Gate, not user input) | 742 | Dataset C: `CIBIL_Score` | Risk Tier, Archetype, Recommendation |
| 9 | Credit History | `credit_history` | Select | Required | Allowed: `1` (meets guidelines), `0` (does not meet guidelines) | 1 | Dataset A: `Credit_History` | Eligibility |
| 10 | Existing Monthly EMI | `existing_emi` | Integer | Optional | Min: 0, Max: 1,000,000. Total of all current EMI payments. Enter 0 if no active loans. | 12000 | Dataset C: `Existing_EMI` | Risk Tier, Archetype, Recommendation |
| 11 | Number of Active Loans | `number_of_loans` | Integer | Optional | Min: 0, Max: 20 | 2 | Dataset C: `Number_of_Loans` | Risk Tier, Archetype, Recommendation |
| 12 | Months of Past Delinquency | `delinquent_months` | Integer | Optional | Min: 0, Max: 120. Number of months with missed or late payments in the last 5 years. | 0 | Dataset C: `Delinquent_Months` | Risk Tier, Archetype, Recommendation |
| 13 | Credit Utilization (%) | `credit_utilization` | Integer | Optional | Min: 0, Max: 100. Percentage of available credit currently used. | 35 | Dataset C: `Credit_Utilization` | Risk Tier, Archetype, Recommendation |

---

## Field Count Summary

| Category | Required | Optional | Total |
| :--- | :--- | :--- | :--- |
| Personal Information | 1 | 0 | 1 |
| Income and Assets | 1 | 0 | 1 |
| Loan Details | 3 | 0 | 3 |
| Credit Profile & KYC Gates | 4 | 4 | 8 |
| **Total** | **9** | **4** | **13** |

---

## Engine Coverage Map

This table confirms every engine has at least the minimum required fields to produce its output.

| Engine | Required Fields Used | Optional Fields Used |
| :--- | :--- | :--- |
| **Eligibility Engine** | `loan_amount`, `loan_term`, `credit_history` (3 fields) | — |
| **Risk Tier Engine** | `age`, `loan_amount`, `loan_term`, `credit_score` (4 fields) | `existing_emi`, `number_of_loans`, `delinquent_months`, `credit_utilization` (4 fields) |
| **Archetype Engine** | `age`, `loan_amount`, `credit_score` (3 fields) | `existing_emi`, `number_of_loans`, `delinquent_months`, `credit_utilization` (4 fields) |
| **Recommendation Engine** | `loan_amount`, `credit_score` (2 fields) | `existing_emi`, `number_of_loans`, `delinquent_months`, `credit_utilization` (4 fields) |
| **PDF Report Engine** | `full_name` + all assessment outputs | All fields included in report |

*(Note: Income integers for the Optimization Engine are derived post-verification via Account Aggregator, superseding the categorical `income_bracket` used during Triage.)*

---

## Default Values for Optional Fields

When an optional field is omitted, the backend applies these defaults during preprocessing:

| Field | Default Value | Rationale |
| :--- | :--- | :--- |
| `existing_emi` | `0` | Assume no current EMI obligations |
| `number_of_loans` | `0` | Assume no active loans |
| `delinquent_months` | `0` | Assume clean payment history |
| `credit_utilization` | `30` | Industry median utilization |

---

## Frontend Grouping

Fields should be presented to the user in four sections matching the table structure above:

1. **Personal Information** — Quick demographic capture (Age is strictly hidden)
2. **Income & Assets** — Financial standing (Brackets only)
3. **Loan Details** — What they are applying for
4. **Credit Profile** — Bureau and repayment history (Fetched post PAN input)

This ordering follows a natural progression from "who are you" → "what do you earn" → "what do you want" → "what is your credit history."
