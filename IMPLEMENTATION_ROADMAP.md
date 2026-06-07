# RiskIntel — Implementation Roadmap V1.1

**Status:** ACTIVE — Solo developer build sequence
**Date:** 2026-06-05
**Revision:** V1.1 — Updated per Principal ML Engineer review. Fixes fake explainability, archetype clustering redundancy, income scale mismatch, livelihood encoding, and readiness calibration assumptions.
**Reference:** `docs/final_architecture_v1.md`, `docs/output_contracts.md`

---

## How to Use This Document

Each phase is self-contained. Complete all tasks in a phase before moving to the next. Each task has explicit acceptance criteria — do not move on until every criterion passes. Phases are ordered by dependency: later phases depend on earlier phases being complete.

**Estimated total phases:** 11
**Estimated total tasks:** 48

---

## Phase 1 — Project Setup

**Objective:** Initialize the Python backend environment, install dependencies, and establish the project's module structure so all subsequent phases have a working foundation.

**Dependencies:** None — this is the starting point.

---

### Task 1.1 — Backend Environment Setup

**Files to create:**
- `backend/requirements.txt`
- `backend/.env.example`

**Actions:**
- Create a Python virtual environment inside `backend/`.
- Install core dependencies: `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `sqlalchemy[asyncio]`, `aiosqlite`, `alembic`, `pandas`, `numpy`, `scikit-learn`, `joblib`, `reportlab`, `treeinterpreter`.
- Freeze versions into `requirements.txt`.
- Create `.env.example` with placeholder config values (`DB_PATH`, `MODEL_DIR`, `REPORT_OUTPUT_DIR`).

**Acceptance criteria:**
- [ ] `pip install -r requirements.txt` completes without errors.
- [ ] `python -c "import fastapi, uvicorn, sqlalchemy, pandas, sklearn, joblib, reportlab"` succeeds.

---

### Task 1.2 — Backend Module Structure

**Files to create:**
- `backend/app/__init__.py`
- `backend/app/config.py`
- `backend/app/engines/__init__.py`
- `backend/app/routes/__init__.py`
- `backend/app/utils/__init__.py`
- `backend/app/report/__init__.py`
- `backend/run.py`

**Actions:**
- Create the FastAPI application instance in `app/main.py` (replaces the planned Flask factory).
- Create `app/core/config.py` with Pydantic `BaseSettings` reading from environment variables.
- Create empty `__init__.py` files for each subpackage.
- Run the app with `uvicorn app.main:app --host 0.0.0.0 --port 8000` (see `backend/Dockerfile`).

**Acceptance criteria:**
- [ ] `uvicorn app.main:app` boots without errors.
- [ ] `GET /health/live` returns `{"status":"UP", ...}`.

---

### Task 1.3 — Frontend Environment Setup

**Files to create:**
- `frontend/` (Vite + React project via `npx`)
- `frontend/.env.example`

**Actions:**
- Initialize a Vite + React project inside `frontend/`.
- Install dependencies: `axios` (or use fetch).
- Create `.env.example` with `VITE_API_URL=http://localhost:5000`.

**Acceptance criteria:**
- [ ] `npm run dev` starts the Vite dev server without errors.
- [ ] Browser shows the default React page.

---

### Task 1.4 — Data Directory Verification

**Files to create:** None — verify existing files.

**Actions:**
- Confirm all 4 required CSVs exist in `data/raw/`:
  - `loan_approval_dataset.csv` (4,269 rows)
  - `External_Cibil_Dataset.csv` (51,336 rows)
  - `Internal_Bank_Dataset.csv` (51,336 rows)
  - `RuralCreditData.csv` (40,000 rows)
- Create `data/processed/` directory if not present.

**Acceptance criteria:**
- [ ] All 4 CSV files load with `pd.read_csv()` without errors.
- [ ] Row counts match expected values.

---

## Phase 2 — Data Preprocessing

**Objective:** Clean and prepare the raw datasets for engine consumption. Save processed outputs to `data/processed/`. All engines will read from processed data, never from raw.

**Dependencies:** Phase 1 complete.

---

### Task 2.1 — Preprocess Dataset A (Eligibility)

**File to create:**
- `backend/app/utils/preprocess_a.py`

**Input:** `data/raw/loan_approval_dataset.csv`
**Output:** `data/processed/eligibility_data.csv`

**Actions:**
- Strip leading spaces from all column names.
- Strip leading spaces from string values (`education`, `self_employed`, `loan_status`).
- Handle 28 negative values in `residential_assets_value` (clip to 0).
- Rename columns to internal names matching the form spec:
  - `no_of_dependents` → `dependents`
  - `income_annum` → `annual_income`
  - `cibil_score` → `cibil_score` (keep)
  - `loan_status` → `loan_status` (keep)
- Drop `loan_id`.
- Save to `data/processed/eligibility_data.csv`.

**Acceptance criteria:**
- [ ] Output CSV has 4,269 rows, 12 columns (11 features + 1 target).
- [ ] No column names have leading spaces.
- [ ] No negative values in any asset column.
- [ ] `loan_status` contains only `"Approved"` and `"Rejected"`.

---

### Task 2.2 — Preprocess Dataset C (Risk Tier + Archetype)

**File to create:**
- `backend/app/utils/preprocess_c.py`

**Input:** `data/raw/External_Cibil_Dataset.csv`
**Output:** `data/processed/risk_tier_thresholds.json`, `data/processed/archetype_data.csv`

