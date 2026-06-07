# RiskIntel — Data Decisions

**Author Role:** Senior Data Scientist / Credit Risk Architect
**Date:** 2026-06-05
**Status:** Authoritative — supersedes assumptions in all prior documents

---

## Purpose

This document records every dataset-to-engine mapping decision, justifies each choice, identifies critical data issues, and corrects errors discovered in the existing form specifications. It is based on direct inspection of the actual CSV files present in `data/raw/`.

---

## Datasets Verified

| ID | File | Rows | Cols | Target | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| A | `loan_approval_dataset.csv` | 4,269 | 13 | `loan_status` (Approved / Rejected) | Usable — synthetic, simple features |
| C-ext | `External_Cibil_Dataset.csv` | 51,336 | 62 | `Approved_Flag` (P1 / P2 / P3 / P4) | Usable — rich bureau data |
| C-int | `Internal_Bank_Dataset.csv` | 51,336 | 26 | None (joins to C-ext via PROSPECTID) | Usable — paired with C-ext |
| B | `RuralCreditData.csv` | 40,000 | 21 | None | Usable — livelihood + housing data |

**Discarded files:** `BOB.csv`, `bob_df.csv`, `IDBI.csv`, `idbi_df.csv`, `PNB1.csv`, `pnb_df.csv`, `Syndicate.csv`, `syndicate_df.csv`, `combined_df.csv`, `states.csv`, `states_df.csv`, `test_modified.csv`, `train_modified.csv`, `Unseen_Dataset.csv`, `myFunction.py`. These are either NPA/defaulter lists from individual banks, pre-processed intermediary files, or encoding-corrupted files. None contain loan applicant features suitable for prediction engines.

---

## Critical Finding 1 — Approved_Flag Is Already the Risk Tier

The `External_Cibil_Dataset.csv` target column `Approved_Flag` is **not binary**. It contains four classes:

| Value | Count | % | Interpretation |
| :--- | :--- | :--- | :--- |
| P1 | 5,803 | 11.3% | Lowest risk |
| P2 | 32,199 | 62.7% | Moderate risk |
| P3 | 7,452 | 14.5% | Elevated risk |
| P4 | 5,882 | 11.5% | Highest risk |

**Credit Score distribution by tier:**

| Tier | Mean Score | Min | Max |
| :--- | :--- | :--- | :--- |
| P1 | 716 | 701 | 811 |
| P2 | 683 | 669 | 700 |
| P3 | 667 | 489 | 776 |
| P4 | 646 | 469 | 658 |

**Impact:** The Risk Tier Engine does not need to invent tiers. The target IS the tier. This is a multi-class classification problem (4 classes), not a binary classification with post-hoc binning.

---

## Critical Finding 2 — The Current Form Spec Maps to a Different Dataset

The Person A form specification (`docs/forms/person_a_fields.md`) was written assuming the classic Kaggle "Loan Eligibility Prediction" dataset (Gender, Married, Credit_History, Property_Area, CoapplicantIncome). **That dataset does not exist in this repository.**

The actual `loan_approval_dataset.csv` contains completely different columns:

| Column in spec (assumed) | Exists? | Actual column in dataset |
| :--- | :--- | :--- |
| `Gender` | ❌ No | — |
| `Married` | ❌ No | — |
| `Credit_History` (binary) | ❌ No | — |
| `Property_Area` | ❌ No | — |
| `CoapplicantIncome` | ❌ No | — |
| `ApplicantIncome` | ❌ No | `income_annum` (annual, not monthly) |
| `LoanAmount` | ❌ Name differs | `loan_amount` |
| `Loan_Amount_Term` | ❌ Name differs | `loan_term` (values: 2–20, likely years) |
| `Dependents` | ❌ Name differs | `no_of_dependents` (values: 0–5, no "3+" category) |
| `Education` | ✅ Similar | `education` (Graduate / Not Graduate, with leading space) |
| `Self_Employed` | ✅ Similar | `self_employed` (Yes / No, with leading space) |
| — | ❌ Missing from spec | `cibil_score` (300–900) |
| — | ❌ Missing from spec | `residential_assets_value` |
| — | ❌ Missing from spec | `commercial_assets_value` |
| — | ❌ Missing from spec | `luxury_assets_value` |
| — | ❌ Missing from spec | `bank_asset_value` |

