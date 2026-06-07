# RiskIntel — Dataset Documentation

This document describes the three datasets used in RiskIntel, their contents, purpose, and mapping to system engines.

---

## Dataset A — Loan Approval Prediction Dataset

**Source:** Kaggle — Loan Eligibility Prediction

**Purpose:** Eligibility Assessment for Person A workflow.

**Target Variable:** `Loan_Status` (Approved / Not Approved)

### Features

| Feature | Type | Description |
| :--- | :--- | :--- |
| `Gender` | Categorical | Male / Female |
| `Married` | Categorical | Yes / No |
| `Dependents` | Categorical | 0, 1, 2, 3+ |
| `Education` | Categorical | Graduate / Not Graduate |
| `Self_Employed` | Categorical | Yes / No |
| `ApplicantIncome` | Numeric | Primary applicant income |
| `CoapplicantIncome` | Numeric | Co-applicant income |
| `LoanAmount` | Numeric | Requested loan amount (thousands) |
| `Loan_Amount_Term` | Numeric | Term of loan (months) |
| `Credit_History` | Binary | 1 = meets guidelines, 0 = does not |
| `Property_Area` | Categorical | Urban / Semiurban / Rural |
| `Loan_Status` | Binary (Target) | Y = Approved, N = Not Approved |

### Engine Mapping

| Engine | How Dataset A is Used |
| :--- | :--- |
| Eligibility Engine | Train binary classifier to predict Loan_Status |

### Known Characteristics

- Credit_History is a strong predictor of Loan_Status.
- Class imbalance may exist (more approvals than rejections).
- Missing values present in LoanAmount, Self_Employed, and other fields.

### File Placement

```
data/raw/dataset_a.csv        → Raw download
data/processed/dataset_a.csv  → Cleaned version
```

---

## Dataset B — RuralCreditData

**Source:** Kaggle — Credit/Loan Dataset - Rural India

**Purpose:** Readiness Assessment for Person B (New-To-Credit) workflow.

**Target Variable:** None (no approval labels). Used for scoring and archetype derivation.

### Features

| Feature | Type | Description |
| :--- | :--- | :--- |
| `age` | Numeric | Age of applicant |
| `sex` | Categorical | Male / Female |
| `social_class` | Categorical | Social classification |
| `primary_business` | Categorical | Main occupation or business type |
| `secondary_business` | Categorical | Secondary source of income |
| `annual_income` | Numeric | Total annual income |
| `monthly_expenses` | Numeric | Average monthly expenses |
| `old_dependents` | Numeric | Number of elderly dependents |
| `young_dependents` | Numeric | Number of young dependents |
| `home_ownership` | Categorical | Owned / Rented / Other |
| `type_of_house` | Categorical | Pucca / Semi-Pucca / Kucha |
| `house_area` | Numeric | Area of dwelling |
| `loan_purpose` | Categorical | Purpose of requested loan |
| `loan_amount` | Numeric | Requested loan amount |
| Various amenity flags | Binary | Electricity, water, road, etc. |

### Engine Mapping

| Engine | How Dataset B is Used |
| :--- | :--- |
| Readiness Engine | Derive Readiness Score (0–100) from income, expenses, housing, infrastructure features |
| Livelihood Archetype Engine | Cluster or classify borrowers by business type, income pattern, and infrastructure |

### Known Characteristics

- No approval labels — cannot train a supervised approval classifier.
- Contains rich livelihood and infrastructure data suitable for scoring and clustering.
- Focused on rural and semi-urban populations.

### File Placement

```
data/raw/dataset_b.csv        → Raw download
data/processed/dataset_b.csv  → Cleaned version
```

---

## Dataset C — Leading Indian Bank + CIBIL Dataset

**Source:** Kaggle — Leading Indian Bank Dataset with CIBIL features

**Purpose:** Risk Tier Analysis, Borrower Archetype Identification, and Recommendation Engine for Person A.

**Target Variable:** `Approved_Flag` (binary approval indicator)

### Features

| Feature | Type | Description |
| :--- | :--- | :--- |
| `CIBIL_Score` / `credit_score` | Numeric | Bureau credit score (300–900) |
| `Income` | Numeric | Annual income |
| `Loan_Amount` | Numeric | Requested amount |
| `Loan_Tenure` | Numeric | Loan duration |
| `Existing_EMI` | Numeric | Current monthly EMI obligations |
| `Number_of_Loans` | Numeric | Active loan count |
| `Delinquent_Months` | Numeric | Months of delinquency |
| `Credit_Utilization` | Numeric | Credit utilization ratio |
| `Asset_Value` | Numeric | Total asset value |
| `Age` | Numeric | Applicant age |
| `Approved_Flag` | Binary (Target) | Approval outcome |

> **Note:** Feature names may vary by the specific dataset version. The above represents typical fields found in this dataset family.

### Engine Mapping

| Engine | How Dataset C is Used |
| :--- | :--- |
| Risk Tier Engine | Classify into P1/P2/P3/P4 using credit score, EMI, utilization, delinquency |
| Borrower Archetype Engine | Cluster borrowers by financial behavior patterns |
| Recommendation Engine | Extract feature importance to generate strengths, risk factors, and action plan |

### Known Characteristics

- `Approved_Flag` is highly correlated with CIBIL Score.
- Risk Tier is treated as a risk-grade signal, not a default probability.
- Rich credit-behavior features enable meaningful archetype clustering.

### File Placement

```
data/raw/dataset_c.csv        → Raw download
data/processed/dataset_c.csv  → Cleaned version
```

---

## Dataset-to-Engine Summary

```
Dataset A ──▶ Eligibility Engine (Person A)

Dataset B ──▶ Readiness Engine (Person B)
         ──▶ Livelihood Archetype Engine (Person B)

Dataset C ──▶ Risk Tier Engine (Person A)
         ──▶ Borrower Archetype Engine (Person A)
         ──▶ Recommendation Engine (Person A)
```