**Actions:**
- Validate Credit_Score threshold boundaries:
  - P1: ≥ 701
  - P2: 669–700
  - P3: 659–668
  - P4: ≤ 658
- Save threshold config to `risk_tier_thresholds.json`.
- Extract 6 user-knowable columns for archetype clustering (Credit_Score excluded — see V1.1 review note): `NETMONTHLYINCOME`, `AGE`, `GENDER`, `EDUCATION`, `MARITALSTATUS`, `Time_With_Curr_Empr`.
- Encode categoricals: `GENDER` → numeric, `EDUCATION` → ordinal, `MARITALSTATUS` → numeric.
- Save to `data/processed/archetype_data.csv`.

> **V1.1 Review Note — Credit_Score excluded from archetype clustering:** Credit_Score accounts for 94.42% of classification signal in Dataset C. Including it in K-Means causes archetypes to collapse into risk-tier proxies (e.g., P1 ≈ "Stable Established", P4 ≈ "Credit-Stressed"), making E3 redundant with E2. Removing it forces the algorithm to discover behavioral dimensions orthogonal to credit score: income level, life stage, employment stability, and household composition.

**Acceptance criteria:**
- [ ] `risk_tier_thresholds.json` contains the 4 tier boundaries.
- [ ] `archetype_data.csv` has 51,336 rows, 6 columns, all numeric.
- [ ] No missing values.

---

### Task 2.3 — Preprocess Dataset B (Readiness + Livelihood)

**File to create:**
- `backend/app/utils/preprocess_b.py`

**Input:** `data/raw/RuralCreditData.csv`
**Output:** `data/processed/readiness_data.csv`, `data/processed/livelihood_data.csv`

**Actions:**
- Drop `Id` column.
- Handle missing values:
  - `city` (4.66%): fill with `"Unknown"`.
  - `social_class` (13.14%): fill with `"Unknown"`.
  - `secondary_business` (13.1%): fill with `"none"`.
  - `monthly_expenses` (0.3%): fill with median.
  - `home_ownership` (0.95%): fill with mode (1.0).
  - `type_of_house` (1.74%): fill with mode.
  - `sanitary_availability` (0.52%): fill with mode.
  - `water_availabity` (13.13%): fill with median (0.5).
  - `primary_business` (0.06%): fill with mode.
  - `loan_purpose` (0.06%): fill with mode.
- Fix typo: rename `water_availabity` → `water_availability`.
- For `readiness_data.csv`: keep all 20 columns (minus Id).
- For `livelihood_data.csv`: extract clustering features (`primary_business`, `annual_income`, `monthly_expenses`, `loan_amount`, `loan_purpose`, `home_ownership`, `type_of_house`).
- Map `primary_business` (30+ categories) to macro-categories before encoding: `Agriculture` (farming, rearing, dairy), `Retail` (tailoring, grocery, vendor), `Production` (handloom, handicrafts, manufacturing), `Services` (daily wage, transport, other services). Map based on dominant category groups in the data.
- Map `loan_purpose` (37 categories) to macro-categories before encoding: `Agriculture` (crop, livestock, agro-based), `Business` (working capital, equipment, raw materials), `Housing` (house repair, construction), `Personal` (education, medical, other).
- Encode macro-categories as ordinal integers. Do NOT one-hot encode — K-Means cannot handle 70+ sparse binary dimensions meaningfully.