**Impact:** The entire Person A form specification must be rewritten. 5 fields reference columns that don't exist. 4 fields that DO exist in the dataset were omitted from the spec. Every "Dataset Source" mapping in the current spec is wrong.

---

## Critical Finding 3 — Person B Form Spec Invented Fields

The Person B form specification (`docs/forms/person_b_fields.md`) contains fields that do not exist in `RuralCreditData.csv`:

| Spec field | Exists in data? | Actual situation |
| :--- | :--- | :--- |
| `has_electricity` | ❌ No | No electricity column exists |
| `has_water` | ❌ Partial | `water_availabity` exists but is a float (0.0 / 0.5 / 1.0), not boolean |
| `has_road` | ❌ No | No road connectivity column exists |
| `has_internet` | ❌ No | No internet column exists |
| `home_ownership` as categorical | ❌ Wrong type | Actual is float: 1.0 (owned) / 0.0 (not owned) |
| `type_of_house` as pucca/semi_pucca/kucha | ❌ Wrong values | Actual values: T1 / T2 / R |
| `business_duration_months` | ❌ No | Does not exist in dataset |

**Fields in the dataset that were missed by the spec:**

| Dataset column | Type | Description |
| :--- | :--- | :--- |
| `city` | object | 4.66% missing — city/location |
| `social_class` | object | 13.14% missing — social classification |
| `occupants_count` | int64 | Number of occupants in household |
| `sanitary_availability` | float64 | 0.0 / 1.0 binary — sanitation access |
| `loan_tenure` | int64 | Loan tenure in months |
| `loan_installments` | int64 | Number of installments |

**The spec also underestimated category variety:**
- Actual `primary_business`: 30+ categories (Tailoring, Goat rearing, Cow Rearing, Handloom Work, etc.). Spec listed 9.
- Actual `loan_purpose`: 37 categories (Apparels, Agro Based Businesses, Animal husbandry, etc.). Spec listed 8.

---

## Critical Finding 4 — Dataset A Is Synthetic

Evidence that `loan_approval_dataset.csv` is synthetic/generated:

1. **0% missing values** across all 13 columns. Real financial data always has missing values.
2. **Near-perfect 50/50 splits**: Graduate (2,144) vs Not Graduate (2,125). Yes (2,150) vs No (2,119). This is statistically implausible in real data.
3. **Uniformly distributed `loan_term`**: Values 2,4,6,8,10,12,14,16,18,20 appear in nearly equal counts (~405–490 each). Real loan terms cluster heavily at 12, 60, 120, 180, 360 months.
4. **Leading spaces** in 12 of 13 column names — common in Kaggle-generated datasets.
5. **28 negative values** in `residential_assets_value` — physically impossible.
6. **Very high income values** — mean ₹50.6L annual, min ₹2L, max ₹99L. Uniformly distributed, not realistic.

**Impact:** The dataset is usable for building a working demo. It is NOT representative of real loan applicant distributions. Models trained on it will not generalize to real data. This is an accepted V1 limitation.

---

## Engine-to-Dataset Mapping

### Decision 1 — Eligibility Engine → `loan_approval_dataset.csv`

**Justification:**
- Has a binary approval target (`loan_status`: Approved / Rejected).
- Features are simple enough to collect from users: income, loan amount, CIBIL score, asset values, education, employment, dependents, loan term.
- Small dataset (4,269 rows) but sufficient for a binary classifier with 11 features.

**Model type:** Binary classification (Random Forest or Gradient Boosting).

**Features used:** `no_of_dependents`, `education`, `self_employed`, `income_annum`, `loan_amount`, `loan_term`, `cibil_score`, `residential_assets_value`, `commercial_assets_value`, `luxury_assets_value`, `bank_asset_value`.

**Target:** `loan_status` → Mapped to Eligibility: Highly Likely / Likely / Borderline / Unlikely based on predicted probability thresholds.

---

### Decision 2 — Risk Tier Engine → `External_Cibil_Dataset.csv` + `Internal_Bank_Dataset.csv` (joined)

**Justification:**
- `Approved_Flag` already contains P1/P2/P3/P4 — this IS the risk tier label.
- 88 features (62 external + 26 internal) joined on `PROSPECTID` (100% overlap, 51,336 rows).
- Rich bureau data enables meaningful 4-class risk separation.

