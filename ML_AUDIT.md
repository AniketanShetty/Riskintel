# RiskIntel — ML Governance Audit

**Version:** 1.0
**Audit date:** 2026-06-06
**Scope:** Repository-wide ML governance review. No frontend, no styling.
**Inherits:** `FRONTEND_ARCHITECTURE_V1.1.md` (frozen backend, 317 tests passing)
**Auditor:** Senior ML Auditor, Risk Model Validator, Data Governance Reviewer

---

## 1. Executive Summary

RiskIntel is a loan decision-support system with **two distinct ML foundations**:

1. **Person A pipeline** — `RandomForestClassifier` (joblib artifact, 11 features) trained on `eligibility_data.csv` (4,269 rows). A separate `risk_tier_engine` applies static CIBIL thresholds to produce a tier label.
2. **Person B pipeline** — Pure rule-based `ReadinessEngine` (zero ML model artifacts in `models/readiness/`). The KMeans archetype model exists but is not used in production routing; production uses a deterministic string lookup (`livelihood_mapper.py`).
3. **Borrower archetype** — KMeans(4) on 4 features from `External_Cibil_Dataset.csv` (51,336 rows), but production routing uses string-keyed dictionary lookup, not the trained clusterer.

**The most serious finding is structural, not statistical.** The Person A training data appears to be **synthetically rule-generated**. Four independent forensic experiments agree:

| Experiment | Result | Source |
|---|---|---|
| f4 — Single Feature AUC | CIBIL alone = **0.968 AUC**. Status: WARNING | `experiments/metrics/f4_single_feature_auc.json` |
| f7 — Shallow Tree Forensics | Depth-1 tree = **0.972 AUC**; depth-2 = **0.996 AUC**. Verdict: LIKELY_RULE_GENERATED_DATA, FAIL | `experiments/metrics/f7_shallow_tree_metrics.csv` |
| f9 — SHAP Forensics | CIBIL contributes **79.72%** of total SHAP. Threshold behavior: LIKELY_SYNTHETIC_RULE | `experiments/metrics/f9_shap_verdict.json` |
| f1 — Target Leakage | CIBIL point-biserial correlation: **0.7705**; mutual information: **0.5079**. Highest of any feature. | `experiments/metrics/f1_leakage_summary.json` |
| f5 — Random Label Test | Mean shuffled-label AUC: **0.4935**. PASS. | `experiments/metrics/f5_random_label_auc.json` |
| f2 — Train/Test Contamination | 0 contaminated rows. PASS. | `experiments/metrics/f2_contamination_extended.json` |

**Interpretation:** The CIBIL score is mathematically a near-deterministic function of the loan_status label. A depth-2 decision tree reproduces the label at 99.6% AUC. The model has not learned multivariate financial behavior; it has rediscovered a single threshold on CIBIL. The full model AUC of 0.9988 is illusory: it is a Random Forest wrapper around what is effectively `if cibil_score > T: approve`.

**Person B is rule-based and is not a learned model.** This is a design choice, not a defect. The `ReadinessEngine` has explicit, auditable scoring rules and a documented `_FINANCIAL_HEALTH_FLOOR_THRESHOLD = 0.5` policy override (`readiness_engine.py:370`). It does not silently propagate training biases because it has no training set. It is, however, fragile to the *imputation logic* that proxies missing values (see §4.5).

**Calibration is not measured or maintained.** Probabilities from the Person A `RandomForestClassifier` are not calibrated post-training (no CalibratedClassifierCV, no Platt scaling, no isotonic regression, no `predict_proba` calibration check). The architecture's confidence frame is a single-line mono display of `probability` from `predict_proba`. Without calibration, the displayed 0.68 may be miscalibrated, and the floor-breach override decisions driven by it may be too frequent or too rare.

**Fairness controls are absent.** No demographic columns (gender, caste, religion, age band) appear in `eligibility_data.csv`. The feature set is clean on that axis. However:
- `risk_tier_thresholds.json` has only 4 hard tiers (P1 ≥ 701, P2 669–700, P4 ≤ 658, P3 = "fallback" for 659–668). CIBIL scores are correlated with socioeconomic status; using hard thresholds on CIBIL to gate P4 overrides is a **proxy for protected-class discrimination risk**.
- `risk_tier_engine.py:75-87` triggers `P4` rejection for "score ≤ 658" with no recourse mechanism and no disparate-impact audit.
- `f6_feature_semantics_verdict.json`: HIGH_LEAKAGE_RISK, 2 features flagged. `dependents` and `education` are flagged as "Fair Lending / ECOA Proxy Risk (Familial Status)" and "Fair Lending / Redlining Proxy Risk" respectively.

