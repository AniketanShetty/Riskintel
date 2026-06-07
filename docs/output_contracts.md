# RiskIntel — Output Contracts V1.1

**Status:** FROZEN — defines all API response shapes before implementation.
**Date:** 2026-06-05
**Revision:** V1.1 — Added `bias` field to eligibility response per `treeinterpreter` integration.
**Reference:** `docs/final_architecture_v1.md`

---

## Purpose

This document specifies the exact JSON shape of every API response and internal payload in RiskIntel V1. Frontend development, backend implementation, and PDF report generation must all conform to these contracts. Any change to a contract requires updating this document first.

All fields marked **Required** will always be present in the response. Fields marked **Conditional** appear only under stated conditions.

---

## 1. Person A — API Response

**Endpoint:** `POST /api/assess/person-a`
**HTTP Status:** `200 OK`

```json
{
  "status": "success",
  "user_type": "person_a",
  "timestamp": "2026-06-05T11:40:00Z",
  "correlation_id": "c8b417bd-316f-47ed-bbda-39d23db9bd34",
  "applicant": {
    "full_name": "Aniket Sharma",
    "age": 34,
    "gender": "M",
    "marital_status": "Married",
    "education": "Graduate",
    "self_employed": "No",
    "years_at_current_employer": 6,
    "annual_income": 9600000,
    "dependents": 2,
    "cibil_score": 742,
    "loan_amount": 15000000,
    "loan_term": 12,
    "loan_purpose": "home",
    "residential_assets_value": 5600000,
    "commercial_assets_value": 3700000,
    "luxury_assets_value": 8800000,
    "bank_asset_value": 3300000
  },
  "eligibility": {
    "verdict": "Highly Likely",
    "probability": 0.91,
    "bias": 0.50,
    "feature_contributions": {
      "cibil_score": 0.15,
      "annual_income": 0.08,
      "loan_amount": -0.04,
      "residential_assets_value": 0.06,
      "commercial_assets_value": 0.04,
      "luxury_assets_value": 0.05,
      "bank_asset_value": 0.03,
      "education": 0.02,
      "self_employed": 0.01,
      "dependents": -0.01,
      "loan_term": 0.02
    }
  },
  "risk_tier": {
    "tier": "P1",
    "label": "Low Risk",
    "description": "Premium borrower. Credit score indicates strong repayment reliability.",
    "score_used": 742,
    "thresholds": {
      "P1": "≥ 701",
      "P2": "669 – 700",
      "P3": "659 – 668",
      "P4": "≤ 658"
    }
  },
  "archetype": {
    "label": "Stable Established",
    "description": "High credit score, long employment tenure, moderate-to-high income. Represents a reliable, low-risk borrower profile.",
    "cluster_id": 0
  },
  "recommendations": {
    "strengths": [
      "Strong CIBIL score (742) well above the P1 threshold.",
      "High total asset value provides strong collateral backing.",
      "Stable employment history with 6 years at current employer."
    ],
    "risk_factors": [
      "Loan-to-income ratio is moderately high at 1.56x annual income."
    ],
    "recommendations": [
      "Consider reducing the loan amount or extending the loan term to improve the debt-to-income ratio.",
      "Maintain current credit behavior to preserve P1 tier status."
    ],
    "action_plan": [
      "1. Review if a lower loan amount meets your requirements.",
      "2. Compare loan terms — a longer term reduces monthly EMI burden.",
      "3. Avoid new credit enquiries before final application."
    ]
  }
}
```

### Field Specifications — Person A Response

#### Root Level

| Field | Type | Required | Allowed Values | Description |
| :--- | :--- | :--- | :--- | :--- |
| `status` | string | Required | `"success"` | Response status |
| `user_type` | string | Required | `"person_a"` | Fixed identifier |
| `timestamp` | string | Required | ISO 8601 format | Server timestamp of assessment |
| `correlation_id` | string | Required | UUID | Unique identifier for tracing and audit logs |

#### `applicant` Object

