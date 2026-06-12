# Person B — Input Field Specifications

**Workflow:** New-To-Credit (NTC) Borrower

**Engines Served:**
- Readiness Engine (Dataset B)
- Livelihood Archetype Engine (Dataset B)
- Recommendation Engine (derived from Dataset B features)

---

## Design Rationale

Person B has no meaningful credit history and no reliable bureau score. The form collects:

1. **Livelihood and income data** — feeds the Readiness Engine to calculate a score (0–100) and the Livelihood Archetype Engine to classify the borrower profile.
2. **Housing and infrastructure data** — captures stability signals that influence readiness scoring and recommendation generation.

No credit-bureau fields are collected. No approval probability is generated. The system assesses **readiness**, not **creditworthiness**.

*Note: Per V2 Constitution, exact numeric income, monthly expenses, direct dependent counting, and sole earner status are explicitly banned. Income is collected as a broad bracket for Triage, expenses are derived via Pincode baseline. Age is strictly derived via KYC, not manual input.*

---

## Field Definitions

### Section 1 — Personal Information

| # | User Label | Internal Name | Data Type | Required | Validation Rules | Example Value | Dataset Source | Used By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Full Name | `full_name` | String | Required | Min 2 chars, max 100 chars. Letters, spaces, periods only. | Ramesh Kumar | — (report only) | PDF Report Engine |

---

### Section 2 — Livelihood Details

| # | User Label | Internal Name | Data Type | Required | Validation Rules | Example Value | Dataset Source | Used By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2 | Income Bracket | `income_bracket` | Select | Required | Standard predefined ranges. | 10k-20k | Intake | Triage Engine |

---

### Section 3 — Loan Details

| # | User Label | Internal Name | Data Type | Required | Validation Rules | Example Value | Dataset Source | Used By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 3 | Loan Amount Requested | `loan_amount` | Integer | Required | Min: 1,000, Max: 5,000,000 | 50000 | Dataset B: `loan_amount` | Readiness, Recommendation |
| 4 | Loan Purpose | `loan_purpose` | Select | Required | Allowed: `business_expansion`, `working_capital`, `equipment_purchase`, `crop_inputs`, `livestock_purchase`, `home_improvement`, `education`, `medical` | working_capital | Dataset B: `loan_purpose` | Readiness, Archetype, Recommendation |

---

### Section 4 — Housing Information

| # | User Label | Internal Name | Data Type | Required | Validation Rules | Example Value | Dataset Source | Used By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 5 | Pincode | `pincode` | String | Required | 6-digit valid Indian Pincode | 411001 | Intake | Triage Engine |

---

## Dynamic Stage 2 Verification Fields

If Triage passes and the borrower proceeds to `Pending Verification` (Field Visit), the Field Officer CRM explicitly collects the following:

| # | Field | Type | Note |
| :--- | :--- | :--- | :--- |
| V1 | `secondary_contact_number` | String | Strictly for skip-tracing/fraud detection; banned as a qualitative trust metric. |
| V2 | `fo_visit_photo_hash` | String | Geotagged photo hash for anti-collusion audit trail. |
| V3 | `verified_monthly_cash_income` | Integer | Destroy the intake bracket constraint. |
| V4 | `vintage_artifact_type` | Select | Used to anchor business vintage math (e.g., `merchant_qr`, `municipal_license`, `none`). |
| V5 | `vintage_artifact_issue_date`| Date | Used to calculate `business_vintage_months`. |

---

## Field Count Summary

| Category | Required | Optional | Total |
| :--- | :--- | :--- | :--- |
| Personal Information | 1 | 0 | 1 |
| Livelihood Details | 1 | 0 | 1 |
| Loan Details | 2 | 0 | 2 |
| Housing Information | 1 | 0 | 1 |
| **Total** | **5** | **0** | **5** |

---

## Engine Coverage Map

This table confirms every engine has at least the minimum required fields to produce its output.

| Engine | Required Fields Used | Optional Fields Used |
| :--- | :--- | :--- |
| **Readiness Engine** | `age` (derived), `loan_amount`, `loan_purpose` (3 fields) | — |
| **Livelihood Archetype Engine** | `age` (derived), `loan_purpose` (2 fields) | — |
| **Recommendation Engine** | `loan_amount`, `loan_purpose` (2 fields) | — |
| **PDF Report Engine** | `full_name` + all assessment outputs | All fields included in report |

---

## Derived Features (Computed by Backend)

These features are calculated from raw inputs during preprocessing. They are not collected from the user.

| Derived Feature | Formula | Used By |
| :--- | :--- | :--- |
| `age` | Extracted from KYC (PAN/Aadhaar) | Readiness, Archetype |
| `monthly_living_cost` | `Base_Poverty_Line * Pincode_Tier_Multiplier` | Triage, Optimization |
| `business_vintage_months` | `Current_Date - vintage_artifact_issue_date` (0 if artifact is none) | Livelihood Resilience |

---

## Frontend Grouping

Fields should be presented to the user in five sections matching the table structure above:

1. **Personal Information** — Basic identity (Age is strictly hidden)
2. **Livelihood Details** — How they earn
3. **Loan Details** — What they need
4. **Housing Information** — Stability indicators

*(Note: Monthly expenses, direct dependents, sole earner status, and explicit age are banned. The UI must not ask these questions.)*