**Drift monitoring is absent.** No drift detection, no population-stability-index computation, no input-distribution monitoring, no prediction-distribution monitoring, no PSI thresholds, no alert paths. The 317-test backend has no tests for model drift, no scheduled re-training, no model-version pinning in production.

**Freeze readiness score: 31/100.** Critical findings block production.

---

## 2. Fairness Assessment

### F1. CRITICAL — Person A dataset lacks protected-class columns, but Person B and archetype datasets contain them, and they are linked to outcomes

**Evidence:**
- `data/processed/eligibility_data.csv` columns (header only): `dependents, education, self_employed, annual_income, loan_amount, loan_term, cibil_score, residential_assets_value, commercial_assets_value, luxury_assets_value, bank_asset_value, loan_status`. **No gender, caste, religion, age band, marital status.**
- `data/processed/readiness_data.csv` columns: `city, age, sex, social_class, primary_business, secondary_business, annual_income, monthly_expenses, old_dependents, young_dependents, home_ownership, type_of_house, occupants_count, house_area, sanitary_availability, water_availability, loan_purpose, loan_tenure, loan_installments, loan_amount`. **Sex and social_class present.**
- `data/raw/External_Cibil_Dataset.csv` (used for archetype KMeans): **GENDER, MARITALSTATUS, EDUCATION** all present.
- `experiments/scripts/f6_feature_semantics.py:35-40`: `education` is annotated "Fair Lending / Redlining Proxy Risk."
- `experiments/scripts/f6_feature_semantics.py:32-34`: `dependents` is annotated "Fair Lending / ECOA Proxy Risk (Familial Status)."

**Why this matters:** A protected-class feature absent from the *training* dataset does not mean the model is fair. The *archetype* training used `External_Cibil_Dataset.csv` which contains gender. While the production routing uses `livelihood_mapper.py` (string lookup, not the KMeans model), the *labels* in `borrower_archetype_definitions.json` ("Educated Professionals", "Highly Tenured Veterans", "Young Starters", "Mid-Career Established") were derived from KMeans clusters trained on gender-correlated features. The `Young Starters` cluster, in particular, may correlate with age and gender proxies.

**Severity:** CRITICAL.
**File:** `experiments/scripts/f6_feature_semantics.py:32-40`.

---

### F2. CRITICAL — `risk_tier_thresholds.json` uses hard CIBIL thresholds as a P4 override mechanism

**Evidence:**
- `data/processed/risk_tier_thresholds.json`: P1 ≥ 701, P2 669–700, P4 ≤ 658, P3 fallback for 659–668.
- `backend/app/orchestrator.py:142-144`: `if risk_tier_raw.get("risk_tier") == "P4" and eligibility_verdict in ("Highly Likely", "Likely"): eligibility_verdict = "Unlikely"; is_override = True; policy_override_flags.append("OVERRIDE_E2_P4_REJECTION")`.
- A borrower with CIBIL 658 receives P4 + automatic rejection override. A borrower with CIBIL 700 receives P2. **The threshold is on a continuous score without any demographic-adjusted variant.**

**Why this matters:** CIBIL scores in India correlate with income, caste, geography, and gender (documented in CIBIL annual reports and RBI working papers). A hard threshold on CIBIL is the textbook definition of a proxy for protected-class discrimination. There is no disparate-impact audit, no fairness metric (demographic parity, equalized odds), no recourse for borrowers near the boundary.

**Severity:** CRITICAL.
**Files:** `data/processed/risk_tier_thresholds.json:1-22`, `backend/app/orchestrator.py:138-144`.

---

### F3. HIGH — Recommendation logic generates advice that may differ across implicit subgroups

**Evidence:**
- `backend/app/engines/recommendation/rules_person_a.py:50-89`: All rules depend on top-N feature contributions from the model. The contributions are determined by the synthetic-rule model. If the model's threshold on CIBIL systematically denies certain CIBIL ranges more than others, the advice differs.
- `backend/app/engines/recommendation/rules_person_b.py:11-15`: `has_low_component` is sorted and the two lowest-scoring components are flagged. **The selection is rank-based, not threshold-based.** A borrower with components at 50, 51, 80, 80, 80 gets the same "low" flag as a borrower at 5, 6, 90, 90, 90.
- `rules_person_b.py:46-50`: "Financial health indicators show limited debt absorption capacity" — generic phrasing, no applicant-specific quantification. A loan officer cannot act on this without re-reading the breakdown.

**Why this matters:** A loan officer's behavior is shaped by the recommendation. If the recommendation is biased by the model, the bias propagates through the human-in-the-loop.

**Severity:** HIGH.
**File:** `backend/app/engines/recommendation/rules_person_b.py:9-15`.

---

### F4. MEDIUM — `livelihood_mapper.py` cluster 0 ("General Micro-Enterprise") is a default that obscures subgroup