Echo of the submitted form values. All 17 fields are returned exactly as received (after validation and whitespace trimming). This enables the PDF report to render the applicant's inputs without a second lookup.

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `full_name` | string | Required | Applicant name |
| `age` | integer | Required | 18–70 |
| `gender` | string | Required | `"M"`, `"F"`, `"Other"` |
| `marital_status` | string | Required | `"Married"`, `"Single"` |
| `education` | string | Required | `"Graduate"`, `"Not Graduate"` |
| `self_employed` | string | Required | `"Yes"`, `"No"` |
| `years_at_current_employer` | integer | Required | 0–50 |
| `annual_income` | integer | Required | Min 0 |
| `dependents` | integer | Required | 0–5 |
| `cibil_score` | integer | Required | 300–900 |
| `loan_amount` | integer | Required | Min 300,000 |
| `loan_term` | integer | Required | 2–20 (years) |
| `loan_purpose` | string | Required | `"home"`, `"education"`, `"personal"`, `"business"`, `"vehicle"`, `"medical"` |
| `residential_assets_value` | integer | Required | Min 0 |
| `commercial_assets_value` | integer | Required | Min 0 |
| `luxury_assets_value` | integer | Required | Min 0 |
| `bank_asset_value` | integer | Required | Min 0 |

#### `eligibility` Object

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `verdict` | string | Required | One of: `"Highly Likely"`, `"Likely"`, `"Borderline"`, `"Unlikely"` |
| `probability` | float | Required | Range: 0.00 – 1.00. Model's predicted probability of approval. |
| `bias` | float | Required | Base prediction rate from the training set. Represents the model's default prediction before considering this specific applicant's features. Provided by `treeinterpreter`. |
| `feature_contributions` | object | Required | Key-value map of feature name → contribution score. Computed by `treeinterpreter` per-prediction path decomposition. Positive values push toward approval, negative toward rejection. All 11 model features included. Invariant: `bias + Σ(feature_contributions) = probability`. |

**Verdict mapping from probability:**

| Probability Range | Verdict |
| :--- | :--- |
| ≥ 0.80 | Highly Likely |
| 0.60 – 0.79 | Likely |
| 0.40 – 0.59 | Borderline |
| < 0.40 | Unlikely |

#### `risk_tier` Object

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `tier` | string | Required | One of: `"P1"`, `"P2"`, `"P3"`, `"P4"` |
| `label` | string | Required | Human-readable tier label |
| `description` | string | Required | 1–2 sentence explanation of what this tier means |
| `score_used` | integer | Required | The CIBIL score that determined the tier |
| `thresholds` | object | Required | The threshold ranges for all 4 tiers — provides transparency |

**Tier labels:**

| Tier | Label |
| :--- | :--- |
| P1 | Low Risk |
| P2 | Moderate Risk |
| P3 | Elevated Risk |
| P4 | High Risk |

#### `archetype` Object

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `label` | string | Required | Human-readable archetype name (determined post-clustering) |
| `description` | string | Required | 1–2 sentence profile description |
| `cluster_id` | integer | Required | Internal cluster index (0-based). Used for debugging, not displayed to user. |

#### `recommendations` Object

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `strengths` | string[] | Required | 1–5 positive observations about the applicant's profile. Never empty. |
| `risk_factors` | string[] | Required | 0–5 negative observations. May be empty if no risk factors identified. |
| `recommendations` | string[] | Required | 1–5 actionable suggestions. Never empty. |
| `action_plan` | string[] | Required | 1–5 numbered, prioritized steps the applicant can take. Never empty. |

---

## 2. Person B — API Response

**Endpoint:** `POST /api/assess/person-b`
**HTTP Status:** `200 OK`

