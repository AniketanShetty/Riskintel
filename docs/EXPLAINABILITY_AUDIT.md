# RiskIntel — Explainability Audit

**Version:** 1.0
**Date:** 2026-06-06
**Scope:** Can a loan officer explain, reproduce, justify, and defend every RiskIntel output?
**Inherits:** [ML_AUDIT.md](ML_AUDIT.md), [ML_AUDIT_PHASE_2.md](ML_AUDIT_PHASE_2.md), [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md), [DATA_PROVENANCE_AUDIT.md](DATA_PROVENANCE_AUDIT.md), [FAIRNESS_AUDIT_FIRST_TIME_BORROWERS.md](FAIRNESS_AUDIT_FIRST_TIME_BORROWERS.md).
**Method:** Read-only. Engine code re-read. Transformation path traced. Reproduction test executed. Output truthfulness verified.
**No code modified.**

---

## 1. Summary Verdict

| Engine | Explained? | Reproduced? | Justified to regulator? | Challenged by customer? | Grade |
|---|---|---|---|---|---|
| E1 Eligibility | Partial | Partial | NO | NO | **RED** |
| E2 Risk Tier | YES | YES | Partial | NO | **YELLOW** |
| E3 Borrower Archetype | NO | NO | NO | NO | **RED** |
| E5 Readiness | YES | YES | Partial | Partial | **YELLOW** |
| E6 Livelihood | YES | YES | YES | Partial | **GREEN** |

**Composite grade: 2 RED, 2 YELLOW, 1 GREEN.** E1 and E3 are not production-suitable for explainability. E2 and E5 are explainable in code but not defensible to a regulator without model card documentation. E6 is the only engine that is fully explainable.

---

## 2. E1 — Eligibility Engine

### 2.1 Input fields used

`backend/app/engines/eligibility/eligibility_engine.py:74-94`. Eleven features:

```
dependents, education, self_employed, annual_income, loan_amount,
loan_term, cibil_score, residential_assets_value, commercial_assets_value,
luxury_assets_value, bank_asset_value
```

### 2.2 Transformation steps

`eligibility_engine.py:62-95`:

1. `education` is coerced to 1 if "graduate" else 0.
2. `self_employed` is coerced to 1 if "yes" else 0.
3. `dependents` cast to `int`, `0` default.
4. Income / loan / assets / CIBIL all cast to `float`, `0` default.
5. DataFrame built in a **fixed column order** (line 75-80).
6. `ti.predict(self.model, df)` is called — the `treeinterpreter` library returns per-feature contributions.
7. Probability is rounded to 4 decimals.
8. Verdict is bucketed by hard thresholds at 0.80, 0.60, 0.40 (line 115-122).

### 2.3 Thresholds

`eligibility_engine.py:115-122`:

```
prob >= 0.80 → "Highly Likely"
prob >= 0.60 → "Likely"
prob >= 0.40 → "Borderline"
else         → "Unlikely"
```

### 2.4 Rules

None. E1 is a Random Forest wrapper. The model is a 100-tree ensemble, with `max_depth=10`, `random_state=42` (per `backend/app/engines/eligibility/train.py:27`).

### 2.5 Output generation path

1. `treeinterpreter` decomposes prediction into bias + per-feature contributions.
2. Per-feature contributions are returned as `feature_contributions` (raw floats, 4-decimal precision).
3. Verdict is a function of the scalar probability, not the contributions.
4. The model output is wrapped in an envelope with the verdict, probability, bias, and contributions.

### 2.6 Reproduction

The model is **not** a deterministic function for two reasons:

1. **Non-monotonic probability in the CIBIL sweep** (per the prior audit): CIBIL=600 → 0.6189; CIBIL=700 → 0.6289; CIBIL=800 → 0.5989. The model is reproducible **per-input** (joblib is deterministic for a fixed `random_state=42`), but the **decision boundary is unstable**: a borrower who improves their CIBIL from 700 to 800 sees their approval probability drop by 0.030. **The same person with a strictly better bureau record receives a strictly worse probability.**
2. **Unhandled exceptions at 7 of 17 CIBIL values** (CIBIL ∈ {100, 200, 300, 500, 540, 900, 1000}). A first-time borrower with a bureau score in the failure range cannot be assessed. The orchestrator raises `CriticalEngineError` and the audit log receives no row.

The model itself is reproducible on any given input. The **decision** is not stable across the input space.

### 2.7 Justification to a regulator

**No.**

1. The probabilities are **uncalibrated** (per [ML_AUDIT.md](ML_AUDIT.md) C1). The displayed `0.68 probability` is not a true probability of any event. The model is a wrapper around `cibil_score >= 549.5 → approve`. Per [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md) §3, this is documented.
2. The CIBIL score is **quasi-leaky** (per [ML_AUDIT.md](ML_AUDIT.md) D2): the bureau score may include the outcome of the loan being scored. A regulator asking "why was this borrower approved or denied" will receive an answer that includes a feature that may have encoded the outcome.
3. The model is trained on **synthetic-rule data** (per [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md) D1). A regulator asking "what does the model know" will receive an answer that does not correspond to real borrower behavior.
4. The `feature_contributions` are **not economic signals** (per [FAIRNESS_AUDIT_FIRST_TIME_BORROWERS.md](FAIRNESS_AUDIT_FIRST_TIME_BORROWERS.md) F6). A regulator asking why `luxury_assets_value: -0.1353` contributed negatively to a borrower with zero luxury assets will receive no answer.
5. The training data has **no documented provenance or license** (per [DATA_PROVENANCE_AUDIT.md](DATA_PROVENANCE_AUDIT.md) §6.1). A regulator asking "what is the basis for this model" will be told the data came from an unspecified source.

### 2.8 Customer challenge