**Evidence:**
- `backend/app/engines/livelihood/livelihood_mapper.py:78-79`: If `primary_business` is not in the dictionary, the function returns `ARCHETYPES[0]`, the catch-all cluster.
- The dictionary has 100+ entries across 5 clusters (Trade & Retail, Services, Agri-Allied, Manufacturing, Transport & Logistics).
- Borrowers whose business is not in the dictionary (e.g., "computer repair", "tutoring center", "boutique") are silently classified as "Unclassified or general small-scale business activity" (`livelihood_mapper.py:7`).

**Why this matters:** Catch-all clusters in unsupervised classification are a known source of bias. The catch-all cluster averages over heterogeneous businesses, and the "description" applied to the borrower is "Unclassified." This is misclassification, not just a label.

**Severity:** MEDIUM.
**File:** `backend/app/engines/livelihood/livelihood_mapper.py:38-67, 78-85`.

---

### F5. MEDIUM — No fairness metrics computed or stored

**Evidence:**
- 13 forensic experiment scripts in `experiments/scripts/` (f0–f12). None compute demographic parity, equalized odds, disparate impact, or any other fairness metric.
- The `run_all_experiments.py` orchestrator at lines 6-14 runs f0–f6 only. The fairness-relevant experiments (f6 feature semantics) run, but f6 only annotates *risk*; it does not measure fairness.
- The 317-test backend has no fairness tests.

**Why this matters:** Fairness cannot be assured without measurement. The absence of measurement is the finding.

**Severity:** MEDIUM.
**Files:** `experiments/run_all_experiments.py:6-14`, all `experiments/scripts/f*` files.

---

## 3. Calibration Assessment

### C1. CRITICAL — Probabilities are not calibrated; the displayed confidence is uncalibrated

**Evidence:**
- `backend/app/engines/eligibility/eligibility_engine.py:101-106`: The function calls `ti.predict(self.model, df)` and returns `prob = float(prediction[0][pos_idx])`. This is a `RandomForestClassifier.predict_proba` average, which is **not calibrated by default**.
- The model's predicted probability is rounded to 4 decimals (`eligibility_engine.py:126`).
- No `CalibratedClassifierCV`, no `sklearn.calibration.calibration_curve`, no `Brier score`, no `expected_calibration_error` is computed anywhere in the codebase.
- The orchestrator's confidence frame (`orchestrator.py`) displays `probability` directly. Loan officers see `0.68 probability` and act on it. If the model is miscalibrated, the loan officer is misled.
- The verdict thresholds (`eligibility_engine.py:115-122`) are hardcoded at 0.80, 0.60, 0.40 with no justification. If the model's output is miscalibrated, these boundaries are arbitrary.

**Why this matters:** A "probability" that is uncalibrated is a score, not a probability. Calling it a probability implies a frequentist interpretation ("this borrower will repay 68% of the time") that is not supported by the data.

**Severity:** CRITICAL.
**File:** `backend/app/engines/eligibility/eligibility_engine.py:101-129`.

---

### C2. HIGH — Verdict thresholds are arbitrary and not derived from calibration

**Evidence:**
- `backend/app/engines/eligibility/eligibility_engine.py:115-122`: `if prob >= 0.80: "Highly Likely"; elif prob >= 0.60: "Likely"; elif prob >= 0.40: "Borderline"; else: "Unlikely"`.
- These thresholds do not correspond to any measured risk band. They are author-intuition values.
- The `risk_tier_thresholds.json` has its own thresholds (701, 669, 658), which are not coordinated with the eligibility engine's probability thresholds.
- The `OVERRIDE_E2_P4_REJECTION` flag in `orchestrator.py:142-144` is fired by `risk_tier`, not by `eligibility`. Two threshold systems exist, neither calibrated to a real-world cost-of-error ratio.

**Why this matters:** Risk decisioning requires threshold calibration against the institution's actual loss tolerance. The current thresholds are hardcoded and uncalibrated.

**Severity:** HIGH.
**File:** `backend/app/engines/eligibility/eligibility_engine.py:115-122`.

---

### C3. MEDIUM — No reliability diagram, no calibration plot in experiment outputs

**Evidence:**
- `experiments/scripts/` directory does not contain a `calibration.py` script.
- `experiments/metrics/` does not contain a `*calibration*` or `*brier*` file.
- `experiments/plots/` does not contain a reliability diagram.

**Severity:** MEDIUM.

---

## 4. Data Quality Assessment

### D1. CRITICAL — Person A training data appears to be synthetically rule-generated from CIBIL