```json
{
  "status": "success",
  "user_type": "person_b",
  "timestamp": "2026-06-05T11:40:00Z",
  "correlation_id": "c8b417bd-316f-47ed-bbda-39d23db9bd34",
  "applicant": {
    "full_name": "Ramesh Kumar",
    "age": 42,
    "gender": "M",
    "primary_business": "Tailoring",
    "secondary_business": "none",
    "annual_income": 120000,
    "monthly_expenses": 8000,
    "loan_amount": 50000,
    "loan_purpose": "Apparels",
    "loan_tenure": 12,
    "loan_installments": 12,
    "young_dependents": 3,
    "old_dependents": 1,
    "occupants_count": 6,
    "home_ownership": 1,
    "type_of_house": "T2",
    "house_area": 450,
    "sanitary_availability": 1,
    "water_availability": 0.5,
    "social_class": "OBC"
  },
  "readiness": {
    "score": 68,
    "band": "Moderately Ready",
    "components": {
      "financial_health": {
        "score": 72,
        "weight": 0.35,
        "factors": {
          "income_expense_ratio": 1.25,
          "loan_income_ratio": 0.42
        }
      },
      "housing_stability": {
        "score": 75,
        "weight": 0.20,
        "factors": {
          "home_ownership": "Owned",
          "house_type": "Semi-Permanent",
          "house_area": 450
        }
      },
      "infrastructure_access": {
        "score": 75,
        "weight": 0.15,
        "factors": {
          "sanitary_availability": true,
          "water_availability": "Partial"
        }
      },
      "household_burden": {
        "score": 45,
        "weight": 0.15,
        "factors": {
          "total_dependents": 4,
          "dependents_per_income_unit": 0.033
        }
      },
      "business_viability": {
        "score": 70,
        "weight": 0.15,
        "factors": {
          "primary_business": "Tailoring",
          "has_secondary_income": false,
          "purpose_alignment": "Aligned"
        }
      }
    }
  },
  "archetype": {
    "label": "Micro-Retail",
    "description": "Small-scale retail or services-based livelihood with modest income and working capital needs.",
    "cluster_id": 2
  },
  "recommendations": {
    "strengths": [
      "Owns home — strong stability indicator.",
      "Loan-to-income ratio is manageable at 0.42x annual income.",
      "Loan purpose is well-aligned with primary business."
    ],
    "improvement_areas": [
      "High dependent burden (4 dependents) relative to income.",
      "No secondary income source — single point of failure.",
      "Only partial water availability — infrastructure gap."
    ],
    "recommendations": [
      "Explore a secondary income source to diversify household revenue.",
      "Consider Self Help Group (SHG) membership for microfinance access.",
      "Ensure loan installments align with seasonal income patterns."
    ],
    "next_steps": [
      "1. Join or form a local SHG if not already a member.",
      "2. Document 6 months of income records to strengthen future applications.",
      "3. Explore government schemes for sanitation and water access improvement."
    ]
  }
}
```

### Field Specifications — Person B Response

#### Root Level

| Field | Type | Required | Allowed Values | Description |
| :--- | :--- | :--- | :--- | :--- |
| `status` | string | Required | `"success"` | Response status |
| `user_type` | string | Required | `"person_b"` | Fixed identifier |
| `timestamp` | string | Required | ISO 8601 format | Server timestamp of assessment |
| `correlation_id` | string | Required | UUID | Unique identifier for tracing and audit logs |

#### `applicant` Object

Echo of the submitted form values. All 20 fields returned as received.

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `full_name` | string | Required | Applicant name |
| `age` | integer | Required | 18–70 |
| `gender` | string | Required | `"M"`, `"F"`, `"Other"` |
| `primary_business` | string | Required | One of the business categories from the dataset |
| `secondary_business` | string | Required | Business category or `"none"` |
| `annual_income` | integer | Required | Min 0 |
| `monthly_expenses` | integer | Required | Min 0 |
| `loan_amount` | integer | Required | Min 100 |
| `loan_purpose` | string | Required | One of the 37 purpose categories from the dataset |
| `loan_tenure` | integer | Required | Months |
| `loan_installments` | integer | Required | Number of installments |
| `young_dependents` | integer | Required | 0–15 |
| `old_dependents` | integer | Required | 0–10 |
| `occupants_count` | integer | Required | Min 1 |
| `home_ownership` | integer | Required | `1` (owned), `0` (not owned) |
| `type_of_house` | string | Required | `"T1"` (permanent), `"T2"` (semi-permanent), `"R"` (temporary) |
| `house_area` | integer | Conditional | Present only if provided. Min 50. |
| `sanitary_availability` | integer | Required | `1` (available), `0` (not available) |
| `water_availability` | float | Required | `0.0` (none), `0.5` (partial), `1.0` (full) |
| `social_class` | string | Conditional | Present only if provided |

#### `readiness` Object

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `score` | integer | Required | 0–100. Weighted composite of component scores. |
| `band` | string | Required | One of: `"Ready"`, `"Moderately Ready"`, `"Needs Improvement"`, `"Not Ready"` |
| `components` | object | Required | Breakdown of 5 scoring components (see below) |