**Model type:** Multi-class classification (P1/P2/P3/P4).

**The user-input problem:**
Most features in this dataset are bureau-derived (delinquency counts, DPD history, trade line counts, enquiry patterns, utilization percentages). A typical user does NOT know these values.

**Resolution:**
Only a subset of columns are user-knowable:

| User-knowable column | Source |
| :--- | :--- |
| `Credit_Score` | User knows their CIBIL score |
| `NETMONTHLYINCOME` | User knows their income |
| `AGE` | User knows their age |
| `GENDER` | User knows their gender |
| `EDUCATION` | User knows their education |
| `MARITALSTATUS` | User knows their marital status |
| `Time_With_Curr_Empr` | User knows years at current employer |

That is **7 features out of 88**. Two approaches exist:

**Approach A (Recommended for V1):** Train a simplified Risk Tier model on only these 7 user-knowable features. Accept reduced accuracy. This is honest — the model uses only what the user provides.

**Approach B (Future):** In a real deployment, bureau data would come from a CIBIL API. The full 88-feature model could then be used on the bank side. Out of scope for V1.

**Decision:** Use Approach A. Train on the 7 user-knowable features. Document the accuracy tradeoff.

---

### Decision 3 — Borrower Archetype Engine → `External_Cibil_Dataset.csv` + `Internal_Bank_Dataset.csv` (joined)

**Justification:**
- Same dataset as Risk Tier but used unsupervised.
- Behavioral patterns (utilization, enquiry hunger, delinquency patterns, trade line mix) naturally cluster into borrower types.

**Model type:** K-Means or Gaussian Mixture clustering on a feature subset.

**Clustering features (user-knowable subset for V1):**

| Feature | Why it's useful for archetypes |
| :--- | :--- |
| `Credit_Score` | Core creditworthiness indicator |
| `NETMONTHLYINCOME` | Economic capacity |
| `AGE` | Life stage signal |
| `EDUCATION` | Encoded ordinally |
| `Time_With_Curr_Empr` | Stability signal |

After clustering, assign human-readable labels based on cluster centroids:
- **Stable Borrower** — High score, long employment, moderate income
- **High-Income Established** — High score, high income
- **Credit-Seeking** — Lower score, multiple enquiries pattern
- **Credit-Stressed** — Low score, short employment

**Important:** Clustering is justified here because we are finding natural groupings in financial behavior to provide descriptive labels. We are NOT using clustering to bypass the absence of a target variable. The target (P1-P4) exists but describes risk, not behavioral type. Archetypes describe borrower profile, which is a different dimension.

---

### Decision 4 — Recommendation Engine → Derived (No Separate Dataset)

**Justification:**
The Recommendation Engine does not have its own model. It is a rule-based layer that consumes outputs from the other engines.

**Logic:**
1. From the Eligibility Engine: extract feature importance. If a feature (e.g., CIBIL score) has high negative contribution → it becomes a "Risk Factor" and generates an action ("Improve your credit score above 700").
2. From the Risk Tier Engine: the tier itself drives recommendations. P3/P4 → "Reduce existing debt obligations", "Avoid new credit enquiries".
3. From the Archetype Engine: the archetype label drives contextual advice. Credit-Stressed → "Consider debt consolidation".

**Strengths** = top positive feature contributions from the eligibility model.
**Risk Factors** = top negative feature contributions.
**Action Plan** = rule-mapped recommendations per risk factor + archetype-specific advice.

No ML model is needed. This is deliberate — recommendations should be interpretable and deterministic, not black-box predicted.

---

### Decision 5 — Readiness Engine → `RuralCreditData.csv`

**Justification:**
- Only dataset with NTC (new-to-credit) applicant features.
- Contains livelihood, housing, infrastructure, and loan data.
- No approval target exists.

**How it works without a target variable:**

The Readiness Score (0–100) is a **weighted composite score**, not a model prediction. This is the correct approach because:

1. There is no approval label to train on.
2. Fabricating a synthetic target (e.g., "approved if income > X") would be dishonest.
3. A weighted score with transparent components is more interpretable and more useful to the applicant.

**Scoring formula (designed, not learned):**

