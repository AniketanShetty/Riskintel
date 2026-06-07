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

Fields are designed to be accessible to rural and semi-urban applicants with limited financial literacy. Labels use plain language. Infrastructure fields use checkboxes rather than requiring exact values.

---

## Field Definitions

### Section 1 — Personal Information

| # | User Label | Internal Name | Data Type | Required | Validation Rules | Example Value | Dataset Source | Used By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Full Name | `full_name` | String | Required | Min 2 chars, max 100 chars. Letters, spaces, periods only. | Ramesh Kumar | — (report only) | PDF Report Engine |
| 2 | Age | `age` | Integer | Required | Min: 18, Max: 70 | 42 | Dataset B: `age` | Readiness, Archetype |
| 3 | Gender | `gender` | Select | Required | Allowed: `male`, `female`, `other` | male | Dataset B: `sex` | Readiness, Archetype |

---

### Section 2 — Livelihood Details

| # | User Label | Internal Name | Data Type | Required | Validation Rules | Example Value | Dataset Source | Used By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 4 | Primary Occupation / Business | `primary_business` | Select | Required | Allowed: `agriculture`, `livestock`, `retail_shop`, `handicrafts`, `food_processing`, `transport`, `services`, `daily_wage`, `other` | agriculture | Dataset B: `primary_business` | Readiness, Archetype, Recommendation |
| 5 | Secondary Income Source | `secondary_business` | Select | Optional | Allowed: `agriculture`, `livestock`, `retail_shop`, `handicrafts`, `food_processing`, `transport`, `services`, `daily_wage`, `none`, `other` | livestock | Dataset B: `secondary_business` | Readiness, Archetype |
| 6 | Annual Household Income | `annual_income` | Integer | Required | Min: 0, Max: 5,000,000 | 120000 | Dataset B: `annual_income` | Readiness, Archetype, Recommendation |
| 7 | Average Monthly Expenses | `monthly_expenses` | Integer | Required | Min: 0, Max: 500,000 | 8000 | Dataset B: `monthly_expenses` | Readiness, Recommendation |

---

### Section 3 — Loan Details

| # | User Label | Internal Name | Data Type | Required | Validation Rules | Example Value | Dataset Source | Used By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 8 | Loan Amount Requested | `loan_amount` | Integer | Required | Min: 1,000, Max: 5,000,000 | 50000 | Dataset B: `loan_amount` | Readiness, Recommendation |
| 9 | Loan Purpose | `loan_purpose` | Select | Required | Allowed: `business_expansion`, `working_capital`, `equipment_purchase`, `crop_inputs`, `livestock_purchase`, `home_improvement`, `education`, `medical` | working_capital | Dataset B: `loan_purpose` | Readiness, Archetype, Recommendation |

---

### Section 4 — Dependents

| # | User Label | Internal Name | Data Type | Required | Validation Rules | Example Value | Dataset Source | Used By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 10 | Young Dependents (under 18) | `young_dependents` | Integer | Required | Min: 0, Max: 15 | 3 | Dataset B: `young_dependents` | Readiness, Recommendation |
| 11 | Elderly Dependents (above 60) | `old_dependents` | Integer | Required | Min: 0, Max: 10 | 1 | Dataset B: `old_dependents` | Readiness, Recommendation |

---

### Section 5 — Housing Information

| # | User Label | Internal Name | Data Type | Required | Validation Rules | Example Value | Dataset Source | Used By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 12 | Home Ownership | `home_ownership` | Select | Required | Allowed: `owned`, `rented`, `employer_provided`, `family_shared` | owned | Dataset B: `home_ownership` | Readiness, Archetype, Recommendation |
| 13 | Type of House | `type_of_house` | Select | Required | Allowed: `pucca` (permanent), `semi_pucca` (semi-permanent), `kucha` (temporary) | semi_pucca | Dataset B: `type_of_house` | Readiness, Archetype |
| 14 | House Area (sq ft) | `house_area` | Integer | Optional | Min: 50, Max: 10,000 | 450 | Dataset B: `house_area` | Readiness |

---

### Section 6 — Infrastructure Access