**Band mapping:**

| Score Range | Band |
| :--- | :--- |
| 75–100 | Ready |
| 50–74 | Moderately Ready |
| 25–49 | Needs Improvement |
| 0–24 | Not Ready |

#### `readiness.components` — Each Component

Every component has the same shape:

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `score` | integer | Required | 0–100. Component sub-score. |
| `weight` | float | Required | Component weight in final score (sums to 1.0 across all 5). |
| `factors` | object | Required | Key-value pairs showing the raw values or ratios used to compute this sub-score. Content varies per component. |

**Component names and weights:**

| Component Key | Weight | Description |
| :--- | :--- | :--- |
| `financial_health` | 0.35 | Income-to-expense ratio, loan-to-income ratio |
| `housing_stability` | 0.20 | Ownership status, house type, house area |
| `infrastructure_access` | 0.15 | Sanitation and water availability |
| `household_burden` | 0.15 | Dependents relative to income |
| `business_viability` | 0.15 | Business type, secondary income, purpose alignment |

#### `archetype` Object

Same shape as Person A archetype.

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `label` | string | Required | Livelihood archetype label |
| `description` | string | Required | 1–2 sentence profile description |
| `cluster_id` | integer | Required | Internal cluster index (0-based) |

#### `recommendations` Object

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `strengths` | string[] | Required | 1–5 positive observations. Never empty. |
| `improvement_areas` | string[] | Required | 0–5 areas needing improvement. May be empty. |
| `recommendations` | string[] | Required | 1–5 actionable suggestions. Never empty. |
| `next_steps` | string[] | Required | 1–5 numbered, prioritized steps. Never empty. |

**Note:** Person B uses `improvement_areas` instead of Person A's `risk_factors`. This is intentional — Person B is not being risk-assessed, so the language shifts from "risk" to "improvement."

---

## 3. PDF Report Payload

**Endpoint:** `POST /api/report/generate`
**HTTP Status:** `200 OK`
**Response Content-Type:** `application/pdf`

The PDF endpoint does not return JSON. It returns a binary PDF file. However, internally, the report engine receives a structured payload that combines the assessment response with report metadata.

### Internal Report Payload (Backend Only)

```json
{
  "report_metadata": {
    "report_id": "RI-20260605-A-00142",
    "generated_at": "2026-06-05T11:40:00Z",
    "user_type": "person_a",
    "version": "1.0"
  },
  "applicant": { },
  "eligibility": { },
  "risk_tier": { },
  "archetype": { },
  "recommendations": { }
}
```

The `applicant`, `eligibility`, `risk_tier`, `archetype`, and `recommendations` objects are **identical** to the corresponding objects in the Person A or Person B API response. No transformation is applied — the report engine renders the same data that the frontend received.

### Report Metadata

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `report_id` | string | Required | Format: `RI-YYYYMMDD-{A|B}-{5-digit-sequence}`. Example: `RI-20260605-A-00142` |
| `generated_at` | string | Required | ISO 8601 timestamp |
| `user_type` | string | Required | `"person_a"` or `"person_b"` |
| `version` | string | Required | Report template version. Fixed at `"1.0"` for V1. |

### PDF Content Sections

The generated PDF contains these sections in order:

**Person A Report:**

| Section | Content Source | Description |
| :--- | :--- | :--- |
| Header | `report_metadata` | Report ID, date, RiskIntel branding |
| Applicant Summary | `applicant` | Name, demographics, income, loan details |
| Eligibility Assessment | `eligibility` | Verdict, probability bar chart, feature contribution chart |
| Risk Tier | `risk_tier` | Tier badge (P1–P4), description, threshold table |
| Borrower Profile | `archetype` | Archetype label, description |
| Strengths | `recommendations.strengths` | Bulleted list |
| Risk Factors | `recommendations.risk_factors` | Bulleted list with warning icons |
| Recommendations | `recommendations.recommendations` | Numbered list |
| Action Plan | `recommendations.action_plan` | Numbered steps with checkboxes |
| Disclaimer | Static text | "This report is for informational purposes only..." |

**Person B Report:**