| Component | Weight | Inputs | Logic |
| :--- | :--- | :--- | :--- |
| Financial Health | 35% | `annual_income`, `monthly_expenses`, `loan_amount` | Income-to-expense ratio, loan-to-income ratio |
| Housing Stability | 20% | `home_ownership`, `type_of_house`, `house_area` | Owned > Rented. T1/T2 > R. Larger area = more stability |
| Infrastructure Access | 15% | `sanitary_availability`, `water_availabity` | Higher availability = higher sub-score |
| Household Burden | 15% | `old_dependents`, `young_dependents`, `occupants_count` | Fewer dependents relative to income = better |
| Business Viability | 15% | `primary_business`, `secondary_business`, `loan_purpose` alignment | Purpose-business alignment, secondary income bonus |

Each component produces a sub-score (0–100). The final Readiness Score = weighted average of sub-scores.

**Readiness Band mapping:**

| Score Range | Band |
| :--- | :--- |
| 75–100 | Ready |
| 50–74 | Moderately Ready |
| 25–49 | Needs Improvement |
| 0–24 | High Risk |

**Why not a classifier?** Because there is nothing to classify. The absence of a target is not a problem to solve — it is a constraint to respect. The score communicates preparedness honestly. Any attempt to predict "approval" without approval data would be fabrication.

---

### Decision 6 — Livelihood Archetype Engine → `RuralCreditData.csv`

**Justification:**
- Dataset contains rich livelihood data (30+ business types, income, expenses, loan purpose).
- Clustering is appropriate here because we want to discover natural groupings in livelihood patterns.

**Model type:** K-Means clustering.

**Clustering features:**

| Feature | Role |
| :--- | :--- |
| `primary_business` | Encoded — drives archetype category |
| `annual_income` | Economic scale |
| `monthly_expenses` | Cost burden |
| `loan_amount` | Capital need |
| `loan_purpose` | Encoded — business intent |
| `home_ownership` | Stability |
| `type_of_house` | Encoded — infrastructure level |

**Expected archetypes (to be validated against cluster centroids):**
- **Agri Livelihood** — Agriculture/livestock primary, crop/animal loan purpose, lower income
- **Micro-Retail** — Tailoring/grocery/vendor, small loan amounts, working capital purpose
- **Artisan Producer** — Handloom/handicrafts, moderate income, equipment-oriented loans
- **Service Worker** — Daily wage/services, lowest income, highest expense ratio