**Evidence (the four-way forensic convergence):**
- `experiments/metrics/f4_single_feature_auc.json`: `rf_cibil_auc: 0.9681`, `full_model_auc: 0.9988`, status `WARNING`.
- `experiments/metrics/f7_shallow_tree_metrics.csv`: depth-1 tree achieves `roc_auc: 0.972`, depth-2 tree achieves `roc_auc: 0.996`. Per `f7_label_generation_forensics.py:142-153`, an AUC > 0.95 at depth 4 indicates LIKELY_RULE_GENERATED_DATA.
- `experiments/metrics/f9_shap_verdict.json`: `top_feature: cibil_score`, `top_feature_pct_contribution: 79.72`, verdict `WARNING`, threshold_behavior `LIKELY_SYNTHETIC_RULE`.
- `experiments/metrics/f1_leakage_summary.json`: `max_corr_feature: cibil_score`, `max_corr_value: 0.7705`, `max_mi_feature: cibil_score`, `max_mi_value: 0.5079`.
- `experiments/metrics/f6_feature_semantics_verdict.json`: verdict `HIGH_LEAKAGE_RISK`, `high_risk_features_count: 2`.

**Interpretation:** The Person A `loan_status` label in `eligibility_data.csv` is, with very high probability, generated by a deterministic rule on CIBIL and a small set of secondary features. The model has not learned multivariate financial behavior; it has learned a lookup table. **Deploying this model in production means deploying the original rule, plus a wrapper that obscures what the rule is doing.**

**Severity:** CRITICAL.
**Files:** `experiments/metrics/f4_single_feature_auc.json`, `f7_shallow_tree_metrics.csv`, `f9_shap_verdict.json`, `f1_leakage_summary.json`, `f6_feature_semantics_verdict.json`.

---

### D2. CRITICAL — CIBIL scores are quasi-leaky: they may include the default event of the loan being scored

**Evidence:**
- `experiments/scripts/f6_feature_semantics.py:14-19`: `cibil_score` is annotated with `Potential Leakage Risk: High`. The notes state: "EXTREME RISK: Bureau scores update dynamically. If this data was pulled recently, it includes the default event of this very loan."
- The Person A `eligibility_data.csv` contains `loan_status` and `cibil_score` for the same row. The bureau score in the row may have been pulled *after* the loan decision and the eventual default, encoding the outcome into the feature.
- No temporal split is performed in training. `experiments/scripts/f2_contamination.py:39-40` does a random `train_test_split` with `random_state=42`. There is no `test_set` that is **temporally later** than the training set. If the CIBIL score updates post-loan, the random split leaks outcome into features.

**Why this matters:** Temporal leakage in credit data is a documented industry problem. The current training methodology does not defend against it.

**Severity:** CRITICAL.
**Files:** `experiments/scripts/f6_feature_semantics.py:14-19`, `experiments/scripts/f2_contamination.py:39-40`, `backend/app/engines/eligibility/eligibility_engine.py:90`.

---

### D3. HIGH — Class imbalance is severe in `External_Cibil_Dataset.csv` (used for archetype training)

**Evidence:**
- `External_Cibil_Dataset.csv` (51,336 rows): `Approved_Flag` distribution: `P2: 32199 (62.7%)`, `P3: 7452 (14.5%)`, `P4: 5882 (11.5%)`, `P1: 5803 (11.3%)`. P2 is the majority class.
- The KMeans(4) archetype training (`train_borrower_archetype.py:55-57`) does not stratify, does not check class balance, and uses 4 features that include EDUCATION.
- GENDER distribution: `M: 45245 (88.1%)`, `F: 6091 (11.9%)`. **Imbalanced by gender.**

**Why this matters:** The cluster definitions ("Educated Professionals", "Highly Tenured Veterans", "Young Starters", "Mid-Career Established") are derived from imbalanced data. "Young Starters" likely correlates with gender and low-education proxies. Even though production routing uses string lookup, the label vocabulary itself was derived from biased data.

**Severity:** HIGH.
**Files:** `scripts/train_borrower_archetype.py:36-83`, `data/raw/External_Cibil_Dataset.csv` (class distribution confirmed by inspection).

---

### D4. HIGH — `eligibility_data.csv` and `External_Cibil_Dataset.csv` are likely the same source or related, with potential ID leakage across training/inference

**Evidence:**
- `experiments/scripts/f2_contamination.py:39-40`: trains a Random Forest and reports 0% train/test contamination. The contamination check uses canonical row hashing. A 0% result is plausible if the random split is well-shuffled. **It does not rule out cross-dataset contamination.**
- `data/raw/` contains 14 separate CSV files including `BOB.csv` (Bank of Baroda), `IDBI.csv`, `PNB1.csv`, `Syndicate.csv`, `External_Cibil_Dataset.csv`, `Internal_Bank_Dataset.csv`, `loan_approval_dataset.csv`, `test_modified.csv`, `train_modified.csv`. Many of these are likely training-set variants.
- No `data/provenance.json` or `data/lineage.json` describes where `eligibility_data.csv` came from or how it was constructed.
- `experiments/scripts/utils_manifest.py` (referenced in scripts but not read in this audit) appears to track script runs, not data lineage.