| Section | Content Source | Description |
| :--- | :--- | :--- |
| Header | `report_metadata` | Report ID, date, RiskIntel branding |
| Applicant Summary | `applicant` | Name, demographics, livelihood, loan details |
| Readiness Assessment | `readiness` | Score gauge (0–100), band label |
| Component Breakdown | `readiness.components` | 5 component scores displayed as progress bars |
| Livelihood Profile | `archetype` | Archetype label, description |
| Strengths | `recommendations.strengths` | Bulleted list |
| Improvement Areas | `recommendations.improvement_areas` | Bulleted list with improvement icons |
| Recommendations | `recommendations.recommendations` | Numbered list |
| Next Steps | `recommendations.next_steps` | Numbered steps with checkboxes |
| Disclaimer | Static text | "This report is for informational purposes only..." |

### Report API Response Headers

| Header | Value |
| :--- | :--- |
| `Content-Type` | `application/pdf` |
| `Content-Disposition` | `attachment; filename="RiskIntel_Report_{report_id}.pdf"` |

---

## 4. Recommendation Payload

The Recommendation Engine (E4) is called internally by the backend after the other engines complete. It is not a separate API endpoint. Its input and output contracts are defined here for implementation clarity.

### E4 Input — Person A

```json
{
  "user_type": "person_a",
  "eligibility_verdict": "Highly Likely",
  "approval_probability": 0.91,
  "bias": 0.50,
  "feature_contributions": {
    "cibil_score": 0.32,
    "annual_income": 0.18,
    "loan_amount": -0.07,
    "residential_assets_value": 0.12,
    "commercial_assets_value": 0.08,
    "luxury_assets_value": 0.10,
    "bank_asset_value": 0.06,
    "education": 0.04,
    "self_employed": 0.01,
    "dependents": -0.02,
    "loan_term": 0.03
  },
  "risk_tier": "P1",
  "archetype_label": "Stable Established",
  "applicant": {
    "annual_income": 9600000,
    "loan_amount": 15000000,
    "cibil_score": 742,
    "loan_purpose": "home"
  }
}
```

### E4 Input — Person B

```json
{
  "user_type": "person_b",
  "readiness_score": 68,
  "readiness_band": "Moderately Ready",
  "component_scores": {
    "financial_health": 72,
    "housing_stability": 75,
    "infrastructure_access": 75,
    "household_burden": 45,
    "business_viability": 70
  },
  "archetype_label": "Micro-Retail",
  "applicant": {
    "primary_business": "Tailoring",
    "annual_income": 120000,
    "monthly_expenses": 8000,
    "loan_amount": 50000,
    "loan_purpose": "Apparels",
    "young_dependents": 3,
    "old_dependents": 1,
    "home_ownership": 1,
    "sanitary_availability": 1,
    "water_availability": 0.5
  }
}
```

### E4 Output

The output shape differs by user type:

**Person A:**

| Field | Type | Min Items | Max Items |
| :--- | :--- | :--- | :--- |
| `strengths` | string[] | 1 | 5 |
| `risk_factors` | string[] | 0 | 5 |
| `recommendations` | string[] | 1 | 5 |
| `action_plan` | string[] | 1 | 5 |

**Person B:**

| Field | Type | Min Items | Max Items |
| :--- | :--- | :--- | :--- |
| `strengths` | string[] | 1 | 5 |
| `improvement_areas` | string[] | 0 | 5 |
| `recommendations` | string[] | 1 | 5 |
| `next_steps` | string[] | 1 | 5 |

### Recommendation Generation Rules

**Strengths** are generated from:
- Feature contributions > 0 (Person A)
- Component scores ≥ 70 (Person B)
- Positive raw input signals (e.g., home ownership, high credit score)

**Risk Factors / Improvement Areas** are generated from:
- Feature contributions < 0 (Person A)
- Component scores < 50 (Person B)
- Concerning ratios (e.g., loan-to-income > 3x, high dependents-per-income)

**Recommendations** are mapped from a static rule table:

| Trigger | Recommendation |
| :--- | :--- |
| CIBIL < 700 | "Work on improving your credit score by ensuring timely payments." |
| Loan-to-income > 3x | "Consider reducing the loan amount or increasing income sources." |
| No secondary income (Person B) | "Explore a secondary income source to diversify revenue." |
| Low infrastructure (Person B) | "Explore government schemes for infrastructure improvement." |
| High dependent burden | "Plan for dependent-related expenses before taking on new debt." |

The rule table is exhaustive and maintained as a configuration file, not hardcoded in logic.

---

## 5. Error Response Payload

All errors return a consistent JSON shape regardless of the error type.

**HTTP Status:** `4xx` or `5xx`

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "One or more input fields failed validation.",
    "details": [
      {
        "field": "cibil_score",
        "value": 950,
        "rule": "max:900",
        "message": "CIBIL score must be between 300 and 900."
      },
      {
        "field": "annual_income",
        "value": -50000,
        "rule": "min:0",
        "message": "Annual income cannot be negative."
      }
    ]
  }
}
```

### Error Response Fields

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `status` | string | Required | Always `"error"` |
| `error.code` | string | Required | Machine-readable error code (see table below) |
| `error.message` | string | Required | Human-readable summary |
| `error.details` | array | Conditional | Present only for `VALIDATION_ERROR`. Contains per-field errors. |

### Error Codes

| Code | HTTP Status | When |
| :--- | :--- | :--- |
| `VALIDATION_ERROR` | 400 | One or more form fields fail validation rules |
| `MISSING_REQUIRED_FIELD` | 400 | A required field is absent from the request body |
| `INVALID_USER_TYPE` | 400 | `user_type` is not `"person_a"` or `"person_b"` |
| `MODEL_NOT_LOADED` | 503 | ML model files not found or failed to deserialize |
| `ENGINE_FAILURE` | 500 | An engine threw an unhandled exception during processing |
| `REPORT_GENERATION_FAILED` | 500 | PDF generation failed |
| `INTERNAL_ERROR` | 500 | Catch-all for unexpected server errors |

### Validation Error Detail Object

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `field` | string | Required | The internal field name that failed |
| `value` | any | Required | The value that was submitted |
| `rule` | string | Required | The validation rule that was violated (e.g., `"min:300"`, `"required"`, `"one_of:M,F,Other"`) |
| `message` | string | Required | Human-readable explanation of the violation |

### Example Error Responses

**Missing required field:**
```json
{
  "status": "error",
  "error": {
    "code": "MISSING_REQUIRED_FIELD",
    "message": "Required field 'cibil_score' is missing from the request."
  }
}
```

**Model not loaded:**
```json
{
  "status": "error",
  "error": {
    "code": "MODEL_NOT_LOADED",
    "message": "The Eligibility Engine model could not be loaded. Ensure model files exist in the models/ directory."
  }
}
```

**Engine failure:**
```json
{
  "status": "error",
  "error": {
    "code": "ENGINE_FAILURE",
    "message": "The Readiness Engine encountered an unexpected error during scoring.",
    "details": [
      {
        "engine": "readiness",
        "error_type": "ZeroDivisionError",
        "context": "monthly_expenses was 0, causing division by zero in income_expense_ratio calculation."
      }
    ]
  }
}
```

---

## Contract Versioning

All API responses include implicit version tracking through the report metadata version field (`"version": "1.0"`). If the response shape changes in a future version:

1. Update this document.
2. Increment the version string.
3. Maintain backward compatibility for one version cycle (frontend must handle both old and new shapes during transition).

---

## Frontend Consumption Notes

The frontend should:

1. **Check `status` first.** If `"error"`, display the `error.message` and any `details[].message` values. Do not attempt to render assessment data.
2. **Never hardcode tier/band labels.** Always read `risk_tier.label` and `readiness.band` from the response. This allows backend label changes without frontend redeployment.
3. **Render `feature_contributions` as a horizontal bar chart.** Positive values on the right (green), negative values on the left (red). Sorted by absolute magnitude.
4. **Render `readiness.components` as progress bars.** Each bar shows 0–100 with the weight displayed alongside.
5. **Use `thresholds` from `risk_tier` to render a visual scale.** Show where the applicant's score falls relative to all tier boundaries.

---

## Output Contracts Are Frozen

These contracts define the agreement between the backend and frontend teams. Implementation must conform to these shapes. Any deviation requires updating this document first with justification.