**No.** The customer receives a verdict and (in the architecture's design) a set of feature contributions. The contributions include negative numbers for assets the customer declared as zero. The customer cannot challenge a number derived from a `treeinterpreter` decomposition of a model trained on synthetic data.

**Grade: RED.** E1 produces an output that is technically reproducible per-input but cannot be explained in plain language, cannot be justified to a regulator with a documented model card, and cannot be challenged by a customer with an intelligible counter-argument.

---

## 3. E2 — Risk Tier Engine

### 3.1 Input fields used

`backend/app/engines/risk_tier/risk_tier_engine.py:49-87`. **One field:** `score` (integer CIBIL score).

### 3.2 Transformation steps

`risk_tier_engine.py:60-87`:

1. Compare integer score to thresholds.
2. Return `{risk_tier, tier_description}` from `risk_tier_thresholds.json`.

### 3.3 Thresholds

`data/processed/risk_tier_thresholds.json`:

```json
"P1": "score >= 701"
"P2": "669 <= score < 701"
"P3": "fallback for 659 <= score < 669"
"P4": "score <= 658"
```

### 3.4 Rules

None. E2 is a deterministic lookup.

### 3.5 Output generation path

Trivial. The output is one of four tier labels.

### 3.6 Reproduction

**YES.** E2 is a pure function. Given a CIBIL score, the tier is deterministic.

### 3.7 Justification to a regulator

**Partial.** A regulator can be shown the threshold file, the threshold definitions, and the rationale (P1 = Low Risk, P2 = Moderate, P3 = Elevated, P4 = High). However:

- The thresholds are **not derived from observed default rates** (per [ML_AUDIT.md](ML_AUDIT.md) F2). The 701/669/658 cutoffs are hand-authored, not policy-derived.
- The P4 override at `orchestrator.py:142-144` is **not calibrated to a cost-of-error ratio**.
- There is **no disparate-impact audit** (per [ML_AUDIT.md](ML_AUDIT.md) F5).
- CIBIL is a **quasi-leaky feature** (per [ML_AUDIT.md](ML_AUDIT.md) D2).

A regulator asking "why P4" can be told "CIBIL ≤ 658" but cannot be told "the 658 threshold was chosen because of observed default rates" — because no such observation exists.

### 3.8 Customer challenge

**No.** A P4 customer is told "high risk" with no further explanation. The threshold file does not include a customer-readable rationale. There is no recourse mechanism in E2.

**Grade: YELLOW.** E2 is technically reproducible and explainable in code, but the threshold values are not documented as policy-derived and there is no customer recourse path.

---

## 4. E3 — Borrower Archetype Engine

### 4.1 Input fields used

`backend/app/engines/archetype/borrower_archetype_engine.py:78-101`. Four features:

```
NETMONTHLYINCOME, AGE, Time_With_Curr_Empr, EDUCATION (ordinal-encoded)
```

### 4.2 Transformation steps

`borrower_archetype_engine.py:84-101`:

1. Coerce features to float (line 84-88). NaN → 0.
2. Map `EDUCATION` via `EDUCATION_MAP` (8 categories → 0..6).
3. Build DataFrame in fixed column order.
4. `_cached_scaler.transform(input_data)`.
5. `_cached_model.predict(X_scaled)[0]`.
6. `_cached_definitions.get(cluster_id, "Unknown Archetype")`.

### 4.3 Thresholds

None. E3 is a KMeans with `n_clusters=4`. Cluster identity is determined by Euclidean distance to centroids.

### 4.4 Rules

The cluster **labels** are assigned by a deterministic centroid-ranking rule (`scripts/train_borrower_archetype.py:66-83`):

- Highest EDUCATION centroid → "Educated Professionals"
- Highest tenure of remaining → "Highly Tenured Veterans"
- Lowest AGE of last two → "Young Starters"
- Remaining → "Mid-Career Established"

### 4.5 Output generation path

1. StandardScaler transform.
2. KMeans predict (cluster ID).
3. Label lookup from `borrower_archetype_definitions.json`.

### 4.6 Reproduction

**NO.** Per [ML_AUDIT_PHASE_2.md](ML_AUDIT_PHASE_2.md) §2.4, KMeans found a cluster of **size 1** (cluster ID 3, n=1) labeled "Educated Professionals." A re-run of the exact training pipeline with `random_state=42` reproduces the singleton. The reproducibility **of the artifact** is fine; the **cluster identity is meaningless** for that 1-row cluster.

### 4.7 Justification to a regulator

**No.**

1. The "Educated Professionals" cluster has **one borrower** with NETMONTHLYINCOME = ₹2,500,000, AGE = 25. The label is a function of one feature (EDUCATION) within a 4-cluster solution. The label is **fabricated**, not empirical.
2. The training data (`External_Cibil_Dataset.csv`, 51,336 rows) is **Home Credit Group data, not Indian** (per [DATA_LICENSE_VERIFICATION.md](DATA_LICENSE_VERIFICATION.md) §1.1). The label vocabulary was derived from Czech/Russia/Kazakhstan/China demographics. Applying "Educated Professionals" to a 25-year-old Indian loan applicant is a category error at the population level.
3. The training data has a **restrictive license** (per [DATA_PROVENANCE_AUDIT.md](DATA_PROVENANCE_AUDIT.md) §4). Production use is unauthorized.
4. The KMeans was trained without fairness considerations. The training data is **88% male** (per [ML_AUDIT_PHASE_2.md](ML_AUDIT_PHASE_2.md) §2.4). All four clusters have ~88% male composition. The "Young Starters" label, defined primarily by age, is confounded by gender-imbalanced training.

A regulator asking "what does 'Educated Professionals' mean" will receive an answer that does not correspond to the borrower's reality. The "1-row cluster" finding alone is enough to disqualify E3 from production.

### 4.8 Customer challenge

**No.** A customer classified as "Young Starters" sees a label that is **derived from age and gender proxies** in a KMeans trained on a different population. The customer cannot challenge a label that has no empirical basis in their own country or demographic.

**Grade: RED.** E3 is the worst-performing engine for explainability. The label vocabulary is fabricated, the cluster identity is unstable, and the training data is the wrong population.

---

## 5. E5 — Readiness Engine

### 5.1 Input fields used

`backend/app/engines/readiness/readiness_engine.py:50-457`. Inputs: age, dependents (young/old), occupants_count, home_ownership, type_of_house, house_area, sanitary_availability, water_availability, primary_business, secondary_business, loan_purpose, loan_tenure, loan_installments, loan_amount, annual_income, monthly_expenses.

The engine does **not** consume: `sex`, `social_class`, `age` (used for invalidation only), `city` (used as a key for archetype lookup but not scoring). See [FAIRNESS_AUDIT_FIRST_TIME_BORROWERS.md](FAIRNESS_AUDIT_FIRST_TIME_BORROWERS.md) §3.3.

### 5.2 Transformation steps

`readiness_engine.py:50-457`:

1. Impute defaults: house_area=450 if NaN; secondary_business="none" if NaN.
2. Validate numeric ranges (rejects NaN and Infinity, accepts non-positive income as 0).
3. Translate home_ownership string to internal `{owned, family_shared, rented, employer_provided}`.
4. Translate type_of_house string to internal `{T1, T2, R}`.
5. Compute five component scores:
   - **Financial health** (35%): stability_ratio + debt_burden_ratio, weighted average.
   - **Housing stability** (20%): ownership + house_type + dwelling_quality.
   - **Infrastructure access** (15%): sanitary (50%) + water (50%).
   - **Household burden** (15%): deductions for young/old dependents and excess occupants.
   - **Business viability** (15%): biz_stability + intent_alignment + diversification.
6. Combine components with fixed weights into a raw score, clamp to [0, 100], round to integer.
7. Map to band:
   - score >= 75: "Ready"
   - score >= 50: "Moderately Ready"
   - score >= 25: "Needs Improvement"
   - else: "Not Ready"
8. **Floor breach override:** if financial_health_score < 0.5 → band = "Not Ready" regardless of other components (line 370: `_FINANCIAL_HEALTH_FLOOR_THRESHOLD = 0.5`).

### 5.3 Thresholds

```
score >= 75: "Ready"
score >= 50: "Moderately Ready"
score >= 25: "Needs Improvement"
score < 25:  "Not Ready"

financial_health < 0.5 → force "Not Ready"
```

### 5.4 Rules

E5 has no "rules" in the recommendation sense. The recommendation engine (E5's consumer) has 14 rules across 4 buckets (`rules_person_b.py`). The recommendation rules are deterministic.

### 5.5 Output generation path

The readiness score is computed by the engine, the band by threshold mapping, the floor breach by override rule. The output is wrapped in `{band, score, components, mapped_features, imputed_fields, policy_override_applied}`. Recommendations are computed by `rules_person_b.py` evaluating the lowest two components (rank-based) and applying rule text.

### 5.6 Reproduction

**YES.** E5 is rule-based. Given inputs, the score is deterministic. Given the score and rules, the recommendation is deterministic. The only non-determinism is the `KMeans` archetype lookup in `borrower_archetype_engine.py` (separate concern).

### 5.7 Justification to a regulator

**Partial.** A regulator can be shown the engine code, the floor breach rule, and the component weights. However:

- The weights (35/20/15/15/15) are **hand-assigned**, not derived from observed outcomes (per [ML_AUDIT.md](ML_AUDIT.md) E5).
- The 0.5 floor breach threshold is **not policy-derived**.
- The recommendation rules are **generic** ("Micro-enterprises with established daily savings habits generally build better readiness over time" — `rules_person_b.py:63`). Per [FAIRNESS_AUDIT_FIRST_TIME_BORROWERS.md](FAIRNESS_AUDIT_FIRST_TIME_BORROWERS.md) §4.3, a ₹50M-income applicant with score 98 receives the same micro-savings advice as a poor borrower. The advice does not adapt to the score.
- The rank-based "improvement areas" selection (`rules_person_b.py:9-15`) is a heuristic. A borrower with all components at 50, 51, 80, 80, 80 receives the same "low" flag as one with 5, 6, 90, 90, 90.

A regulator asking "why was the floor breach applied" can be told "because financial health score < 0.5" but cannot be told "because the 0.5 threshold was chosen from a cost-of-error analysis" — because no such analysis exists.

### 5.8 Customer challenge

**Partial.** A customer can be told: "your financial health score is X, which is below our policy floor of 0.5 on a 0–100 scale; this is why we marked you Not Ready." The customer can argue the imputation logic (default 450 sq ft for missing house_area) but cannot argue the policy choice. The recommendation rationale is generic and not applicant-specific.

**Grade: YELLOW.** E5 is reproducible, mostly explainable, and the floor breach is documented. The weight and threshold choices are not policy-derived; the recommendation advice is generic.

---

## 6. E6 — Livelihood Engine

### 6.1 Input fields used

`backend/app/engines/livelihood/livelihood_mapper.py:69-86`. **One field:** `primary_business` (string).

### 6.2 Transformation steps

`livelihood_mapper.py:78-85`:

1. Validate: input must be a non-empty string.
2. Normalize: `.strip().lower()`.
3. Lookup: `LIVELIHOOD_DICTIONARY.get(normalized, 0)`.
4. Return: `ARCHETYPES[cluster_id]`.

### 6.3 Thresholds

None. E6 has no thresholds. It is a hash-map lookup.

### 6.4 Rules

The dictionary `LIVELIHOOD_DICTIONARY` (lines 38-67) is a hand-built mapping from 100+ business strings to 6 cluster IDs:

- 0: General Micro-Enterprise (catch-all)
- 1: Trade & Retail
- 2: Services
- 3: Agri-Allied
- 4: Manufacturing
- 5: Transport & Logistics

### 6.5 Output generation path

Trivial. The output is one of six archetype labels with a description.

### 6.6 Reproduction

**YES.** E6 is a deterministic dictionary lookup. Given a business string, the output is the same on every call.

### 6.7 Justification to a regulator

**YES.** A regulator can be shown the dictionary, the signature constraint (`mapper.py:75-77` accepts only a string), and the per-business mappings. The dictionary is hand-built and reviewable. The signature constraint explicitly excludes social_class, gender, and infrastructure from entering the mapping (per [ML_AUDIT_PHASE_2.md](ML_AUDIT_PHASE_2.md) §4.11).

Caveats:

- The dictionary is **incomplete**. Common Indian MFI business types are present (kirana, tailoring, dairy, etc.) but a borrower with a novel business type falls to cluster 0 ("General Micro-Enterprise") with the description "Unclassified or general small-scale business activity." The catch-all is **misclassification presented as a result**. Per [ML_AUDIT_PHASE_2.md](ML_AUDIT_PHASE_2.md) §7, an `is_unclassified` flag should be added.
- The dictionary has **no outcome validation**. The 6 archetypes are not benchmarked against default rates.

### 6.8 Customer challenge

**Partial.** A customer with a known business type can be told: "your business type 'tailoring' falls in the 'Services' archetype, defined as 'Service-oriented activities including tailoring, salons, repairs, and professional services.'" The customer can challenge the dictionary entry (e.g., "I'm a tailor, but I also run a small retail shop; why am I in Services not Trade & Retail?") and the institution can show the dictionary mapping. The customer cannot challenge the **categories** themselves — they are hand-authored, not derived from any statistical analysis.

A customer assigned cluster 0 ("Unclassified") has a much weaker challenge. The "Unclassified" label is a generic default, not a specific decision. The customer cannot argue against a generic default.

**Grade: GREEN.** E6 is the only engine that is fully deterministic, fully explainable, fully reviewable. The catch-all cluster is a documented weakness, not a failure. The engine does what the dictionary says it does, and the dictionary can be reviewed.

---

## 7. "Loan Officer Explanation"

Below is the canonical "loan officer explanation" for a typical RiskIntel output, written in the loan officer's voice. Each engine's explanation is constructed strictly from the engine logic. Where the engine logic cannot produce an explanation, the explanation is marked **CANNOT EXPLAIN**.

---

### 7.1 Person A — eligibility outcome "Likely" (probability 0.6289)

A loan officer would say:

> "Based on the inputs you provided, our eligibility model returned a probability of 0.6289, which falls in our 'Likely' band. The dominant factor in the assessment was your CIBIL score of 700 — the model assigns it the largest positive contribution to the probability. The model also produced negative contributions from your reported asset values (luxury_assets_value and residential_assets_value), which are zero in your application. The model was trained on a 4,269-row dataset whose source is not documented in our records, and the probabilities have not been calibrated against observed loan performance. We can show you the model code, but the rationale 'luxury assets reduce eligibility by 0.1353' does not correspond to a real economic signal when you declared no luxury assets. The verdict is a function of an uncalibrated probability and a hard threshold of 0.60. The model is reproducible for a given input, but the probability is not monotonic in your CIBIL — a higher CIBIL does not always produce a higher probability. **CANNOT EXPLAIN why luxury_assets_value contributes -0.1353 when you declared zero luxury assets. CANNOT EXPLAIN why a CIBIL of 800 produces a lower probability than a CIBIL of 700. CANNOT EXPLAIN the training data source or the threshold derivation.**"

**The loan officer cannot give an intelligible explanation to the applicant.** E1's `feature_contributions` are not economic signals. The verdict is a hard threshold on an uncalibrated probability.

### 7.2 Person A — risk tier P4 (CIBIL ≤ 658)

> "Your CIBIL score of N places you in our P4 tier, which we label 'High Risk.' The threshold for P4 is 658. This is a fixed threshold; we cannot tell you the cost-of-error analysis that selected this number. We can show you the threshold file. The P4 override on your case will replace any favorable eligibility verdict with 'Unlikely' or 'Borderline' regardless of the model's probability."

**Partial.** The loan officer can cite the threshold. The loan officer cannot justify the threshold.

### 7.3 Person A — archetype "Young Starters"

> "Our archetype engine has classified you as a 'Young Starters' borrower. The label is determined by a KMeans clustering on four features (income, age, tenure with current employer, education). **CANNOT EXPLAIN** — the 'Young Starters' label is defined primarily by your age relative to other clusters in the training data. The training data is a Home Credit Group dataset (Czech, Russia, Kazakh, Chinese population) used under a research-only license, and one of the four clusters in our model contains exactly one applicant, labeled 'Educated Professionals' because that applicant had the highest education centroid. The cluster labels are hand-assigned, not statistically derived. The 'Young Starters' label is being applied to an Indian loan applicant based on a clustering model that was trained on a population that does not include you."

**Cannot explain.** E3 cannot produce a borrower-readable rationale.

### 7.4 Person B — readiness "Not Ready" (floor breach)

> "Your readiness score is 0, which places you in the 'Not Ready' band. The score is the weighted sum of five components: financial health (35%), housing stability (20%), infrastructure access (15%), household burden (15%), and business viability (15%). Your financial health component is below our policy floor of 0.5 on a 0–100 scale, which forces the band to 'Not Ready' regardless of your other components. Your financial health component is driven by your annual_income and monthly_expenses values. The floor threshold of 0.5 is a policy choice, not a statistical threshold; we cannot show the cost-of-error analysis that selected it."

**Partial.** The loan officer can show the floor breach rule and the financial health component formula. The loan officer cannot show the policy rationale for the 0.5 threshold.

### 7.5 Person B — readiness "Ready" (housing/infrastructure driven)

> "Your readiness score is 79, which places you in the 'Ready' band. The score is driven primarily by your housing stability component (75 of 100) and your infrastructure access component (100 of 100). Your financial health is 64. Your housing stability comes from your owned T1 pucca house and your 450 sq ft house area. Your infrastructure access comes from your full water availability and sanitary availability. **The model does not measure your credit history, your prior loans, or your repayment record.** It measures your house and your amenities. Two borrowers with the same income but different houses will receive different scores. **The recommendation 'evaluate options for structured micro-savings products' is generic and is the same advice a low-income borrower receives.**"

**Partial.** The loan officer can show the components. The loan officer cannot explain why a "5-year good repayment history" is treated identically to "owns a pucca house with water."

### 7.6 Person B — livelihood cluster 0 "Unclassified"

> "Our livelihood engine could not find your business type in our dictionary. We have classified you as 'General Micro-Enterprise' with the description 'Unclassified or general small-scale business activity.' This is the default cluster when no business-type match is found. The dictionary has entries for kirana, tailoring, dairy, and ~100 other common business types, but yours is not among them."

**YES.** E6 is fully explainable. The catch-all is documented.

---

## 8. Composite Verdict

| Engine | Reproducible | Documented policy | Calibrated | Defensible to regulator | Defensible to customer | Grade |
|---|---|---|---|---|---|---|
| E1 | Partial (non-monotonic) | NO (synthetic data) | NO | NO | NO | **RED** |
| E2 | YES | NO (no policy rationale) | N/A (no probability) | Partial | NO | **YELLOW** |
| E3 | NO (1-row cluster, fabricated labels) | NO | N/A | NO | NO | **RED** |
| E5 | YES | Partial (weights + floor not policy-derived) | N/A (heuristic) | Partial | Partial | **YELLOW** |
| E6 | YES | YES (dictionary reviewable) | N/A (lookup) | YES | Partial (catch-all weak) | **GREEN** |

**Composite: 2 RED, 2 YELLOW, 1 GREEN.** E1 and E3 are the explainability failures. E2 and E5 are reproducible but undocumented as policy. E6 is the only fully explainable engine.

---

## 9. Summary

| Engine | Grade | Primary explainability risk |
|---|---|---|
| E1 Eligibility | **RED** | Uncalibrated `predict_proba`; non-monotonic; fabricated `feature_contributions`; synthetic training data; CIBIL leakage. |
| E2 Risk Tier | **YELLOW** | Reproducible; threshold values not policy-derived; no recourse for P4. |
| E3 Borrower Archetype | **RED** | 1-row cluster labeled "Educated Professionals"; narrative labels in production; wrong population. |
| E5 Readiness | **YELLOW** | Rule-based; weights not policy-derived; generic recommendations; floor breach is policy choice without cost-of-error analysis. |
| E6 Livelihood | **GREEN** | Deterministic dictionary; reviewable; documented catch-all. |

**Two engines are not production-suitable for explainability (E1, E3). Two engines are technically explainable but lack policy-level documentation (E2, E5). One engine is fully explainable (E6).**

The institution cannot defend the E1 eligibility verdict to a regulator with a documented model card. The institution cannot defend the E3 archetype label to a customer with an intelligible rationale. The other three engines can be defended, conditional on policy documentation being written.

**Binding action:**
- Disable E3 from production response.
- Replace E1 dataset and retrain.
- Write model cards for E2, E5, E6.
- Add `is_unclassified` flag to E6.

The explainability audit identifies the same structural failures the prior audits identified: the data is the problem, the E3 model is broken, the E1 model is uncalibrated. A loan officer can only fully explain E6. E2 and E5 can be explained. E1 and E3 cannot.
