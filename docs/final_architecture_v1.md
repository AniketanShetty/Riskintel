# RiskIntel — Final Architecture V1.1

**Status:** FROZEN — V1.1 Architecture
**Date:** 2026-06-05
**Revision:** V1.1 — Updated per Principal ML Engineer review (sync with `IMPLEMENTATION_ROADMAP.md` V1.1 and `docs/output_contracts.md` V1.1). Added `bias` output to E1, removed `cibil_score`/`Credit_Score` from E3 inputs, and updated E6 to use macro-categories.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [User Types](#user-types)
3. [Engine Definitions](#engine-definitions)
4. [Data Flow](#data-flow)
5. [ML vs Rule-Based Decisions](#ml-vs-rule-based-decisions)
6. [Dataset-to-Engine Mapping](#dataset-to-engine-mapping)
7. [Engine Specifications](#engine-specifications)
8. [Known Limitations](#known-limitations)
9. [Decision Log](#decision-log)

---

## System Overview

RiskIntel is a Loan Decision Support System with two distinct user workflows:

- **Person A** — Credit-aware borrower with existing CIBIL score and credit history. Receives eligibility assessment, risk tier, borrower archetype, and personalized recommendations.
- **Person B** — New-to-credit (NTC) borrower with no bureau history. Receives a readiness score, livelihood archetype, and actionable guidance.

The system is designed as a set of **stateless engines** orchestrated by a Flask API, with a Vite/React frontend and PDF report generation via ReportLab.

---

## User Types

### Person A — Credit-Aware Borrower

| Item | Detail |
| :--- | :--- |
| **Input source** | Web form (17 fields) |
| **Engines triggered** | Eligibility → Risk Tier → Borrower Archetype → Recommendation |
| **Primary output** | Eligibility verdict, Risk Tier (P1–P4), Archetype label, Action plan |
| **Report** | PDF with all outputs, strengths, risk factors, recommendations |

### Person B — New-to-Credit Borrower

| Item | Detail |
| :--- | :--- |
| **Input source** | Web form (20 fields) |
| **Engines triggered** | Readiness → Livelihood Archetype → Recommendation |
| **Primary output** | Readiness Score (0–100), Readiness Band, Livelihood Archetype label |
| **Report** | PDF with readiness breakdown, archetype context, improvement steps |

---

## Engine Definitions

RiskIntel V1 contains **six engines**. Each engine is a self-contained module that receives a Python dict and returns a result dict. No engine has side effects. No engine depends on another engine's internal state.

| # | Engine | Type | Person | Dataset |
| :--- | :--- | :--- | :--- | :--- |
| E1 | Eligibility Engine | ML — Binary Classification | A | `loan_approval_dataset.csv` |
| E2 | Risk Tier Engine | Rule-Based — Threshold Logic | A | Derived from `External_Cibil_Dataset.csv` analysis |
| E3 | Borrower Archetype Engine | ML — K-Means Clustering | A | `External_Cibil_Dataset.csv` |
| E4 | Recommendation Engine | Rule-Based — Deterministic Logic | A + B | No dataset — consumes outputs from other engines |
| E5 | Readiness Engine | Rule-Based — Weighted Scoring | B | `RuralCreditData.csv` |
| E6 | Livelihood Archetype Engine | ML — K-Means Clustering | B | `RuralCreditData.csv` |

---

## Data Flow

### Person A Pipeline

```
User Form (17 fields)
    │
    ├──► [E1] Eligibility Engine
    │         Input:  no_of_dependents, education, self_employed,
    │                 income_annum, loan_amount, loan_term,
    │                 cibil_score, residential_assets_value,
    │                 commercial_assets_value, luxury_assets_value,
    │                 bank_asset_value
    │         Output: eligibility_verdict, approval_probability,
    │                 bias, feature_contributions
    │
    ├──► [E2] Risk Tier Engine
    │         Input:  cibil_score
    │         Output: risk_tier (P1/P2/P3/P4), tier_description
    │
    ├──► [E3] Borrower Archetype Engine
    │         Input:  income (monthly, derived from annual), age, gender,
    │                 education, marital_status, years_at_current_employer
    │         Output: archetype_label, archetype_description,
    │                 cluster_id
    │
    └──► [E4] Recommendation Engine
              Input:  eligibility_verdict, risk_tier, archetype_label,
                      bias (from E1), feature_contributions (from E1),
                      raw user inputs
              Output: strengths[], risk_factors[],
                      recommendations[], action_plan[]
                      │
                      ▼
                  PDF Report
```

### Person B Pipeline

```
User Form (20 fields)
    │
    ├──► [E5] Readiness Engine
    │         Input:  annual_income, monthly_expenses, loan_amount,
    │                 home_ownership, type_of_house, house_area,
    │                 sanitary_availability, water_availabity,
    │                 young_dependents, old_dependents, occupants_count,
    │                 primary_business, secondary_business,
    │                 loan_purpose, loan_tenure, loan_installments
    │         Output: readiness_score (0-100), readiness_band,
    │                 component_scores{}
    │
    ├──► [E6] Livelihood Archetype Engine
    │         Input:  primary_business, secondary_business,
    │                 annual_income, monthly_expenses,
    │                 loan_amount, loan_purpose,
    │                 home_ownership, type_of_house
    │         Output: archetype_label, archetype_description,
    │                 cluster_id
    │
    └──► [E4] Recommendation Engine
              Input:  readiness_score, readiness_band,
                      component_scores, archetype_label,
                      raw user inputs
              Output: strengths[], improvement_areas[],
                      recommendations[], next_steps[]
                      │
                      ▼
                  PDF Report
```

---

## ML vs Rule-Based Decisions

### E1 — Eligibility Engine: ML (Binary Classification)

**Decision:** Use supervised ML.

**Why ML:** The dataset (`loan_approval_dataset.csv`) has a binary target (`loan_status`: Approved / Rejected) with 11 usable features. This is a standard classification problem. A Random Forest baseline can learn non-linear interactions between income, assets, CIBIL score, and loan parameters that a simple rule set cannot capture.

**Why not rule-based:** Loan approval decisions involve multi-factor interactions. A person with low income but high assets and excellent CIBIL might still be approved. Hard-coded rules cannot capture these interactions without manually enumerating all edge cases, which defeats the purpose.

**Model:** Random Forest Classifier. No hyperparameter tuning in V1.

---

### E2 — Risk Tier Engine: Rule-Based (Threshold Logic)

**Decision:** Use rule-based threshold logic. No ML model.

**Why rule-based:** The validated experiment proved that `Approved_Flag` (P1/P2/P3/P4) in the CIBIL dataset can be reconstructed from `Credit_Score` alone with **99.56% accuracy**. The target is a deterministic discretization of the credit score with minimal exceptions.

The discovered thresholds are:

| Tier | Credit Score Range | Interpretation |
| :--- | :--- | :--- |
| P1 | ≥ 701 | Lowest risk — premium borrower |
| P2 | 669 – 700 | Moderate risk — standard borrower |
| P3 | 659 – 668 | Elevated risk — borderline borrower |
| P4 | ≤ 658 | Highest risk — high-risk borrower |

**Why not ML:** Training an ML model to predict a rule-based output is wasteful. It adds model serialization, loading, and prediction overhead to do what a 4-line `if/elif` block does with higher transparency. An ML model here would be a cosmetic wrapper around threshold logic. The project gains more credibility by recognizing this and choosing the right tool.

**P3 note:** P3 showed overlap with other tiers in the original data (score range 489–776). However, the IQR (Q1=662, Q3=667) confirms that the vast majority of P3 cases fall in a narrow score band between P2 and P4. The rule-based engine handles the core band. The small number of P3 outliers at extreme scores (likely flagged by other bureau conditions in the original bank's process) are an accepted limitation of the simplified engine.

---

### E3 — Borrower Archetype Engine: ML (K-Means Clustering)

**Decision:** Use unsupervised ML (K-Means).

**Why ML:** Archetypes answer "what kind of borrower is this?" — a question about natural groupings, not prediction. Clustering discovers these groupings from data rather than hardcoding them. Different clusters will naturally emerge along dimensions of income stability, credit behavior, age, and employment tenure.

**Why clustering is justified here but not for Risk Tier:** Risk Tier has a known answer (credit score thresholds). Archetypes do not. We need the data to tell us what borrower profiles exist. This is the correct use case for unsupervised learning.

**Features:** NETMONTHLYINCOME, AGE, EDUCATION (encoded), MARITALSTATUS (encoded), GENDER (encoded), Time_With_Curr_Empr (Credit_Score excluded in V1.1 to prevent redundancy with Risk Tier).

**Cluster count:** To be determined during implementation via Elbow Method / Silhouette Score. Expected: 3–5 clusters.

**Expected archetype labels (post-hoc, based on centroids):**

| Expected Label | Anticipated Profile |
| :--- | :--- |
| Stable Established | High score, long tenure, moderate income |
| High-Income Premium | High score, high income, shorter tenure |
| Young Professional | Lower age, moderate score, short tenure |
| Credit-Stressed | Low score, low income, short tenure |

Labels are finalized after inspecting actual cluster centroids during implementation.

---

### E4 — Recommendation Engine: Rule-Based (Deterministic)

**Decision:** Rule-based. No ML model.

**Why rule-based:** Recommendations must be deterministic, auditable, and explainable. An ML model that "predicts" recommendations would be a black box generating advice with no traceable rationale.

**How recommendations are generated:**

For Person A:
1. **Strengths** — Derived from positive feature contributions in the Eligibility Engine's output. If `cibil_score` contributed positively → "Strong credit history."
2. **Risk Factors** — Derived from negative feature contributions. If `loan_amount` relative to `income_annum` is unfavorable → "Loan-to-income ratio is high."
3. **Tier-specific advice** — Mapped from Risk Tier. P3/P4 → "Focus on improving CIBIL score above 700." P1 → "You qualify for competitive rates."
4. **Archetype-specific context** — Mapped from Archetype label. "Credit-Stressed" → "Consider debt consolidation before applying."

For Person B:
1. **Component-based feedback** — The Readiness Engine returns sub-scores per component (Financial Health, Housing Stability, etc.). Any sub-score below 50 → specific improvement advice for that component.
2. **Archetype context** — "Agri Livelihood" → advice tailored to agricultural borrowers (crop insurance, SHG membership).
3. **Readiness band advice** — "Needs Improvement" → prioritized action list.

**Why not feature importance for recommendations:** Feature importance from a Random Forest measures how much a feature reduces impurity during splits. A feature can be "important" to the model but completely non-actionable to the user (e.g., `age`). Recommendations must be anchored to things the user can change: reduce loan amount, improve credit score, increase savings. This requires domain logic, not model statistics.

---

### E5 — Readiness Engine: Rule-Based (Weighted Scoring)

**Decision:** Weighted composite scoring formula. No ML model.

**Why not ML:** There is no target variable in `RuralCreditData.csv`. No column says "approved" or "rejected." Without a target, supervised learning is impossible. Fabricating a synthetic target would be dishonest and produce unreliable predictions.

**Why not clustering:** Readiness is a continuous scale measuring preparedness on known dimensions. Clustering produces discrete groups, which is less informative. We know *what* to measure (financial health, housing stability, infrastructure access). We just need to score it.

**Scoring framework:**

| Component | Weight | Inputs | Scoring Logic |
| :--- | :--- | :--- | :--- |
| Financial Health | 35% | `annual_income`, `monthly_expenses`, `loan_amount` | Income-to-expense ratio, loan-to-income ratio. Higher ratio = higher sub-score. |
| Housing Stability | 20% | `home_ownership`, `type_of_house`, `house_area` | Owned (1.0) scores higher. T1 > T2 > R. Larger area contributes positively. |
| Infrastructure Access | 15% | `sanitary_availability`, `water_availabity` | Sum of available amenities scaled to 0–100. |
| Household Burden | 15% | `old_dependents`, `young_dependents`, `occupants_count` | Fewer dependents per unit income = higher sub-score. |
| Business Viability | 15% | `primary_business`, `secondary_business`, `loan_purpose` | Purpose-business alignment bonus. Having secondary income source = bonus. |

**Output:** Readiness Score (0–100) + Readiness Band.

| Score Range | Band |
| :--- | :--- |
| 75–100 | Ready |
| 50–74 | Moderately Ready |
| 25–49 | Needs Improvement |
| 0–24 | Not Ready |

---

### E6 — Livelihood Archetype Engine: ML (K-Means Clustering)

**Decision:** Use unsupervised ML (K-Means).

**Why ML:** We need to discover natural groupings in livelihood patterns. The dataset has 30+ primary business types and 37 loan purpose categories — manual grouping would be arbitrary. Clustering finds coherent groups based on actual data patterns.

**Features:** primary_business (macro-categorized & encoded), annual_income, monthly_expenses, loan_amount, loan_purpose (macro-categorized & encoded), home_ownership, type_of_house (encoded).

**Cluster count:** Determined via Elbow Method. Expected: 4–6 clusters.

**Expected archetype labels (post-hoc):**

| Expected Label | Anticipated Profile |
| :--- | :--- |
| Agri Livelihood | Agriculture/livestock primary, crop-related loans, lower income |
| Micro-Retail | Tailoring/grocery/vendor, small loans, working capital focus |
| Artisan Producer | Handloom/handicrafts, moderate income, equipment loans |
| Service/Wage Worker | Daily wage/services, lowest income, highest expense ratio |

---

## Dataset-to-Engine Mapping

| Dataset | File | Engine(s) | Usage |
| :--- | :--- | :--- | :--- |
| **A** | `loan_approval_dataset.csv` | E1 (Eligibility) | Train binary classifier. 11 features → approval probability. |
| **C-ext** | `External_Cibil_Dataset.csv` | E2 (Risk Tier), E3 (Archetype) | E2: Validated Credit_Score thresholds. E3: Cluster on 6 user-knowable features (Credit_Score excluded). |
| **C-int** | `Internal_Bank_Dataset.csv` | — | Not used in V1. Bureau-internal data that users cannot provide. Retained for future bank-side deployment. |
| **B** | `RuralCreditData.csv` | E5 (Readiness), E6 (Livelihood Archetype) | E5: Weighted scoring using all 16 usable columns. E6: Cluster on 7 livelihood features. |

**Why Internal_Bank_Dataset is excluded from V1:**
All 26 columns are bank-internal trade line data (Total_TL, Tot_Active_TL, Auto_TL, CC_TL, etc.). A user filling out a web form cannot provide any of these values. Including this dataset would require either: (a) simulating bureau data, which is dishonest, or (b) building a bank-employee-only interface, which is out of V1 scope. The dataset is preserved in `data/raw/` for future versions where bank-side integration may be implemented.

---

## Inputs and Outputs Summary

### Person A — Inputs (17 fields)

| Section | Field | Maps To | Engine |
| :--- | :--- | :--- | :--- |
| Identity | `full_name` | Report only | PDF |
| Identity | `age` | C-ext: `AGE` | E3 |
| Identity | `gender` | C-ext: `GENDER` | E3 |
| Identity | `marital_status` | C-ext: `MARITALSTATUS` | E3 |
| Profile | `dependents` | A: `no_of_dependents` | E1 |
| Profile | `education` | A: `education`, C-ext: `EDUCATION` | E1, E3 |
| Profile | `self_employed` | A: `self_employed` | E1 |
| Profile | `years_at_current_employer` | C-ext: `Time_With_Curr_Empr` | E3 |
| Income | `annual_income` | A: `income_annum`, C-ext: `NETMONTHLYINCOME` (÷12) | E1, E3 |
| Assets | `residential_assets_value` | A: `residential_assets_value` | E1 |
| Assets | `commercial_assets_value` | A: `commercial_assets_value` | E1 |
| Assets | `luxury_assets_value` | A: `luxury_assets_value` | E1 |
| Assets | `bank_asset_value` | A: `bank_asset_value` | E1 |
| Loan | `loan_amount` | A: `loan_amount` | E1 |
| Loan | `loan_term` | A: `loan_term` | E1 |
| Loan | `loan_purpose` | Context | E4 |
| Credit | `cibil_score` | A: `cibil_score`, C-ext: `Credit_Score` | E1, E2 |

### Person A — Outputs

| Engine | Output | Format |
| :--- | :--- | :--- |
| E1 | Eligibility Verdict | `Highly Likely` / `Likely` / `Borderline` / `Unlikely` |
| E1 | Approval Probability | Float 0.0 – 1.0 |
| E1 | Bias | Float (base prediction rate) |
| E1 | Feature Contributions | Dict of feature → contribution |
| E2 | Risk Tier | `P1` / `P2` / `P3` / `P4` |
| E2 | Tier Description | String |
| E3 | Borrower Archetype | String label |
| E3 | Archetype Description | String |
| E4 | Strengths | List of strings |
| E4 | Risk Factors | List of strings |
| E4 | Recommendations | List of strings |
| E4 | Action Plan | List of prioritized steps |

### Person B — Inputs (20 fields)

| Section | Field | Maps To | Engine |
| :--- | :--- | :--- | :--- |
| Identity | `full_name` | Report only | PDF |
| Identity | `age` | B: `age` | E5, E6 |
| Identity | `gender` | B: `sex` | E5, E6 |
| Livelihood | `primary_business` | B: `primary_business` | E5, E6 |
| Livelihood | `secondary_business` (opt) | B: `secondary_business` | E5, E6 |
| Livelihood | `annual_income` | B: `annual_income` | E5, E6 |
| Livelihood | `monthly_expenses` | B: `monthly_expenses` | E5, E6 |
| Loan | `loan_amount` | B: `loan_amount` | E5 |
| Loan | `loan_purpose` | B: `loan_purpose` | E5, E6 |
| Loan | `loan_tenure` | B: `loan_tenure` | E5 |
| Loan | `loan_installments` | B: `loan_installments` | E5 |
| Dependents | `young_dependents` | B: `young_dependents` | E5 |
| Dependents | `old_dependents` | B: `old_dependents` | E5 |
| Dependents | `occupants_count` | B: `occupants_count` | E5 |
| Housing | `home_ownership` | B: `home_ownership` (binary 0/1) | E5, E6 |
| Housing | `type_of_house` | B: `type_of_house` (T1/T2/R) | E5, E6 |
| Housing | `house_area` (opt) | B: `house_area` | E5 |
| Infra | `sanitary_availability` | B: `sanitary_availability` (binary 0/1) | E5 |
| Infra | `water_availability` | B: `water_availabity` (0/0.5/1) | E5 |
| Context | `social_class` (opt) | B: `social_class` | E6 |

### Person B — Outputs

| Engine | Output | Format |
| :--- | :--- | :--- |
| E5 | Readiness Score | Integer 0–100 |
| E5 | Readiness Band | `Ready` / `Moderately Ready` / `Needs Improvement` / `Not Ready` |
| E5 | Component Scores | Dict of component → sub-score |
| E6 | Livelihood Archetype | String label |
| E6 | Archetype Description | String |
| E4 | Strengths | List of strings |
| E4 | Improvement Areas | List of strings |
| E4 | Recommendations | List of strings |
| E4 | Next Steps | List of prioritized steps |

---

## Known Limitations

### L1 — Dataset A Is Synthetic

`loan_approval_dataset.csv` shows clear signs of synthetic generation: zero missing values, near-perfect 50/50 category splits, uniformly distributed loan terms, 28 negative values in `residential_assets_value`. The Eligibility Engine trained on this data will not generalize to real-world loan applications. This is an accepted V1 limitation for a portfolio/college project.

### L2 — Risk Tier Thresholds Are Dataset-Specific

The P1–P4 thresholds derived from `External_Cibil_Dataset.csv` reflect one institution's scoring policy. Different banks use different cutoffs. The rule-based engine is transparent about this — thresholds are configurable constants, not hidden inside a model.

### L3 — P3 Tier Has Overlap

In the original dataset, P3 had a credit score range of 489–776, overlapping with all other tiers. The IQR analysis showed that the core P3 band is 662–667. The rule-based engine captures this core band but cannot replicate the original institution's secondary criteria for outlier P3 cases. Approximately 0.5% of cases may be misclassified between P1 and P3.

### L4 — Borrower Archetypes Are Descriptive, Not Prescriptive

Archetype labels are assigned post-hoc after cluster inspection. They describe observed patterns, not ground-truth categories. A borrower labeled "Credit-Stressed" is not guaranteed to be stressed — the label reflects statistical similarity to other borrowers in that cluster.

### L5 — Person B Readiness Score Is Not an Approval Prediction

The Readiness Score is a weighted composite formula, not a model prediction. A score of 80 does NOT mean "80% chance of approval." It means the applicant demonstrates strong preparedness across financial, housing, and infrastructure dimensions. This distinction must be communicated clearly in the UI and PDF report.

### L6 — Internal_Bank_Dataset Is Unused in V1

26 columns of bank-internal trade line data are excluded because users cannot provide this data through a web form. This reduces the information available to the system but maintains the user-facing design principle.

### L7 — Rural Dataset Category Simplification

`RuralCreditData.csv` contains 30+ primary business types and 37 loan purpose categories. The frontend will present grouped/simplified categories and map them to the original values during preprocessing. Some information loss is accepted for usability.

### L8 — No Temporal Validation

All models use random train/test splits. No time-based validation is performed because none of the datasets contain timestamps. This means the models cannot be validated for temporal stability (concept drift). Accepted for V1.

---

## Decision Log

Every architectural decision and why it was made.

| # | Decision | Rationale |
| :--- | :--- | :--- |
| D1 | Eligibility Engine uses ML (Random Forest) | Binary target exists. Multi-factor interactions justify ML over rules. |
| D2 | Risk Tier Engine is rule-based, not ML | Approved_Flag is a deterministic discretization of Credit_Score (99.56% accuracy from score alone). ML adds complexity with no benefit. |
| D3 | Borrower Archetype uses K-Means clustering | Archetypes are emergent groupings — no pre-defined categories. Clustering is the correct tool for discovery. |
| D4 | Recommendation Engine is rule-based | Recommendations must be deterministic, auditable, and anchored to actionable factors. ML predictions of advice are not interpretable. |
| D5 | Readiness Engine uses weighted scoring, not ML | No target variable exists in the rural dataset. Weighted scoring is honest; fabricating a target would be dishonest. |
| D6 | Livelihood Archetype uses K-Means clustering | 30+ business types and 37 purposes require data-driven grouping. Manual categorization would be arbitrary. |
| D7 | Internal_Bank_Dataset excluded from V1 | All columns are bureau-internal and cannot be collected from users via web form. |
| D8 | Recommendations use domain rules, not feature importance | Feature importance measures model behavior, not user actionability. `age` can be "important" to a model but the user cannot change their age. |
| D9 | Person A form rewritten to match actual dataset columns | Previous spec mapped to a different Kaggle dataset. 5 fields referenced non-existent columns. |
| D10 | Person B form corrected for invented fields | `has_electricity`, `has_road`, `has_internet` do not exist in the rural dataset. `home_ownership` is binary, not categorical. `type_of_house` values are T1/T2/R, not pucca/semi_pucca/kucha. |
| D11 | income_annum used instead of monthly income for Dataset A | The actual column is annual income (mean ₹50.6L). Frontend collects annual, backend uses as-is for E1 and divides by 12 for E3 (NETMONTHLYINCOME). |
| D12 | No deep learning models | Largest dataset is 51K rows. Random Forest / Gradient Boosting will match or exceed deep learning performance with better interpretability and faster training. |
| D13 | No LLM-generated recommendations | Rule-based recommendations are deterministic, free, and auditable. LLMs add cost, latency, and non-determinism. |
| D14 | PDF reports via ReportLab | Industry-standard Python library for financial PDFs. No external API dependencies. |
| D15 | SQLite for persistence | V1 scope does not require concurrent write access. SQLite minimizes deployment complexity. |

---

## Technology Stack (V1)

| Layer | Technology |
| :--- | :--- |
| Frontend | Vite + React |
| Backend | FastAPI (Python) |
| ML Models | scikit-learn (Random Forest, K-Means) |
| PDF Generation | ReportLab |
| Database | SQLite (canonical V1 — see D15; Postgres was considered and rejected for V1) |
| Model Serialization | joblib |

---

## What This Architecture Does NOT Include (By Design)

- ❌ Real-time bureau API integration
- ❌ User authentication / login system
- ❌ Model retraining pipeline
- ❌ A/B testing framework
- ❌ Multi-language support
- ❌ Mobile application
- ❌ Admin dashboard for bank employees (V2 candidate)
- ❌ Model monitoring / drift detection

These are explicitly deferred. They are not forgotten — they are out of scope for V1.

---

## V1 Architecture is Frozen

This document represents the final architectural specification for RiskIntel V1. All implementation work should reference this document. Any proposed changes require updating this document first with justification.