**Why clustering is justified here:** Unlike the Readiness Engine (where we know what dimension we're scoring on), archetypes are emergent — we don't know how many types exist or what defines them until we see the data. K-Means discovers these groupings. The labels are applied post-hoc based on centroid interpretation.

---

## Where Clustering Should and Should Not Be Used

| Engine | Clustering? | Justification |
| :--- | :--- | :--- |
| Eligibility Engine | ❌ No | Supervised — has binary target |
| Risk Tier Engine | ❌ No | Supervised — has 4-class target (P1-P4) |
| Borrower Archetype Engine | ✅ Yes | Unsupervised grouping on behavioral features |
| Recommendation Engine | ❌ No | Rule-based — no model |
| Readiness Engine | ❌ No | Weighted scoring — no target to predict, no groupings to find |
| Livelihood Archetype Engine | ✅ Yes | Unsupervised grouping on livelihood features |

**Rule:** Clustering is used ONLY where we need to discover natural groupings and assign descriptive labels. It is never used as a substitute for a missing target variable.

---

## Target Leakage Risks

### Dataset A — `loan_approval_dataset.csv`

| Risk | Column | Assessment |
| :--- | :--- | :--- |
| ⚠️ Low | `cibil_score` | In real systems, CIBIL score is pulled at application time — not leakage. Safe to use. |
| ⚠️ Low | Asset value columns | Self-declared by applicant at time of application. Not post-decision data. Safe. |
| ✅ None | All other columns | Standard application-time features. No leakage. |

### Dataset C — `External_Cibil_Dataset.csv` + `Internal_Bank_Dataset.csv`

| Risk | Column | Assessment |
| :--- | :--- | :--- |
| ⚠️ Medium | `Approved_Flag` as "approval" | If interpreted as "was the loan approved?", then features like `num_times_delinquent` from the same reporting period could be post-decision. However, since `Approved_Flag` is actually a risk tier label (P1-P4), it likely represents a risk grading decision made at application time using bureau data. The leakage risk is low if the tier was assigned BEFORE the loan was disbursed. |
| ⚠️ Low | All bureau features | Bureau data is pulled at application time. Standard practice. |
| ⚠️ Low | `Time_With_Curr_Empr` | Self-declared. Safe. |

### Dataset B — `RuralCreditData.csv`

| Risk | Assessment |
| :--- | :--- |
| ✅ None | No target variable exists. Leakage is not applicable. |

---

## Fields That Should Never Be Requested from Users

These fields exist in the datasets but cannot realistically be provided by a user filling out a web form:

### From External_Cibil_Dataset (62 columns — almost all are unrequestable)

| Field Category | Examples | Why unrequestable |
| :--- | :--- | :--- |
| Delinquency history | `num_times_delinquent`, `max_delinquency_level`, `num_deliq_6mts`, `num_deliq_12mts`, `num_times_30p_dpd`, `num_times_60p_dpd` | Users do not track their DPD counts. This comes from bureau reports. |
| Trade line counts | `num_std`, `num_sub`, `num_dbt`, `num_lss`, `num_std_6mts` etc. | Users do not know how many Standard/Sub-standard/Doubtful/Loss accounts they have. Bureau terminology. |
| Enquiry patterns | `tot_enq`, `CC_enq`, `PL_enq`, `enq_L3m`, `enq_L6m`, `enq_L12m` | Users do not track their credit enquiry counts. |
| Utilization ratios | `CC_utilization`, `PL_utilization`, `pct_currentBal_all_TL` | Users may have a rough sense but not exact percentages. |
| Time-based features | `time_since_recent_payment`, `time_since_first_deliquency`, `time_since_recent_deliquency`, `time_since_recent_enq` | Users do not know the exact number of months since their last delinquency. |
| Product flags | `CC_Flag`, `PL_Flag`, `HL_Flag`, `GL_Flag` | Users could answer "do you have a credit card?" but the flags may encode more nuance. |
| Percentage features | `pct_of_active_TLs_ever`, `pct_opened_TLs_L6m_of_L12m`, `pct_PL_enq_L6m_of_ever`, `pct_CC_enq_L6m_of_ever` | Bureau-computed ratios. Users cannot provide. |

### From Internal_Bank_Dataset (26 columns — all unrequestable)

| Field Category | Examples | Why unrequestable |
| :--- | :--- | :--- |
| Trade line counts | `Total_TL`, `Tot_Active_TL`, `Tot_Closed_TL`, `Auto_TL`, `CC_TL`, `Home_TL`, `PL_TL`, `Secured_TL`, `Unsecured_TL` | Bank-internal data. Users do not have access. |
| Time-period activity | `Total_TL_opened_L6M`, `Tot_TL_closed_L6M`, `Total_TL_opened_L12M` | Users do not track account opening/closing activity by time window. |
| Payment history | `Tot_Missed_Pmnt` | Users may know they missed payments but not the exact count across all accounts. |
| Account ages | `Age_Oldest_TL`, `Age_Newest_TL` | Users may know approximately but not in the format the model expects. |

---

## Critique of Current Form Specifications

### Person A (`docs/forms/person_a_fields.md`) — Major Revision Required

**Fields to REMOVE (do not exist in actual dataset):**

| # | Field | Reason |
| :--- | :--- | :--- |
| 3 | `gender` | Not in `loan_approval_dataset.csv`. Present in External_Cibil but only used for Risk Tier simplified model. |
| 4 | `married` | Not in `loan_approval_dataset.csv`. Present in External_Cibil as `MARITALSTATUS`. |
| 9 | `coapplicant_income` | Does not exist in any dataset in this project. |
| 14 | `property_area` | Does not exist in any dataset in this project. |
| 16 | `credit_history` (binary) | Does not exist. `cibil_score` is already collected — `credit_history` was a binary proxy from a different dataset. |
| 17 | `existing_emi` | Not in `loan_approval_dataset.csv`. Present in External_Cibil as complex trade line data, not a single number. |
| 18 | `number_of_loans` | Not in `loan_approval_dataset.csv`. Present in External_Cibil as multiple TL counts. |
| 19 | `delinquent_months` | Not in `loan_approval_dataset.csv`. Exists as multiple granular fields in External_Cibil. |
| 20 | `credit_utilization` | Not in `loan_approval_dataset.csv`. Exists as `CC_utilization`/`PL_utilization` in External_Cibil. |

**Fields to KEEP (exist in datasets):**

| # | Field | Maps to |
| :--- | :--- | :--- |
| 1 | `full_name` | Report only — keep |
| 2 | `age` | External_Cibil: `AGE` — keep for Risk Tier |
| 5 | `dependents` | Dataset A: `no_of_dependents` — keep but change validation (0–5 integer, not "3+" select) |
| 6 | `education` | Dataset A: `education` — keep |
| 7 | `self_employed` | Dataset A: `self_employed` — keep |
| 8 | `applicant_income` | Dataset A: `income_annum` — keep but rename to `annual_income` and change unit to annual |
| 11 | `loan_amount` | Dataset A: `loan_amount` — keep |
| 12 | `loan_term` | Dataset A: `loan_term` — keep but change validation (values 2–20, likely years) |
| 15 | `credit_score` | Dataset A: `cibil_score`, External_Cibil: `Credit_Score` — keep |

**Fields to ADD (exist in dataset but missing from spec):**

| Field | Maps to | Why needed |
| :--- | :--- | :--- |
| `residential_assets_value` | Dataset A: `residential_assets_value` | Model feature. User can estimate. |
| `commercial_assets_value` | Dataset A: `commercial_assets_value` | Model feature. User can estimate. |
| `luxury_assets_value` | Dataset A: `luxury_assets_value` | Model feature. User can estimate. |
| `bank_asset_value` | Dataset A: `bank_asset_value` | Model feature. User can estimate. |
| `gender` | External_Cibil: `GENDER` | Needed for Risk Tier simplified model |
| `marital_status` | External_Cibil: `MARITALSTATUS` | Needed for Risk Tier simplified model |
| `years_at_current_employer` | External_Cibil: `Time_With_Curr_Empr` | Needed for Risk Tier simplified model |
| `loan_purpose` | Context | Keep for report and recommendations |

---

### Person B (`docs/forms/person_b_fields.md`) — Moderate Revision Required

**Fields to REMOVE:**

| # | Field | Reason |
| :--- | :--- | :--- |
| 15 | `has_electricity` | Column does not exist in `RuralCreditData.csv` |
| 17 | `has_road` | Column does not exist in `RuralCreditData.csv` |
| 18 | `has_internet` | Column does not exist in `RuralCreditData.csv` |

**Fields to FIX:**

| # | Field | Problem | Fix |
| :--- | :--- | :--- | :--- |
| 12 | `home_ownership` | Spec says categorical (owned/rented/employer/family). Actual data is float 0.0/1.0. | Change to binary: `1` (owned) / `0` (not owned) |
| 13 | `type_of_house` | Spec says pucca/semi_pucca/kucha. Actual values: T1/T2/R. | Change to match dataset: `T1` / `T2` / `R`. Label as: T1 = Permanent, T2 = Semi-Permanent, R = Temporary |
| 16 | `has_water` | Spec says boolean checkbox. Actual `water_availabity` is 0.0/0.5/1.0. | Change to 3-level select: Full (1.0) / Partial (0.5) / None (0.0) |
| 4 | `primary_business` | Spec lists 9 categories. Actual data has 30+. | Expand dropdown or use grouped categories |
| 9 | `loan_purpose` | Spec lists 8 categories. Actual data has 37. | Expand dropdown or use grouped categories |

**Fields to ADD:**

| Field | Maps to | Why needed |
| :--- | :--- | :--- |
| `occupants_count` | `occupants_count` | Household burden indicator |
| `sanitary_availability` | `sanitary_availability` | Infrastructure signal (binary 0/1) |
| `loan_tenure` | `loan_tenure` | Loan term requested |
| `loan_installments` | `loan_installments` | Repayment structure |
| `social_class` | `social_class` | 13.14% missing — make optional. Used in archetype clustering. |
| `city` | `city` | 4.66% missing — make optional. Geographic context. |

**Fields to KEEP as-is:** `full_name`, `age`, `gender`, `annual_income`, `monthly_expenses`, `loan_amount`, `young_dependents`, `old_dependents`, `house_area`, `secondary_business`.

**Derived features to FIX:**
- `infrastructure_score` (sum of 4 booleans) → Invalid. Only `sanitary_availability` and `water_availabity` exist. Replace with: `infrastructure_score = sanitary_availability + water_availabity` (range 0.0–2.0).
- Other derived features (`income_expense_ratio`, `loan_income_ratio`, `disposable_income`, `total_dependents`) remain valid.

---

## Revised Person A Field Summary

After correction, Person A collects:

| Section | Fields | Engine |
| :--- | :--- | :--- |
| Identity | `full_name`, `age`, `gender`, `marital_status` | Report, Risk Tier |
| Profile | `dependents`, `education`, `self_employed`, `years_at_current_employer` | Eligibility, Risk Tier |
| Income | `annual_income` | Eligibility, Risk Tier |
| Assets | `residential_assets_value`, `commercial_assets_value`, `luxury_assets_value`, `bank_asset_value` | Eligibility |
| Loan | `loan_amount`, `loan_term`, `loan_purpose` | Eligibility, Report |
| Credit | `cibil_score` | Eligibility, Risk Tier |

**Total: 17 fields** (down from 20, but 4 new asset fields replace 5 phantom fields).

---

## Revised Person B Field Summary

After correction, Person B collects:

| Section | Fields | Engine |
| :--- | :--- | :--- |
| Identity | `full_name`, `age`, `gender` | Report |
| Livelihood | `primary_business`, `secondary_business` (optional), `annual_income`, `monthly_expenses` | Readiness, Archetype |
| Loan | `loan_amount`, `loan_purpose`, `loan_tenure`, `loan_installments` | Readiness |
| Dependents | `young_dependents`, `old_dependents`, `occupants_count` | Readiness |
| Housing | `home_ownership` (binary), `type_of_house` (T1/T2/R), `house_area` (optional) | Readiness, Archetype |
| Infrastructure | `sanitary_availability` (binary), `water_availabity` (3-level) | Readiness |
| Context | `social_class` (optional), `city` (optional) | Archetype |

**Total: 20 fields** (up from 18, but 3 invented fields removed and 5 real fields added).

---

## Complexity Rejections

The following are explicitly rejected for V1:

| Idea | Rejection Reason |
| :--- | :--- |
| Train Risk Tier on all 88 CIBIL+Internal features | Users cannot provide 81 of these features. A model trained on them cannot accept user input. |
| Use a neural network / deep learning model | 4,269 and 51,336 rows do not justify deep learning. Random Forest / Gradient Boosting will match or exceed performance with better interpretability. |
| Generate a "probability of approval" for Person B | No approval labels exist. Fabricating a probability would be dishonest. The weighted Readiness Score is the correct output. |
| Use LLM to generate recommendations | Rule-based recommendations are more reliable, auditable, and deterministic. LLMs add latency, cost, and non-determinism with no clear benefit. |
| Cluster for Readiness Score | Readiness is a continuous score measuring preparedness on known dimensions. Clustering produces discrete categories, which is less informative. Clustering is reserved for Archetype engines where groupings are emergent. |
| Combine all datasets into one | The datasets serve different engines for different user types. Merging them would create a franken-dataset with incompatible feature spaces. |
| Collect bureau-level detail from users | Fields like `num_deliq_6mts`, `pct_PL_enq_L6m_of_ever`, or `Tot_Active_TL` are not known to users and would create form abandonment. The simplified 7-feature Risk Tier model trades accuracy for usability. |

---

## Summary of Decisions

| # | Decision | Status |
| :--- | :--- | :--- |
| D1 | Eligibility Engine uses `loan_approval_dataset.csv` with binary classification | Decided |
| D2 | Risk Tier Engine uses External_Cibil + Internal_Bank joined, simplified to 7 user-knowable features | Decided |
| D3 | Borrower Archetype Engine uses K-Means clustering on 5 user-knowable features from CIBIL data | Decided |
| D4 | Recommendation Engine is rule-based, no separate model | Decided |
| D5 | Readiness Engine uses weighted scoring formula on RuralCreditData | Decided |
| D6 | Livelihood Archetype Engine uses K-Means clustering on RuralCreditData livelihood features | Decided |
| D7 | Person A form spec must be rewritten to match actual dataset columns | Required |
| D8 | Person B form spec must be corrected for invented fields and wrong value types | Required |
| D9 | Approved_Flag (P1-P4) is used directly as Risk Tier label — no need to invent tiers | Decided |
| D10 | Clustering is used ONLY for Archetype engines (Person A and Person B) | Decided |