**Severity:** HIGH.

---

### D5. MEDIUM — Datasets have no schema versioning or hash-based immutability

**Evidence:**
- `data/processed/eligibility_data.csv` is a flat CSV with no header comment indicating version, build date, or source.
- `experiments/scripts/utils_hashing.py` exists and provides `canonical_hash_dataframe`, but it is only used for train/test contamination checks within a single run, not for cross-run immutability.
- The 4,269-row `eligibility_data.csv` could be silently replaced with a different 4,269-row CSV and the model would not detect the swap.

**Severity:** MEDIUM.
**Files:** `data/processed/eligibility_data.csv`, `experiments/scripts/utils_hashing.py`.

---

### D6. MEDIUM — `imputed_fields` in readiness engine uses default proxies without borrower-specific validation

**Evidence:**
- `backend/app/engines/readiness/readiness_engine.py:107-113`: If `house_area_raw` is NaN, default to 450 sq ft. If `secondary_business` is "none" or NaN, default to "none".
- `readiness_engine.py:222-225`: Income imputation uses `monthly_expenses` to compute a proxy when `annual_income` is missing or 0. The proxy logic is not exposed to the loan officer as a data-quality flag in the API response, although the architecture's input contract mentions a "imputed" indicator.
- `backend/app/engines/recommendation/rules_person_b.py:7-15` selects the two lowest-scoring components as "improvement areas," regardless of whether the low score is due to imputation.

**Why this matters:** A borrower with no income data receives a proxy-derived score. The proxy is treated as real. The recommendation engine then flags "financial health" as the improvement area, which may be misattributed.

**Severity:** MEDIUM.
**File:** `backend/app/engines/readiness/readiness_engine.py:107-225`.

---

## 5. Explainability Assessment

### E1. MEDIUM — `treeinterpreter` provides feature contributions, but not enough for borrower-level explanation

**Evidence:**
- `backend/app/engines/eligibility/eligibility_engine.py:100-112`: Uses `ti.predict(self.model, df)` to return per-feature contributions.
- The output is `feature_contributions: {col: value}`. There is no sign convention, no narrative, no per-feature percentile, no comparison to a population baseline.
- `experiments/scripts/f9_shap_forensics.py` exists and would provide better per-feature attribution, but it is **not called in production**. The production engine uses `treeinterpreter`, which provides a similar but not identical attribution. There is no documented choice of which method is canonical.
- `experiments/scripts/f9_permutation_importance.py` exists, also not called in production.

**Severity:** MEDIUM.
**File:** `backend/app/engines/eligibility/eligibility_engine.py:100-129`.

---

### E2. MEDIUM — Recommendation rules are deterministic and reviewable, but the rationale chain is not exposed to the loan officer

**Evidence:**
- `backend/app/engines/recommendation/rules_person_a.py` and `rules_person_b.py` define rules with explicit conditions. The code is auditable.
- `recommendation_engine.py:18, 25`: The response includes `triggered_rule_ids`. The architecture's API contract surface includes this field, and the audit log captures the IDs.
- The loan officer does not see *why* a rule triggered in plain language. The rule ID is logged but the rationale string is the only human-readable explanation. If the rationale is generic (e.g., "Financial health indicators show limited debt absorption capacity"), the loan officer cannot defend it to the borrower.

**Severity:** MEDIUM.
**Files:** `backend/app/engines/recommendation/rules_person_b.py:46-50`, `recommendation_engine.py:17-25`.

---

### E3. MEDIUM — Archetype cluster names are narrative labels, not cluster IDs

**Evidence:**
- `data/processed/borrower_archetype_definitions.json` maps cluster IDs (0–3) to narrative labels.
- `backend/app/engines/archetype/borrower_archetype_engine.py:110`: Returns `archetype_label: "Educated Professionals"` (or similar narrative string). The cluster ID is also returned, but the loan officer sees the label first.
- The narrative label embeds a value judgment ("Educated Professionals", "Young Starters") that may bias the loan officer against the borrower before they read the data.

**Why this matters:** Narrative labels are first-class artifacts in the explanation. They are not neutral.

**Severity:** MEDIUM.
**Files:** `data/processed/borrower_archetype_definitions.json`, `backend/app/engines/archetype/borrower_archetype_engine.py:108-115`.

---

### E4. LOW — Engine trace logs are minimal and do not include the model version used for the decision