| # | User Label | Internal Name | Data Type | Required | Validation Rules | Example Value | Dataset Source | Used By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 15 | Has Electricity | `has_electricity` | Checkbox | Required | Allowed: `true`, `false` | true | Dataset B: amenity flags | Readiness, Archetype, Recommendation |
| 16 | Has Piped Water Supply | `has_water` | Checkbox | Required | Allowed: `true`, `false` | false | Dataset B: amenity flags | Readiness, Archetype, Recommendation |
| 17 | Has Road Connectivity | `has_road` | Checkbox | Required | Allowed: `true`, `false` | true | Dataset B: amenity flags | Readiness, Archetype |
| 18 | Has Internet Access | `has_internet` | Checkbox | Required | Allowed: `true`, `false` | false | Dataset B: amenity flags | Readiness, Archetype |

---

## Field Count Summary

| Category | Required | Optional | Total |
| :--- | :--- | :--- | :--- |
| Personal Information | 3 | 0 | 3 |
| Livelihood Details | 3 | 1 | 4 |
| Loan Details | 2 | 0 | 2 |
| Dependents | 2 | 0 | 2 |
| Housing Information | 2 | 1 | 3 |
| Infrastructure Access | 4 | 0 | 4 |
| **Total** | **16** | **2** | **18** |

---

## Engine Coverage Map

This table confirms every engine has at least the minimum required fields to produce its output.

| Engine | Required Fields Used | Optional Fields Used |
| :--- | :--- | :--- |
| **Readiness Engine** | `age`, `gender`, `primary_business`, `annual_income`, `monthly_expenses`, `loan_amount`, `loan_purpose`, `young_dependents`, `old_dependents`, `home_ownership`, `type_of_house`, `has_electricity`, `has_water`, `has_road`, `has_internet` (15 fields) | `secondary_business`, `house_area` (2 fields) |
| **Livelihood Archetype Engine** | `age`, `gender`, `primary_business`, `annual_income`, `loan_purpose`, `home_ownership`, `type_of_house`, `has_electricity`, `has_water`, `has_road`, `has_internet` (11 fields) | `secondary_business` (1 field) |
| **Recommendation Engine** | `primary_business`, `annual_income`, `monthly_expenses`, `loan_amount`, `loan_purpose`, `young_dependents`, `old_dependents`, `home_ownership`, `has_electricity`, `has_water`, `has_internet` (11 fields) | — |
| **PDF Report Engine** | `full_name` + all assessment outputs | All fields included in report |

---

## Default Values for Optional Fields

When an optional field is omitted, the backend applies these defaults during preprocessing:

| Field | Default Value | Rationale |
| :--- | :--- | :--- |
| `secondary_business` | `none` | Assume single income source |
| `house_area` | Median from Dataset B training data | Imputed from dataset distribution |

---

## Derived Features (Computed by Backend)

These features are calculated from raw inputs during preprocessing. They are not collected from the user.

| Derived Feature | Formula | Used By |
| :--- | :--- | :--- |
| `total_dependents` | `young_dependents + old_dependents` | Readiness, Recommendation |
| `income_expense_ratio` | `annual_income / (monthly_expenses × 12)` | Readiness, Recommendation |
| `loan_income_ratio` | `loan_amount / annual_income` | Readiness, Recommendation |
| `infrastructure_score` | Count of `true` values across `has_electricity`, `has_water`, `has_road`, `has_internet` (0–4) | Readiness, Archetype |
| `disposable_income` | `(annual_income / 12) - monthly_expenses` | Readiness, Recommendation |

---

## Frontend Grouping

Fields should be presented to the user in six sections matching the table structure above:

1. **Personal Information** — Basic identity
2. **Livelihood Details** — How they earn
3. **Loan Details** — What they need
4. **Dependents** — Financial obligations
5. **Housing Information** — Stability indicators
6. **Infrastructure Access** — Checkboxes for basic amenities

This ordering follows a natural progression from "who are you" → "how do you earn" → "what do you need" → "who depends on you" → "where do you live" → "what infrastructure do you have."

---

## Important Notes

- **No credit score field.** Person B is new-to-credit. No bureau data is collected or assumed.
- **No approval probability output.** Readiness ≠ Approval. The system assesses preparedness, not creditworthiness.
- **Checkbox UX for infrastructure.** Binary flags are presented as checkboxes to minimize input effort for users who may have limited digital literacy.