> **V1.1 Review Note — Why macro-categories:** Label-encoding 30+ raw categories creates false ordinal relationships (business #30 is not "farther" from business #1 than business #2). One-hot encoding creates 70+ sparse dimensions that degrade Euclidean distance. Macro-categories (4 per field) are semantically ordered and produce stable, interpretable clusters.

**Acceptance criteria:**
- [ ] `readiness_data.csv` has 40,000 rows, 20 columns, 0 missing values.
- [ ] `livelihood_data.csv` has 40,000 rows, 7 columns, all numeric, 0 missing values.
- [ ] Column `water_availability` exists (typo fixed).

---

## Phase 3 — Eligibility Engine (E1)

**Objective:** Train a Random Forest binary classifier on Dataset A. Serialize the model. Create the engine module that accepts a dict and returns eligibility results.

**Dependencies:** Phase 2 (Task 2.1) complete.

---

### Task 3.1 — Train Eligibility Model

**File to create:**
- `backend/app/engines/train_eligibility.py`

**Input:** `data/processed/eligibility_data.csv`
**Output:** `models/eligibility_model.joblib`, `models/eligibility_metadata.json`

**Actions:**
- Load processed data.
- Encode categoricals (`education`, `self_employed`) via LabelEncoder.
- Split 80/20 train/test (random_state=42).
- Train RandomForestClassifier (n_estimators=100, random_state=42).
- Evaluate: accuracy, F1, classification report.
- Save model with `joblib.dump()`.
- Save metadata JSON: accuracy, F1, feature names, label mapping, train date.

**Acceptance criteria:**
- [ ] `eligibility_model.joblib` exists in `models/`.
- [ ] `eligibility_metadata.json` contains accuracy > 0.75.
- [ ] Model loads with `joblib.load()` and predicts on a sample input.

---

### Task 3.2 — Eligibility Engine Module

**File to create:**
- `backend/app/engines/eligibility.py`

**Input:** Python dict with 11 feature fields.
**Output:** Python dict matching `eligibility` object in output contract.

**Actions:**
- Load serialized model on startup.
- Implement `predict(input_dict) -> result_dict`.
- Map predicted probability to verdict (Highly Likely / Likely / Borderline / Unlikely) per threshold table in output contracts.
- Compute per-prediction feature contributions using `treeinterpreter`. This decomposes the Random Forest prediction into `bias + Σ(feature_contributions)` along the actual decision paths taken for the specific input. Each contribution is directional (positive = pushes toward approval, negative = pushes toward rejection) and sums exactly to the prediction.
- Return `{"verdict": ..., "probability": ..., "feature_contributions": {...}, "bias": ...}`.

> **V1.1 Review Note — Why not global feature importances × deviation:** Random Forest `.feature_importances_` (MDI) is a global, non-directional metric averaged across all trees. Multiplying it by `(input - training_mean)` assumes a linear relationship that contradicts tree-based split routing. Two inputs with the same feature value can follow completely different decision paths. `treeinterpreter` traces the actual path per prediction, producing mathematically valid, instance-level explanations that sum exactly to the predicted probability.

**Acceptance criteria:**
- [ ] `predict({"dependents": 2, "education": "Graduate", ...})` returns a valid result dict.
- [ ] `verdict` is one of the 4 allowed strings.
- [ ] `probability` is a float between 0.0 and 1.0.
- [ ] `feature_contributions` contains all 11 feature keys.
- [ ] Engine handles missing optional fields gracefully (returns error, not crash).

---

## Phase 4 — Risk Tier Engine (E2)

**Objective:** Implement the rule-based Risk Tier engine using Credit_Score thresholds. No ML model.

**Dependencies:** Phase 2 (Task 2.2) complete.

---

### Task 4.1 — Risk Tier Engine Module

**File to create:**
- `backend/app/engines/risk_tier.py`

**Input:** Python dict with `cibil_score` field.
**Output:** Python dict matching `risk_tier` object in output contract.

**Actions:**
- Load thresholds from `data/processed/risk_tier_thresholds.json`.
- Implement `classify(input_dict) -> result_dict`.
- Apply threshold logic:
  - cibil_score ≥ 701 → P1
  - 669 ≤ cibil_score ≤ 700 → P2
  - 659 ≤ cibil_score ≤ 668 → P3
  - cibil_score ≤ 658 → P4
- Map tier to label and description.
- Include thresholds object in response for transparency.

**Acceptance criteria:**
- [ ] `classify({"cibil_score": 742})` returns `{"tier": "P1", "label": "Low Risk", ...}`.
- [ ] `classify({"cibil_score": 680})` returns `{"tier": "P2", ...}`.
- [ ] `classify({"cibil_score": 665})` returns `{"tier": "P3", ...}`.
- [ ] `classify({"cibil_score": 500})` returns `{"tier": "P4", ...}`.
- [ ] Edge cases: 701 → P1, 700 → P2, 669 → P2, 668 → P3, 659 → P3, 658 → P4.
- [ ] Invalid input (missing or out-of-range cibil_score) returns an error, not a crash.

---

## Phase 5 — Borrower Archetype Engine (E3)

**Objective:** Train K-Means clustering on 6 user-knowable features from the CIBIL dataset (Credit_Score excluded per V1.1 review). Serialize the model. Create the engine module.

**Dependencies:** Phase 2 (Task 2.2) complete.

---

### Task 5.1 — Train Archetype Clustering Model

**File to create:**
- `backend/app/engines/train_archetype.py`

**Input:** `data/processed/archetype_data.csv`
**Output:** `models/archetype_model.joblib`, `models/archetype_metadata.json`, `models/archetype_scaler.joblib`

**Actions:**
- Load processed archetype data (6 features: NETMONTHLYINCOME, AGE, GENDER, EDUCATION, MARITALSTATUS, Time_With_Curr_Empr).
- Standardize features using StandardScaler (K-Means is distance-based — scaling required).
- Run Elbow Method for k=2 to k=8. Select optimal k.
- Train KMeans with optimal k (random_state=42).
- Inspect cluster centroids. Assign human-readable labels based on centroid profiles. Verify that cluster labels do NOT simply mirror risk tiers — if they do, the feature set needs further revision.
- Save model, scaler, and metadata (cluster centroids, labels, silhouette score).

> **V1.1 Income Scale Sensitivity:** The scaler is fitted on Dataset C's NETMONTHLYINCOME (mean ≈ ₹25K–29K). At runtime, Person A's `annual_income` is divided by 12 and fed through this scaler. For users entering realistic Indian monthly incomes (₹15K–₹80K), the z-scores will be valid. For demo purposes, do NOT use Dataset A's synthetic income values (mean ₹4.2L/month) — they will produce extreme outlier z-scores and meaningless cluster assignments. Use realistic income values when testing E3.

**Acceptance criteria:**
- [ ] `archetype_model.joblib` and `archetype_scaler.joblib` exist in `models/`.
- [ ] `archetype_metadata.json` contains cluster labels, centroids, and silhouette score.
- [ ] Silhouette score > 0.15 (lower threshold accepted — removing Credit_Score reduces dominant variance axis, producing softer but more meaningful cluster boundaries).
- [ ] 3–5 clusters with distinct, interpretable profiles that do NOT mirror risk tiers.

---

### Task 5.2 — Archetype Engine Module

**File to create:**
- `backend/app/engines/archetype.py`

**Input:** Python dict with 6 feature fields (NETMONTHLYINCOME, AGE, GENDER, EDUCATION, MARITALSTATUS, Time_With_Curr_Empr). Credit_Score is excluded per V1.1 review.
**Output:** Python dict matching `archetype` object in output contract.

**Actions:**
- Load model and scaler on startup.
- Implement `classify(input_dict) -> result_dict`.
- Scale input using saved scaler.
- Predict cluster.
- Map cluster_id to label and description from metadata.
- Return `{"label": ..., "description": ..., "cluster_id": ...}`.

**Acceptance criteria:**
- [ ] `classify({"NETMONTHLYINCOME": 25000, "AGE": 35, "GENDER": "Male", ...})` returns a valid result.
- [ ] `label` is one of the defined archetype labels from metadata.
- [ ] `cluster_id` is a non-negative integer.

---

## Phase 6 — Readiness Engine (E5)

**Objective:** Implement the weighted scoring formula for Person B. No ML model — pure rule-based computation.

**Dependencies:** Phase 2 (Task 2.3) complete.

---

### Task 6.1 — Readiness Engine Module

**File to create:**
- `backend/app/engines/readiness.py`

**Input:** Python dict with 16 Person B feature fields.
**Output:** Python dict matching `readiness` object in output contract.

**Actions:**
- Implement 5 component scoring functions:
  - `score_financial_health(annual_income, monthly_expenses, loan_amount) -> 0-100`
  - `score_housing_stability(home_ownership, type_of_house, house_area) -> 0-100`
  - `score_infrastructure_access(sanitary_availability, water_availability) -> 0-100`
  - `score_household_burden(young_dependents, old_dependents, occupants_count, annual_income) -> 0-100`
  - `score_business_viability(primary_business, secondary_business, loan_purpose) -> 0-100`
- Combine using weights: 0.35, 0.20, 0.15, 0.15, 0.15.
- Map total score to band: Ready / Moderately Ready / Needs Improvement / Not Ready.
- Return full response with component breakdown.

**Acceptance criteria:**
- [ ] A high-quality applicant (owned home, high income, low expenses, good infrastructure) scores ≥ 75.
- [ ] A low-quality applicant (no home, low income, high expenses, no infrastructure) scores ≤ 25.
- [ ] All 5 component scores are between 0 and 100.
- [ ] Weights sum to 1.0.
- [ ] Final score is between 0 and 100.
- [ ] Band is one of the 4 allowed strings.
- [ ] Component breakdown includes factors with actual values.

---

### Task 6.2 — Readiness Scoring Calibration

**File to create:**
- `backend/app/engines/calibrate_readiness.py`

**Input:** `data/processed/readiness_data.csv`
**Output:** Console output — distribution analysis.

**Actions:**
- Run the Readiness Engine on all 40,000 rows.
- Print score distribution: min, max, mean, median, std.
- Print band distribution: count and percentage per band.
- Verify no band has 0% or >80% of applicants (distribution should be reasonable).
- Adjust scoring logic or weights if distribution is heavily skewed.

**Acceptance criteria:**
- [ ] All 4 bands have at least 1 applicant (no empty bands — an empty band indicates a formula error).
- [ ] No single band exceeds 80% of applicants (minimal spread check).
- [ ] Score distribution is documented (min, max, mean, median, std) — no forced target range.

> **V1.1 Review Note — Why distribution-forcing was removed:** The original criteria (all bands ≥ 5%, mean 35–65) assumed the rural population distributes symmetrically across readiness bands. There is no statistical basis for this assumption. Forcing it by tuning weights would distort the economic validity of individual component scores. The correct approach is to document the actual distribution and adjust only if a band is completely empty (indicating a formula error, not a population imbalance).

---

## Phase 7 — Livelihood Archetype Engine (E6)

**Objective:** Train K-Means clustering on livelihood features from the rural dataset. Serialize the model.

**Dependencies:** Phase 2 (Task 2.3) complete.

---

### Task 7.1 — Train Livelihood Clustering Model

**File to create:**
- `backend/app/engines/train_livelihood.py`

**Input:** `data/processed/livelihood_data.csv`
**Output:** `models/livelihood_model.joblib`, `models/livelihood_metadata.json`, `models/livelihood_scaler.joblib`

**Actions:**
- Load processed livelihood data.
- Standardize features using StandardScaler.
- Run Elbow Method for k=3 to k=8.
- Train KMeans with optimal k (random_state=42).
- Inspect cluster centroids. Assign labels (Agri Livelihood, Micro-Retail, Artisan Producer, Service Worker, etc.).
- Save model, scaler, and metadata.

**Acceptance criteria:**
- [ ] `livelihood_model.joblib` and `livelihood_scaler.joblib` exist in `models/`.
- [ ] `livelihood_metadata.json` contains cluster labels, centroids, silhouette score.
- [ ] Silhouette score > 0.15.
- [ ] 4–6 clusters with distinct livelihood profiles.

---

### Task 7.2 — Livelihood Archetype Engine Module

**File to create:**
- `backend/app/engines/livelihood.py`

**Input:** Python dict with 7 livelihood feature fields.
**Output:** Python dict matching `archetype` object in output contract (same shape as Person A archetype).

**Actions:**
- Load model and scaler on startup.
- Implement `classify(input_dict) -> result_dict`.
- Handle categorical encoding at runtime (same encoding used during training).
- Return `{"label": ..., "description": ..., "cluster_id": ...}`.

**Acceptance criteria:**
- [ ] `classify({"primary_business": "Tailoring", "annual_income": 120000, ...})` returns valid result.
- [ ] Label is one of the defined livelihood archetype labels.

---

## Phase 8 — Recommendation Engine (E4)

**Objective:** Implement the rule-based Recommendation Engine that consumes outputs from all other engines and generates actionable advice.

**Dependencies:** Phases 3, 4, 5, 6, 7 complete (all engines must have defined outputs).

---

### Task 8.1 — Recommendation Rules Configuration

**File to create:**
- `backend/app/engines/recommendation_rules.json`

**Actions:**
- Define the complete rule table as a JSON configuration file.
- Rules are organized by:
  - **Person A triggers:** eligibility verdict, risk tier, feature contribution signs, archetype label, ratio thresholds.
  - **Person B triggers:** readiness band, component scores below threshold, archetype label, input signals.
- Each rule has: `trigger_condition`, `category` (strength / risk_factor / recommendation / action), `message`.

**Acceptance criteria:**
- [ ] At least 20 rules for Person A.
- [ ] At least 15 rules for Person B.
- [ ] Every trigger condition is testable (no ambiguous conditions).
- [ ] Every message is actionable (no vague advice like "do better").

---

### Task 8.2 — Recommendation Engine Module

**File to create:**
- `backend/app/engines/recommendation.py`

**Input:** Python dict with engine outputs and raw applicant data (see E4 Input in output contracts).
**Output:** Python dict matching `recommendations` object in output contract.

**Actions:**
- Load rules from `recommendation_rules.json`.
- Implement `generate(engine_outputs, user_type) -> result_dict`.
- Evaluate each rule against the input.
- Collect triggered strengths, risk_factors/improvement_areas, recommendations, action_plan/next_steps.
- Cap each list at 5 items. Prioritize by rule severity.
- Ensure strengths and recommendations are never empty (add fallback generic items if no rules trigger).

**Acceptance criteria:**
- [ ] Person A with P1 tier and "Highly Likely" verdict generates strengths and minimal risk factors.
- [ ] Person A with P4 tier and "Unlikely" verdict generates multiple risk factors and actionable recommendations.
- [ ] Person B with score 80 ("Ready") generates mostly strengths.
- [ ] Person B with score 20 ("Not Ready") generates multiple improvement areas.
- [ ] `strengths` is never empty.
- [ ] `recommendations` is never empty.
- [ ] Each list has 1–5 items.

---

## Phase 9 — API Layer (FastAPI, SQLite V1)

**Objective:** Wire all engines into FastAPI routes. Implement request validation, error handling, and response formatting per output contracts.

> **Note:** This phase was originally planned as "Flask API" but was migrated
> to FastAPI during the V1 architecture freeze. SQLite is the canonical
> persistence backend (per D15). See `docs/final_architecture_v1.md` for
> the final stack.

**Dependencies:** Phase 8 complete (all engines functional).

---

### Task 9.1 — Input Validation Module

**File to create:**
- `backend/app/utils/validators.py`

**Actions:**
- Implement `validate_person_a(request_json) -> (cleaned_dict, errors)`.
- Implement `validate_person_b(request_json) -> (cleaned_dict, errors)`.
- Validate all required fields, types, ranges per the form specifications.
- Return cleaned data if valid, or error details list if invalid.
- Error details follow the `error.details[]` shape from output contracts.

**Acceptance criteria:**
- [ ] Missing required field → error with code `MISSING_REQUIRED_FIELD`.
- [ ] Out-of-range value → error with code `VALIDATION_ERROR` and per-field detail.
- [ ] Valid input → returns cleaned dict with no errors.
- [ ] Extra unknown fields are ignored (not rejected).

---

### Task 9.2 — Person A Route

**File to create:**
- `backend/app/routes/assess.py`

**Endpoint:** `POST /api/assess/person-a`

**Actions:**
- Parse and validate request body.
- Call E1 (Eligibility) with form inputs.
- Call E2 (Risk Tier) with cibil_score.
- Call E3 (Archetype) with 7 user-knowable fields.
- Call E4 (Recommendation) with combined engine outputs.
- Assemble response per Person A output contract.
- Store result in SQLite for report generation.
- Return JSON with `200 OK`.

**Acceptance criteria:**
- [ ] Valid Person A request returns complete JSON matching output contract shape.
- [ ] Invalid request returns error JSON with correct error code and status.
- [ ] Response includes all 4 sections: eligibility, risk_tier, archetype, recommendations.
- [ ] `applicant` echo contains all 17 submitted fields.

---

### Task 9.3 — Person B Route

**File to create:**
- Extend `backend/app/routes/assess.py`

**Endpoint:** `POST /api/assess/person-b`

**Actions:**
- Parse and validate request body.
- Call E5 (Readiness) with form inputs.
- Call E6 (Livelihood Archetype) with livelihood features.
- Call E4 (Recommendation) with combined engine outputs.
- Assemble response per Person B output contract.
- Store result in SQLite.
- Return JSON with `200 OK`.

**Acceptance criteria:**
- [ ] Valid Person B request returns complete JSON matching output contract shape.
- [ ] `readiness.components` contains all 5 components with scores, weights, and factors.
- [ ] `readiness.band` is one of the 4 allowed strings.

---

### Task 9.4 — Error Handling Middleware

**File to create:**
- `backend/app/utils/error_handlers.py`

**Actions:**
- Register global error handlers in `app/main.py` (FastAPI).
- Handle `RequestValidationError` → 400 with `VALIDATION_ERROR` code (or `MISSING_REQUIRED_FIELD` when fields are absent).
- Handle `CriticalEngineError` / `NonCriticalEngineError` → 500 with `ENGINE_FAILURE` code.
- Handle `AuditLogError` → 500 with `INTERNAL_ERROR` code (fail-closed).
- Handle all uncaught exceptions → 500 with `INTERNAL_ERROR` code.
- All errors return JSON matching the error response contract in `docs/output_contracts.md` §5.

**Acceptance criteria:**
- [ ] Every error returns JSON, never HTML.
- [ ] Every error has `status`, `error.code`, and `error.message`.
- [ ] Stack traces are logged server-side but NOT exposed in the response.

---

### Task 9.5 — SQLite Storage

**File to create:**
- `backend/app/utils/database.py`

**Why SQLite is retained:** SQLite serves three V1 purposes that justify its inclusion: (1) PDF report generation requires retrieving a completed assessment by ID — without storage, the user would need to re-submit the entire form to generate a report. (2) It enables a "recent assessments" list for demo and presentation. (3) It provides an audit trail for the project showcase. SQLite adds zero deployment complexity (single file, zero config, ships with Python's stdlib), and V1's write volume (single user, sequential requests) has no concurrency issues. Removing it would require the frontend to hold the full API response in memory and pass it back to the report endpoint, creating a fragile client-dependent architecture.

**Actions:**
- Create SQLite database at `backend/riskintel.db`.
- Create `assessments` table: `id`, `user_type`, `applicant_name`, `request_json`, `response_json`, `created_at`.
- Implement `save_assessment(user_type, request, response) -> assessment_id`.
- Implement `get_assessment(assessment_id) -> dict`.

**Acceptance criteria:**
- [ ] Assessment is saved after each successful API call.
- [ ] `get_assessment(id)` returns the full stored response.
- [ ] Database file is created automatically on first run.

---

## Phase 10 — Frontend

**Objective:** Build the React frontend with two form workflows, results display, and PDF download.

**Dependencies:** Phase 9 complete (API endpoints functional).

---

### Task 10.1 — Design System and Layout

**Files to create:**
- `frontend/src/index.css` (design tokens, global styles)
- `frontend/src/App.jsx` (root layout with routing)
- `frontend/src/components/Layout.jsx` (header, navigation, footer)

**Actions:**
- Define color palette, typography (Google Fonts), spacing scale.
- Create responsive layout with navigation between Person A and Person B workflows.
- Implement dark mode base.

**Acceptance criteria:**
- [ ] App renders with consistent typography and colors.
- [ ] Navigation between Person A and Person B works.
- [ ] Layout is responsive at mobile (375px) and desktop (1440px) widths.

---

### Task 10.2 — Person A Form

**Files to create:**
- `frontend/src/pages/PersonA.jsx`
- `frontend/src/components/FormSection.jsx`
- `frontend/src/components/FormField.jsx`

**Actions:**
- Build the 4-section form: Identity, Profile + Income + Assets, Loan, Credit.
- Implement client-side validation matching backend validation rules.
- Submit to `POST /api/assess/person-a`.
- Show loading state during submission.

**Acceptance criteria:**
- [ ] All 17 fields render with correct input types (text, number, select).
- [ ] Client-side validation prevents submission of invalid data.
- [ ] Successful submission receives and stores the API response.
- [ ] Form shows validation errors inline per field.

---

### Task 10.3 — Person B Form

**Files to create:**
- `frontend/src/pages/PersonB.jsx`

**Actions:**
- Build the 6-section form: Identity, Livelihood, Loan, Dependents, Housing, Infrastructure.
- Implement client-side validation.
- Submit to `POST /api/assess/person-b`.

**Acceptance criteria:**
- [ ] All 20 fields render correctly.
- [ ] Binary fields (home_ownership, sanitary_availability) render as toggle/checkbox.
- [ ] Water availability renders as 3-option select (None / Partial / Full).
- [ ] Type of house renders as 3-option select (T1 / T2 / R) with human labels.

---

### Task 10.4 — Person A Results Display

**Files to create:**
- `frontend/src/pages/PersonAResults.jsx`
- `frontend/src/components/EligibilityCard.jsx`
- `frontend/src/components/RiskTierCard.jsx`
- `frontend/src/components/ArchetypeCard.jsx`
- `frontend/src/components/RecommendationCard.jsx`
- `frontend/src/components/FeatureChart.jsx`

**Actions:**
- Render eligibility verdict with probability gauge.
- Render feature contributions as horizontal bar chart (positive = green right, negative = red left).
- Render risk tier badge with threshold scale visualization.
- Render archetype label with description.
- Render recommendations as styled lists.
- Add "Download PDF Report" button.

**Acceptance criteria:**
- [ ] All 4 sections (eligibility, risk tier, archetype, recommendations) display correctly.
- [ ] Feature contribution chart sorts by absolute magnitude.
- [ ] Risk tier threshold scale shows where the applicant falls.
- [ ] PDF download button triggers report generation.

---

### Task 10.5 — Person B Results Display

**Files to create:**
- `frontend/src/pages/PersonBResults.jsx`
- `frontend/src/components/ReadinessGauge.jsx`
- `frontend/src/components/ComponentBreakdown.jsx`

**Actions:**
- Render readiness score as a circular gauge (0–100) with band label.
- Render 5 component scores as progress bars with weights displayed.
- Render livelihood archetype label with description.
- Render recommendations as styled lists.
- Add "Download PDF Report" button.

**Acceptance criteria:**
- [ ] Readiness gauge displays score and band.
- [ ] All 5 component progress bars show correct scores.
- [ ] Component weights are visible.
- [ ] PDF download button triggers report generation.

---

### Task 10.6 — Landing Page

**Files to create:**
- `frontend/src/pages/Home.jsx`

**Actions:**
- Create a landing page explaining what RiskIntel does.
- Two call-to-action cards: "I have a credit history" (→ Person A) and "I am new to credit" (→ Person B).
- Brief feature list.

**Acceptance criteria:**
- [ ] Landing page clearly directs users to the correct workflow.
- [ ] Both CTA cards navigate to their respective form pages.
- [ ] Page looks polished and professional.

---

### Task 10.7 — Error Handling UI

**Files to create:**
- `frontend/src/components/ErrorDisplay.jsx`

**Actions:**
- Handle API errors gracefully.
- Display field-level validation errors from the `error.details[]` array.
- Display global errors (MODEL_NOT_LOADED, ENGINE_FAILURE) as alert banners.
- Never show raw stack traces or JSON to the user.

**Acceptance criteria:**
- [ ] Validation errors show inline next to the offending field.
- [ ] Server errors show a user-friendly message with a retry button.
- [ ] Network errors (API unreachable) show a connection error message.

---

## Phase 11 — PDF Report Engine

**Objective:** Generate professional PDF reports for Person A and Person B using ReportLab.

**Dependencies:** Phase 9 complete (stored assessments available).

---

### Task 11.1 — Report Template Design

**Files to create:**
- `backend/app/report/styles.py`
- `backend/app/report/components.py`

**Actions:**
- Define PDF styles: fonts, colors, spacing, margins.
- Create reusable report components: header, section title, table, bulleted list, bar chart, gauge, disclaimer.
- Use RiskIntel branding (logo placeholder, color scheme).

**Acceptance criteria:**
- [ ] Components render correctly in isolation (test with a blank PDF).
- [ ] Fonts load without errors.
- [ ] Colors match the frontend design system.

---

### Task 11.2 — Person A Report Generator

**File to create:**
- `backend/app/report/person_a_report.py`

**Input:** Full Person A assessment response (from SQLite or direct).
**Output:** PDF file bytes.

**Actions:**
- Render all sections defined in output contracts:
  - Header with report ID and date
  - Applicant Summary table
  - Eligibility verdict with probability bar
  - Feature contribution horizontal bar chart
  - Risk Tier badge with threshold table
  - Borrower Archetype section
  - Strengths list
  - Risk Factors list
  - Recommendations list
  - Action Plan with checkboxes
  - Disclaimer footer

**Acceptance criteria:**
- [ ] Generated PDF opens correctly in a PDF reader.
- [ ] All sections are present and populated.
- [ ] No text overflow or layout breaking.
- [ ] File size < 500KB.

---

### Task 11.3 — Person B Report Generator

**File to create:**
- `backend/app/report/person_b_report.py`

**Input:** Full Person B assessment response.
**Output:** PDF file bytes.

**Actions:**
- Render all sections:
  - Header with report ID and date
  - Applicant Summary table
  - Readiness Score gauge with band label
  - Component Breakdown with 5 progress bars
  - Livelihood Archetype section
  - Strengths list
  - Improvement Areas list
  - Recommendations list
  - Next Steps with checkboxes
  - Disclaimer footer

**Acceptance criteria:**
- [ ] Generated PDF opens correctly.
- [ ] Readiness score and band are prominently displayed.
- [ ] All 5 component scores visible.
- [ ] File size < 500KB.

---

### Task 11.4 — Report API Endpoint

**File to create:**
- `backend/app/routes/report.py`

**Endpoint:** `POST /api/report/generate`

**Actions:**
- Accept `assessment_id` in request body.
- Retrieve stored assessment from SQLite.
- Determine user type (person_a or person_b).
- Call the appropriate report generator.
- Return PDF bytes with correct headers (`Content-Type: application/pdf`, `Content-Disposition: attachment`).

**Acceptance criteria:**
- [ ] `POST /api/report/generate {"assessment_id": 1}` returns a PDF file.
- [ ] Response headers include correct Content-Type and Content-Disposition.
- [ ] Invalid assessment_id returns 404 error.
- [ ] Frontend can trigger download and browser prompts "Save As".

---

## Build Order Summary

```
Phase 1  ──► Phase 2  ──┬──► Phase 3 (E1 Eligibility)
                        ├──► Phase 4 (E2 Risk Tier)
                        ├──► Phase 5 (E3 Archetype)
                        ├──► Phase 6 (E5 Readiness)
                        └──► Phase 7 (E6 Livelihood)
                                     │
                                     ▼
                              Phase 8 (E4 Recommendation)
                                     │
                                     ▼
                              Phase 9 (Flask API)
                                     │
                                     ▼
                        ┌──► Phase 10 (Frontend)
                        └──► Phase 11 (PDF Reports)
```

Phases 3–7 can be built in any order after Phase 2. Phase 8 requires all engines. Phase 9 requires Phase 8. Phases 10 and 11 can be built in parallel after Phase 9.

---

## Milestone Checkpoints

| After Phase | You Should Be Able To... |
| :--- | :--- |
| 2 | Load any processed CSV and confirm clean data with zero missing values |
| 3 | Run `eligibility.predict({...})` in a Python shell and get a valid result |
| 4 | Run `risk_tier.classify({"cibil_score": 742})` and get `"P1"` |
| 5 | Run `archetype.classify({...})` and get a labeled archetype |
| 7 | Run `livelihood.classify({...})` and get a labeled livelihood archetype |
| 8 | Run `recommendation.generate({...})` and get strengths + recommendations |
| 9 | `curl -X POST /api/assess/person-a -d '{...}'` returns complete JSON |
| 10 | Fill out a form in the browser and see results rendered |
| 11 | Click "Download PDF" and receive a professional report |

---

## V1 Scope (Final)

The following components are confirmed for V1 implementation:

| Component | Status | V1.1 Notes |
| :--- | :--- | :--- |
| E1 — Eligibility Engine | ✅ V1 | Binary classification. Local explainability via `treeinterpreter`. |
| E2 — Risk Tier Engine | ✅ V1 | Rule-based threshold logic. No ML model. |
| E3 — Borrower Archetype Engine | ✅ V1 (Modified) | K-Means on 6 features (Credit_Score excluded). See final decision below. |
| E4 — Recommendation Engine | ✅ V1 | Rule-based. Consumes all other engine outputs. |
| E5 — Readiness Engine | ✅ V1 | Weighted scoring. Calibration criteria relaxed. |
| E6 — Livelihood Archetype Engine | ✅ V1 | K-Means on macro-categorized livelihood features. |
| Flask API | ✅ V1 | RESTful endpoints with validation and error handling. |
| SQLite Storage | ✅ V1 | Justified for report retrieval and demo audit trail. |
| Frontend | ✅ V1 | Vite + React. Two form workflows + results display. |
| PDF Reports | ✅ V1 | ReportLab-generated professional reports. |

---

## V2 Scope (Deferred)

The following items are explicitly deferred from V1:

| Item | Reason for Deferral |
| :--- | :--- |
| Full 88-feature Risk Tier model | Requires bureau API integration. Users cannot provide 81 of these features via a web form. |
| SHAP-based explainability | `treeinterpreter` is sufficient for V1. SHAP adds dependency weight and computation time for marginal interpretability gains on an 11-feature Random Forest. |
| Archetype engine using full bureau features | Same bureau API dependency. V1 clusters on user-knowable features only. |
| Income distribution harmonization | V1 documents the scale mismatch between Dataset A (synthetic) and Dataset C (realistic). Full resolution requires either collecting monthly income as a separate field or implementing a percentile-mapping layer. |
| Model retraining pipeline | No concept drift monitoring needed for a static demo dataset. |
| A/B testing framework | Single-model architecture in V1. |
| Multi-language support | English-only in V1. |
| Admin dashboard | Bank-employee interface deferred to V2. |
| User authentication | No login system in V1. |
| Real-time bureau API integration | Out of scope for a portfolio project. |

---

## Final Recommendation — Borrower Archetype Engine (E3) in V1

**Decision: KEEP E3 in V1 with modifications.**

### Why Keep It

1. **Portfolio value:** E3 is the only unsupervised learning component for Person A. Removing it reduces the project's ML breadth from 3 techniques (classification, clustering, rule-based scoring) to 2. For a college/resume project, demonstrating clustering adds significant value.

2. **The redundancy problem is solved:** With Credit_Score removed from the feature set, E3 clusters on behavioral and demographic dimensions (income, age, employment stability, education, household composition) that are genuinely orthogonal to the risk tier. A P2 borrower could be "Young Professional" or "Stable Established" — the archetype explains the *profile* behind the tier.

3. **The income scale mismatch is manageable:** The StandardScaler fitted on Dataset C's NETMONTHLYINCOME will normalize any input. For real users entering realistic Indian monthly incomes (₹15K–₹80K), the scaler produces valid z-scores. The mismatch only affects testing with Dataset A's synthetic income values (mean ₹4.2L/month), which should not be used to demo E3.

4. **Implementation cost is low:** K-Means with 6 features, StandardScaler, and cluster label mapping requires approximately 30 lines of core logic. The marginal effort to include E3 is small relative to the portfolio value gained.

### Modifications Applied

| Modification | Rationale |
| :--- | :--- |
| Credit_Score removed from clustering features (6 instead of 7) | Prevents archetype-tier redundancy |
| Silhouette threshold lowered to 0.15 | Removing the dominant variance axis produces softer cluster boundaries |
| Acceptance criteria requires clusters do NOT mirror risk tiers | Explicit validation of orthogonality |
| Income sensitivity documented as known limitation | Prevents incorrect demo inputs |
| Archetype descriptions explicitly labeled as descriptive | Not prescriptive or predictive |

### When to Reconsider

If during Task 5.1 training the resulting clusters produce silhouette score < 0.10 or the cluster centroids are indistinguishable on inspection, E3 should be demoted to a V2 item and replaced with a simpler rule-based borrower profile categorization based on income brackets and employment tenure.

---

## V1.1 Change Log

| # | Change | Section | Severity |
| :--- | :--- | :--- | :--- |
| C1 | Replaced fake feature contribution formula with `treeinterpreter` local explanations | Task 3.2 | Critical fix |
| C2 | Removed Credit_Score from Borrower Archetype clustering features (7 → 6) | Tasks 2.2, 5.1, 5.2 | Critical fix |
| C3 | Added macro-category mapping for `primary_business` (30+ → 4) and `loan_purpose` (37 → 4) before livelihood clustering | Task 2.3 | Medium fix |
| C4 | Removed distribution-forcing acceptance criteria from Readiness calibration | Task 6.2 | Medium fix |
| C5 | Added SQLite retention justification | Task 9.5 | Clarification |
| C6 | Added `treeinterpreter` to project dependencies | Task 1.1 | Dependency |
| C7 | Added V1/V2 scope tables and Archetype Engine final decision | New sections | Structural |