**Evidence:**
- `backend/app/orchestrator.py:81-83`: `engine_statuses = {}` is populated per engine but does not include model version or commit hash.
- The audit log captures model lineage at the *system* level (in `model_lineage_bind`), but not at the *per-decision* level.
- If the model is updated, a historical decision cannot be reproduced from the audit log alone.

**Severity:** LOW.
**File:** `backend/app/orchestrator.py:80-83`.

---

## 6. Production Risk Assessment

### P1. CRITICAL — Zero drift monitoring in production

**Evidence:**
- No drift detection (PSI, KS test, feature distribution shift) is implemented anywhere in `backend/app/`.
- No input monitoring (i.e., is the live distribution of `cibil_score` the same as the training distribution?).
- No output monitoring (i.e., is the live distribution of verdicts the same as the training distribution?).
- No alerting thresholds.
- No scheduled re-training.
- No model version pinning in the served artifact. The joblib file is loaded directly; the model file path is the only version identifier.

**Why this matters:** Credit markets shift. COVID-era India saw 90-day delinquencies rise from 1.5% to 4% in months. A model trained on pre-COVID data will silently misfire in a post-COVID distribution. Without drift monitoring, the institution learns about the drift from defaults, not from the model.

**Severity:** CRITICAL.
**Files:** entire `backend/app/` tree (absent feature).

---

### P2. CRITICAL — No model version pin or fallback policy

**Evidence:**
- `backend/app/engines/eligibility/eligibility_engine.py:32-49`: The model is loaded from `models/eligibility/random_forest.joblib` at engine construction. There is no version check, no minimum version, no SHA verification.
- `models/eligibility/random_forest.joblib` is the only model artifact. Its version, training date, and training data hash are stored separately in `model_lineage_bind` (read by `app/lineage.py`), but the engine does not verify that the loaded file matches the declared lineage.
- If the artifact is replaced (intentionally or otherwise), the engine silently uses the new model.

**Severity:** CRITICAL.
**Files:** `backend/app/engines/eligibility/eligibility_engine.py:32-49`, `backend/app/lineage.py` (referenced but not read in this audit).

---

### P3. HIGH — No input validation against training distribution (out-of-distribution handling)

**Evidence:**
- `backend/app/engines/eligibility/eligibility_engine.py:84-94`: Inputs are coerced via `int()` and `float()` with `0` defaults. A missing `cibil_score` is treated as 0, which falls into P4 territory. **This is silent imputation at the inference layer.**
- The readiness engine (`readiness_engine.py:82-95`) raises `ValueError` on NaN and Infinity but coerces `None` to 0 in many places (e.g., `float(features.get("annual_income", 0))`).
- There is no out-of-distribution detection. A borrower with `cibil_score = 900` (outside any training observation) receives a probability from the same model that produced the training distribution's tail.

**Severity:** HIGH.
**File:** `backend/app/engines/eligibility/eligibility_engine.py:84-94`.

---

### P4. HIGH — No test for model reproducibility or bit-exact inference

**Evidence:**
- The 317 backend tests (`backend/tests/`) cover orchestrator, eligibility, risk_tier, archetype, readiness, recommendations, report generation.
- `backend/tests/test_orchestrator.py` and `test_e2e_*.py` test the orchestration, not the trained model.
- No test loads the model, runs a fixed input, and asserts a fixed output. **The model's predictions are not unit-tested for reproducibility.**
- The joblib file could be replaced, and no test would fail.

**Severity:** HIGH.

---

### P5. MEDIUM — `random_state=42` is hardcoded across all experiments, with no test for seed sensitivity

**Evidence:**
- `experiments/scripts/f4_single_feature_auc.py:25, 31, 37, 79`: `random_state=42` in every model and every split.
- `experiments/scripts/f5_random_label_test.py:56, 60, 63`: `np.random.seed(42 + i)`, `random_state=42 + i`.
- `scripts/train_borrower_archetype.py:56`: `KMeans(n_clusters=4, random_state=42)`.
- No experiment reports seed sensitivity. If `random_state=42` happens to favor a particular feature, no other seed has been tested.

**Severity:** MEDIUM.
**Files:** multiple in `experiments/scripts/`.

---

### P6. MEDIUM — No data quality flag at the API surface for imputed fields

**Evidence:**
- `backend/app/engines/readiness/readiness_engine.py:107-113` and elsewhere: Imputed fields are marked in the response (`imputed_fields` list), but the architecture's API contract does not require this in the response shape.
- The orchestrator forwards `imputed_fields` if the engine returns it, but there is no contract test asserting that the field is present.
- A loan officer cannot tell from the API response whether the readiness score is based on real or imputed data.

**Severity:** MEDIUM.

---

### P7. MEDIUM — `treeinterpreter` polyfill for Python 3.12+ in eligibility engine

**Evidence:**
- `backend/app/engines/eligibility/eligibility_engine.py:13-23`: A custom `LooseVersion` polyfill is defined in-place because `treeinterpreter` depends on `distutils`, which was removed in Python 3.12.
- This is a maintenance liability. The polyfill may not match future `LooseVersion` semantics.
- No test verifies the polyfill's behavior. If `LooseVersion` semantics change in a future Python release, the polyfill will silently drift.

**Severity:** MEDIUM.
**File:** `backend/app/engines/eligibility/eligibility_engine.py:13-23`.

---

## 7. Missing Controls

The following are absent from the codebase. Each is a control that, by industry practice, should exist in a production credit decisioning system. Their absence is a finding, not a defect — the institution must decide whether to add them.

### MC1. CRITICAL — No fairness audit
No demographic-parity, equalized-odds, or disparate-impact computation anywhere in the codebase. `experiments/scripts/` has no such script. The 317 tests have no fairness test.

### MC2. CRITICAL — No calibration monitoring
No `expected_calibration_error`, no Brier score decomposition, no reliability diagram in production. The `predict_proba` output is consumed as-is.

### MC3. CRITICAL — No drift detection
No PSI, KS test, or feature-distribution shift detection. No input drift, no output drift, no concept drift. No alerting.

### MC4. HIGH — No model registry with version pinning
The model is loaded by file path. The lineage metadata in `borrower_archetype_definitions.json` and `risk_tier_thresholds.json` is treated as the source of truth, but the served model is not verified against it.

### MC5. HIGH — No shadow mode / champion-challenger
A new model version cannot be A/B tested against the current version. There is no infrastructure for it.

### MC6. HIGH — No feature importance / SHAP at inference
Production uses `treeinterpreter`, not SHAP. The two methods can disagree on attribution. No canonical choice is documented.

### MC7. MEDIUM — No data lineage for `eligibility_data.csv`
No `data/provenance.json`, no `data/lineage.json`, no script that documents how the dataset was constructed. The forensics scripts (f7, f9) conclude the labels are likely rule-generated, but there is no upstream documentation of the source.

### MC8. MEDIUM — No test of recommendation rules
`backend/tests/test_orchestrator.py` and `test_recommendation.py` (if it exists) test the engine output. No test verifies the rule *content* against a senior credit analyst's review.

### MC9. MEDIUM — No protected-class suppression in the audit log
`backend/app/audit.py:write_audit_record` writes the record, the verdict, the engine statuses, the override flags. It does not write the input features themselves. This is a privacy-positive default, but it also means post-hoc fairness audits cannot be performed on the audit log without a separate feature store.

### MC10. LOW — No documentation of model assumptions
No `MODEL_CARD.md`, no `MODEL_INTENT.md`, no `KNOWN_LIMITATIONS.md` for the eligibility model. The institution cannot communicate to a regulator or a borrower what the model does and does not know.

---

## 8. Recommended Fixes

In priority order. Each fix addresses one or more findings above.

### Fix 1 — Replace the synthetic-rule training data (CRITICAL — F1, D1, D2)

**Action:** Source a new Person A training set that:
- Contains real-world loan performance data (outcome measured 6–12 months after origination, not at origination time).
- Splits temporally (training: loans originated before T; test: loans originated between T and T+6mo).
- Does not include CIBIL scores pulled after the loan outcome.
- Is at least 50,000 rows with < 30% missingness in any feature.

**Owner:** Data team, with risk validation.
**Effort:** 6–12 weeks.

### Fix 2 — Add calibration layer (CRITICAL — C1, C2, P3)

**Action:** Wrap `predict_proba` output in `sklearn.calibration.CalibratedClassifierCV` with isotonic or Platt scaling, fit on a held-out calibration set. Add a `reliability_diagram` script to `experiments/`. Add a Brier score to the audit log.

**Owner:** ML team.
**Effort:** 1 week.

### Fix 3 — Add fairness audit (CRITICAL — F1, F2, F3, MC1)

**Action:** Add an `experiments/scripts/f13_fairness.py` script that computes:
- Demographic parity across `gender`, `social_class`, `urban/rural` for each verdict band.
- Equalized odds across the same dimensions.
- Disparate impact (4/5 rule) for the P4 override rate.
- A mock demographic column must be added to `eligibility_data.csv` (synthetic but realistic) for testing.

**Owner:** ML team + risk validation.
**Effort:** 2 weeks.

### Fix 4 — Add drift monitoring (CRITICAL — P1, MC3)

**Action:** Add a drift service that:
- Logs feature distribution summary statistics hourly.
- Computes PSI weekly.
- Triggers an alert when PSI > 0.2 on any feature.
- Logs prediction distribution summary statistics.
- Emits a model-drift event to the audit log.

**Owner:** Platform team.
**Effort:** 3 weeks.

### Fix 5 — Add model version pinning (CRITICAL — P2, MC4)

**Action:** Store a SHA-256 of the model artifact at training time. At inference, verify the loaded artifact's SHA matches the declared SHA. Refuse to serve if mismatched. Add a `model_version` field to the audit log per decision.

**Owner:** ML team + platform.
**Effort:** 1 week.

### Fix 6 — Add out-of-distribution detection (HIGH — P3, D6)

**Action:** For each input feature, compare the live value against the training distribution (min, max, 1st/99th percentile). If outside, return an `OUT_OF_DISTRIBUTION` error envelope and refuse the assessment. Do not silently impute 0.

**Owner:** ML team.
**Effort:** 1 week.

### Fix 7 — Add temporal split to training (HIGH — D2)

**Action:** Refactor all training scripts to use `train_test_split` with a `date` column, not random. Document the temporal cut-off in the model card.

**Owner:** Data team.
**Effort:** 2 weeks.

### Fix 8 — Add a model card (MEDIUM — MC10)

**Action:** Write `MODEL_CARD.md` per model (eligibility, archetype). Include: intended use, out-of-scope use, training data summary, performance metrics on holdout, fairness metrics, known limitations, retraining cadence.

**Owner:** ML team.
**Effort:** 1 week.

### Fix 9 — Add protected-class suppression at feature level (MEDIUM — F1, F4, E3)

**Action:** Add a `PROHIBITED_FEATURES` set in the engine configuration. Refuse to compute any engine output if a prohibited feature is in the request. Strip the feature from logs and audit entries. Add a `f14_prohibited_features.py` test.

**Owner:** ML team + security.
**Effort:** 1 week.

### Fix 10 — Add rule content review (MEDIUM — MC8)

**Action:** Have a senior credit analyst review every rule in `rules_person_a.py` and `rules_person_b.py`. Annotate each rule with `last_reviewed_by` and `last_reviewed_at`. Add to the audit metadata.

**Owner:** Credit policy team.
**Effort:** 1 week.

### Fix 11 — Recalibrate the verdict thresholds (HIGH — C2, P3)

**Action:** Replace hardcoded `0.80 / 0.60 / 0.40` thresholds with institution-policy-derived thresholds. Document the cost-of-error ratio used to derive them. Add them to the model card.

**Owner:** Risk + credit policy.
**Effort:** 2 weeks.

### Fix 12 — Add data lineage for `eligibility_data.csv` (MEDIUM — MC7)

**Action:** Generate `data/processed/eligibility_data.csv.provenance.json` containing: source dataset(s), build script, build date, row count, column-level missingness, hash.

**Owner:** Data team.
**Effort:** 3 days.

---

## 9. Freeze Readiness Score

**Score: 31/100.**

| Dimension | Score (out of 10) | Justification |
|---|---|---|
| Training data quality | 2 | Synthetic-rule labels per f7, f9. Quasi-leaky CIBIL per f6. |
| Feature engineering | 5 | No prohibited features in eligibility_data. Imputation in readiness is silent. |
| Model training | 4 | Random split, no temporal split. Hardcoded seeds. No calibration. |
| Model evaluation | 6 | Forensic suite exists (f0–f12). No fairness, calibration, or drift metrics. |
| Calibration | 1 | Uncalibrated probabilities consumed as confidence. |
| Fairness | 2 | No demographic data, no fairness metrics, hard CIBIL thresholds. |
| Bias risks | 2 | Catch-all archetype cluster, narrative labels bias, recommendation rules generic. |
| Explainability | 5 | `treeinterpreter` per-decision. Rule IDs in audit log. No SHAP at inference. |
| Drift readiness | 0 | No drift detection, no monitoring, no alerting. |
| Threshold design | 3 | Hardcoded. Not calibrated. Not policy-derived. |
| Production ML risks | 4 | No version pin, no OOD detection, no reproducibility test. |

**Weighted by severity:** 4 Criticals (F1, F2, C1, D1, D2, P1, P2) each cap a sub-score at ≤ 3. The synthetic-rule data finding alone (D1) would prevent a senior model validator from approving the model for production.

**Recommendation:** **DO NOT FREEZE.** Fix the Critical findings before declaring the backend production-ready for new geographies or new borrower segments. The current freeze is acceptable for a *v1.0 demo* of the architecture. The product must not be deployed to a new institution or a new loan product line without first completing Fix 1 (real data), Fix 2 (calibration), Fix 3 (fairness), Fix 4 (drift), and Fix 5 (version pinning).

**Re-audit recommended:** after Fixes 1–5 are complete, before v2.0.
