# RiskIntel — ML Audit Phase 2: Engines E2, E3, E5, E6

**Version:** 1.0
**Date:** 2026-06-06
**Scope:** E2 Risk Tier, E3 Borrower Archetype, E5 Readiness, E6 Livelihood Archetype.
**Inherits:** [ML_AUDIT.md](ML_AUDIT.md) v1.0 (Person A), [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md) v1.0.
**Method:** Read-only audit. Engine code re-read, training data re-fitted, production routing traced.
**No code modified.**

---

## 0. Pre-reads in this audit (no re-quoting; see linked files)

- `backend/app/engines/risk_tier/risk_tier_engine.py` (101 lines) — see [ML_AUDIT.md](ML_AUDIT.md) §2 F2.
- `backend/app/engines/archetype/borrower_archetype_engine.py` (120 lines) — see earlier read.
- `backend/app/engines/livelihood/livelihood_mapper.py` (85 lines) — see earlier read.
- `backend/app/engines/readiness/readiness_engine.py` (462 lines) — see earlier read.
- `backend/app/orchestrator.py` — see earlier read.

---

## 1. E2 — Risk Tier Engine

### 1.1 Architecture summary

E2 is a **non-ML deterministic function** on the applicant's CIBIL score. `risk_tier_engine.py:60-87` returns one of four tiers from a hard threshold file.

```
P1: cibil_score >= 701            (description: "Low Risk")
P2: 669 <= cibil_score < 701      (description: "Moderate Risk")
P3: 659 <= cibil_score < 669      (description: "Elevated Risk", fallback band)
P4: cibil_score <= 658            (description: "High Risk")
```

`orchestrator.py:138-144` adds the override: if `risk_tier == "P4"` and eligibility verdict ∈ {Highly Likely, Likely}, force verdict to Unlikely and append `OVERRIDE_E2_P4_REJECTION`.

### 1.2 Dataset provenance

The E2 thresholds are calibrated against an unspecified CIBIL distribution. The only CIBIL dataset in the repo is `data/raw/External_Cibil_Dataset.csv` (51,336 rows, range 469–811). The thresholds are not derived from this data: there is no `data/processed/risk_tier_thresholds.json` provenance and no build script.

### 1.3 Label generation method

N/A — E2 is unsupervised (no labels). The thresholds are **author-intuition values**, not learned from observed default rates.

### 1.4 Audit against the only available CIBIL data

I applied the E2 thresholds to `External_Cibil_Dataset.csv` and cross-referenced the `Approved_Flag` column:

| E2 band | n | % labeled P1 | % labeled P2 | % labeled P3 | % labeled P4 |
|---|---|---|---|---|---|
| P1 (≥701) | 6,392 | 90.8% | 0.0% | 9.2% | 0.0% |
| P2 (669–700) | 32,199 | 0.0% | 100.0% | 0.0% | 0.0% |
| P3 (659–668) | 6,861 | 0.0% | 0.0% | 100.0% | 0.0% |
| P4 (≤658) | 5,884 | 0.0% | 0.0% | 0.0% | 100.0% |

**Findings:**
- E2's tier labels are **identical** to the dataset's existing `Approved_Flag` values. The thresholds reproduce the source dataset's tier labeling exactly, by construction.
- The 9.2% of P1 rows labeled P3 in the source data are **excluded** from the E2 P1 band purity calculation. The threshold design drops them silently.
- There is no observed default rate in this data. `Approved_Flag` is a tier label assigned by the bureau, not a 12-month default outcome.

### 1.5 Calibration, fairness, leakage, suitability

| Dimension | Status | Evidence |
|---|---|---|
| Calibration | N/A | E2 does not output a probability |
| Feature concentration | N/A | Single feature (CIBIL) |
| Synthetic-rule risk | LOW | E2's 4-tier structure matches the bureau's published bands; whether those bands are themselves synthetic is outside this audit's scope |
| Fairness risk | HIGH | Hard thresholds on CIBIL without demographic adjustment; the override fires on P4 without recourse |
| Production suitability | LOW | Thresholds are not policy-derived; the 9.2% P1→P3 mismatch in source data is unaddressed |

### 1.6 E2 verdict

**CONDITIONAL PASS.** The engine is correct as a deterministic lookup. The conditional:
- The P4 override at `orchestrator.py:142-144` is not calibrated to a cost-of-error ratio.
- The thresholds are not defended in a model card.
- Fairness is unaddressed.

**Recommendation:** Document the P4 override as a policy decision (not a model output) and pair it with a disparate-impact audit. The override itself can stay; its policy rationale cannot.

---

## 2. E3 — Borrower Archetype Engine

### 2.1 Architecture summary

E3 is a **KMeans(4)** trained on 4 features: `NETMONTHLYINCOME`, `AGE`, `Time_With_Curr_Empr`, `EDUCATION`. The model artifacts are at `models/archetype/kmeans_model.pkl` and `scaler.pkl`. The cluster labels are at `data/processed/borrower_archetype_definitions.json` and are assigned by a deterministic centroid-ranking rule.

E3 is **called in the production orchestrator path** for Person A. `orchestrator.py:111-112` invokes `get_borrower_archetype(payload)` for every Person A request.

### 2.2 Dataset provenance

- **Source:** `data/raw/External_Cibil_Dataset.csv` (51,336 rows, 62 columns). No build script, no `provenance.json`.
- **Schema:** Bureau + demographic + financial features.
- **License:** Public Kaggle release. Terms-of-use require verification before production.
- **Population:** Czech, Russian, Kazakh, Chinese. Not Indian.

### 2.3 Training methodology

`scripts/train_borrower_archetype.py:36-83`:
1. Drop rows with NaN in 4 features (51,336 retained).
2. Apply `EDUCATION_MAP` to 8 string categories.
3. `StandardScaler` then `KMeans(n_clusters=4, random_state=42)`.
4. Label assignment by centroid ranking: highest EDUCATION → "Educated Professionals"; highest tenure of remaining → "Highly Tenured Veterans"; lowest AGE of last two → "Young Starters"; remaining → "Mid-Career Established."

### 2.4 Forensic re-fit

Re-ran the exact training pipeline on the source data:

| Metric | Value |
|---|---|
| Rows | 51,336 |
| Cluster sizes | [19,963, 20,292, 11,080, **1**] |
| Inertia | 110,690 |
| Silhouette | 0.283 |
| Calinski-Harabasz | 14,632 |

**Critical finding:** KMeans found a cluster of **size 1** (cluster ID 3). A single applicant with `NETMONTHLYINCOME = 2,500,000` (≈ ₹2.5 crore), `AGE = 25`, `Time_With_Curr_Empr = 35`, `EDUCATION = 4` (GRADUATE) is its own cluster. **The training script labels this one-row cluster as "Educated Professionals."** Every borrower in the production data who is similar to this one applicant will be misclassified.

Cluster composition by gender (from the original `External_Cibil_Dataset`):

| Label (per training script) | n | % Male | Mean age |
|---|---|---|---|
| Educated Professionals (cluster 3) | 1 | 100% | 25.0 |
| Highly Tenured Veterans (cluster 2) | 11,080 | 87.9% | 44.8 |
| Young Starters (cluster 0) | 19,963 | 89.3% | 29.9 |
| Mid-Career Established (cluster 1) | 20,292 | 87.1% | 31.5 |

**Findings:**
- The largest cohort (Young Starters) is defined as "lowest AGE of the non-veteran cluster." It contains ~39% of the dataset.
- The label "Educated Professionals" applies to **one applicant**. The label is meaningless.
- Three of four clusters have very similar gender distributions (~88% male). The training data is imbalanced by gender (45,245 M / 6,091 F). The KMeans does not adjust for this.
- Silhouette 0.283 is low; the cluster structure is weak.
- The "Highly Tenured Veterans" cohort is defined by `Time_With_Curr_Empr = 206` (mean) — over 17 years. The label is descriptive of one feature, not the multivariate profile.

### 2.5 Label generation method

Labels are generated by **deterministic centroid ranking**, not from any observed outcome. The label "Educated Professionals" derives from one feature (highest EDUCATION) among four clusters; the title does not reflect the cluster's multivariate profile, only its EDUCATION centroid.

### 2.6 Synthetic-rule detection

E3 is unsupervised. There is no rule of the form "if EDUCATION=X then label=Educated Professional." The labels are derived from clustering, but the *meaning* of the labels is fabricated. The label "Educated Professionals" applied to a 1-row cluster is a **narrative fabrication**, not a synthetic rule. The risk is the same: a label that has no empirical basis.

### 2.7 Leakage

No target leakage (unsupervised). However, the cluster identity for a 1-row cluster is unstable. Any new applicant similar to that 1-row applicant will either join the 1-row cluster (making it 2 rows) or shift the cluster boundaries. The cluster identity is not stable.

### 2.8 Calibration

KMeans outputs hard cluster IDs. There is no calibration to apply. The "distance to centroid" could be a soft score, but it is not exposed in production.

### 2.9 Fairness risk

**CRITICAL.** The production path exposes the cluster label to the loan officer via `orchestrator.py`. The label "Young Starters" appears as a verdict-adjacent field. A loan officer seeing a 19,963-cohort label that is defined primarily by age and gender proxies has been shown the audit's MC9 finding in production.

**Specific concerns:**
- Education: KMeans was trained on a categorical EDUCATION column with an ordinal mapping that the script author defined. "POST-GRADUATE" maps to 5, "PROFESSIONAL" to 6. The ordinal is defensible but not validated.
- GENDER: dropped from training, but the cluster centroids are confounded by the gender-imbalanced input distribution.
- AGE: the "Young Starters" label is age-anchored. Age is a protected class proxy in credit decisioning.

### 2.10 Production routing verification

Traced the orchestrator with a Person A request:

```json
"archetype": {
  "label": "Young Starters",
  "cluster_id": 2,
  "description": "Younger demographic, lower employment tenure, early career stage."
}
```

E3 IS in the production response. The loan officer sees "Young Starters" as a borrower descriptor. This is the narrative-label risk that [ML_AUDIT.md](ML_AUDIT.md) E3 flagged.

### 2.11 E3 verdict

**FAIL.** Three independent failures:

1. **1-row cluster** is labeled "Educated Professionals" — the entire category is meaningless.
2. **Narrative labels** ("Young Starters", "Educated Professionals") are exposed in production and have no empirical basis.
3. **Cluster 3** is 1 row, but the production routing treats it as a real category.

**Recommendation:** E3 should be removed from the production response. If archetype information is to be retained, replace the KMeans with a defensible, stable method (e.g., quartiles on NETMONTHLYINCOME) or remove the field from the response. The current implementation cannot be defended to a regulator.

---

## 3. E5 — Readiness Engine

### 3.1 Architecture summary

E5 is a **pure rule-based scoring function**. `readiness_engine.py:50-457` computes five component scores (financial_health, housing_stability, infrastructure_access, household_burden, business_viability), each with explicit weights, and combines them into a final score. There is no ML model in `models/readiness/` (the directory is empty).

### 3.2 Dataset provenance

`data/processed/readiness_data.csv` contains 40,000 rows. **There is no target column.** The data is unlabeled inputs only. The "ground truth" for the readiness engine is the rule itself, not observed loan performance.

### 3.3 Label generation method

None. E5 does not predict an outcome. It computes a heuristic score. The bands (Ready ≥ 75, Moderately Ready ≥ 50, Needs Improvement ≥ 25, Not Ready < 25) are author-defined thresholds, not learned from data.

### 3.4 Training methodology

None. There is no training. The engine is a hand-coded scoring function with explicit rules and a documented financial_health floor override (`readiness_engine.py:370`: `_FINANCIAL_HEALTH_FLOOR_THRESHOLD = 0.5`).

### 3.5 Feature importance concentration

Not applicable. The engine's "feature importance" is the rule author's hand-assigned weights:
- financial_health: 35%
- housing_stability: 20%
- infrastructure_access: 15%
- household_burden: 15%
- business_viability: 15%

These weights are not derived from observed outcome data.

### 3.6 Synthetic-rule detection

The financial_health component is the most consequential (35% weight) and contains the floor breach policy. The rules are defensible as policy (lenders do in fact weight financial health heavily). The imputation logic is documented (defaults: 450 sq ft, "none" for missing business). The engine does what its rules say it does.

### 3.7 Leakage

None. No labels. No target. No training.

### 3.8 Calibration

Not applicable. E5 outputs a heuristic score, not a probability. The score cannot be calibrated against ground truth because there is no ground truth.

### 3.9 Fairness risk

**MEDIUM.** The engine does not use gender, caste, or religion. The data has `sex` and `social_class` columns, but the engine ignores them. The financial_health floor override (`readiness_engine.py:370`) is a policy override on a financial feature, not a protected class.

However:
- `type_of_house` ("R", "T1", "T2") and `house_area` correlate with rural/urban status. The engine uses these.
- `water_availability` and `sanitary_availability` correlate with socioeconomic status. The engine uses these.
- The recommendations engine uses the lowest-two-components rule, which may systematically flag rural applicants.

### 3.10 Production routing verification

E5 is called in the orchestrator for Person B (`orchestrator.py:228-234`). The output is wrapped in a `readiness` object with `band`, `score`, `components`, `mapped_features`, `imputed_fields`, `policy_override_applied`.

### 3.11 E5 verdict

**CONDITIONAL PASS.** E5 is a rule-based engine, not a learned model. It is auditable, deterministic, and explainable. The conditional:

- **No calibration possible** because no ground truth exists. The bands are author-intuition.
- **Imputation is silent** — a borrower with no income receives a proxy-derived score. The proxy is not flagged in the API response (only the `imputed_fields` array is, and only in some code paths).
- **The recommendations engine** that consumes E5's output (rules_person_b.py:9-15) selects the two lowest-scoring components as "improvement areas" — a rank-based heuristic that can systematically flag the same components across a population.

**Recommendation:** E5 is a defensible rules engine. It should remain rules-based, not be replaced with ML. The acceptance gate for E5 is *not* "AUC > 0.X" but rather "rules are documented, reviewed, and applied consistently." Add a rules-review audit: every rule in `rules_person_b.py` and `rules_person_a.py` should be reviewed by a credit analyst, dated, and signed.

---

## 4. E6 — Livelihood Archetype Engine

### 4.1 Architecture summary

E6 is a **pure dictionary lookup** on the `primary_business` string. `livelihood_mapper.py:38-67` defines 6 archetypes (cluster IDs 0–5). 100+ business strings map to cluster IDs. Strings not in the dictionary return cluster 0 ("General Micro-Enterprise").

### 4.2 Dataset provenance

`data/processed/livelihood_data.csv` (40,000 rows) contains one-hot encoded macro features and inputs. It is **not used** by `livelihood_mapper.py`. The mapper is a string lookup; no training data is consulted at runtime.

### 4.3 Label generation method

None. The cluster IDs 0–5 are hard-coded in the source. The "labels" are the 6 archetype names in the `ARCHETYPES` dict. The mapping was authored by hand, not learned from data.

### 4.4 Training methodology

None. The mapping is a hand-built dictionary. There is no KMeans, no classifier, no embedding.

### 4.5 Forensic checks on the dictionary

The dictionary has 100+ entries across 5 productive clusters. A borrower's business is mapped to one cluster_id. The signature constraint (`mapper.py:75-77`) is documented: only the `primary_business` string is accepted, not the full applicant dict. This **isolates the prediction algorithm from social_class, gender, water_availability, etc.** — a defensible design.

However:
- The dictionary is **incomplete**. Common Indian MFI business types (kirana, tailoring) are present. Less common ones (computer repair, tutoring center, boutique) are not. Missing strings fall to cluster 0.
- Cluster 0 ("General Micro-Enterprise") has the description "Unclassified or general small-scale business activity." A borrower assigned cluster 0 receives that description. **This is misclassification presented as a result.**
- The dictionary does not include subcategories (e.g., "kirana" and "kirana store" should map to the same cluster but a typo or synonym may not).

### 4.6 Synthetic-rule detection

E6 has no ML component, so the synthetic-rule concern does not apply. However, the **catch-all cluster 0** is a synthetic label applied to a heterogeneous population. It is the dictionary's version of the [ML_AUDIT.md](ML_AUDIT.md) F4 finding.

### 4.7 Leakage

None. The mapping is a hand-built lookup. No target data is used.

### 4.8 Calibration

Not applicable. The mapper outputs a hard cluster ID, not a probability.

### 4.9 Fairness risk

**LOW.** Two reasons:
1. The signature constraint (`mapper.py:75-77`) explicitly excludes non-string inputs. Social class, gender, and infrastructure cannot enter the mapping.
2. The cluster IDs are not normalized against demographic distribution.

The catch-all cluster 0 is a fairness concern: a borrower whose business is not in the dictionary is labeled "Unclassified" regardless of their actual business. This affects borrowers with novel or non-standard businesses. It does not systematically disadvantage protected classes — it disadvantages non-standard business types, which is a different category.

### 4.10 Production routing verification

E6 is called in the orchestrator for Person B. The orchestrator's response includes:
```json
"archetype": {"label": "Services", "description": "...", "cluster_id": 2}
```

E6 returns one of the 6 archetype labels. The borrower sees "Services" or "Trade & Retail" or one of the other 4 productive labels, or "General Micro-Enterprise" (cluster 0).

### 4.11 E6 verdict

**CONDITIONAL PASS.** E6 is a defensible hand-built lookup. The conditional:

- **Cluster 0 catch-all** is the principal concern. Borrowers with novel business types are mislabeled.
- **No statistical validation** of the dictionary. The 6 archetypes are not benchmarked against any outcome.
- **Cluster 0's "Unclassified" description** is the borrower's only signal that the system did not know their business. A loan officer seeing "Unclassified" should be prompted to escalate, not approve.

**Recommendation:** Add a small unknown-business fallback path. If cluster 0 is hit, return a flag to the API ("novel business type, manual classification needed") rather than silently returning a generic label. E6 is fine as a hand-built lookup but should not silently mask classifier failure.

---

## 5. Risk Ranking Across All Engines

| Engine | Severity | Top issue |
|---|---|---|
| **E1** (eligibility) | CRITICAL | Synthetic-rule data; CIBIL dominates 92.9% of model power; uncalibrated probabilities; see [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md) §8. |
| **E2** (risk tier) | HIGH | Hard CIBIL thresholds; P4 override without disparate-impact audit; 9.2% P1→P3 mismatch in source data unaddressed |
| **E3** (archetype) | **CRITICAL** | 1-row cluster labeled "Educated Professionals"; narrative labels in production; weak silhouette (0.283); gender-imbalanced training set |
| **E5** (readiness) | MEDIUM | No calibration; silent imputation; rank-based recommendations can systematically flag rural applicants |
| **E6** (livelihood) | MEDIUM | Catch-all cluster 0 mislabels novel business types; no outcome validation of the dictionary |

**Ranking by severity:**
1. E1 (CRITICAL)
2. E3 (CRITICAL)
3. E2 (HIGH)
4. E5 (MEDIUM)
5. E6 (MEDIUM)

---

## 6. Systemic Diagnosis

### 6.1 Is RiskIntel one broken model or a systemic problem?

**Systemic.** Four of the five engines have at least one of the following defects:

| Defect | E1 | E2 | E3 | E5 | E6 |
|---|---|---|---|---|---|
| Synthetic rule / fabricated label | YES | n/a (no labels) | YES (1-row cluster) | n/a | n/a (hand-built) |
| Hard threshold on a continuous score | n/a (ML) | YES (CIBIL) | n/a | YES (band cuts) | n/a (dict) |
| Uncalibrated probability | YES | n/a | n/a | n/a | n/a |
| Narrative label in production | n/a | n/a | YES | n/a | YES (cluster 0) |
| Silent imputation | n/a | n/a | n/a | YES | n/a |
| No fairness audit | YES | YES | YES | partial | NO |
| No drift monitoring | YES | YES | YES | YES | YES |
| No model version pin | YES | YES | YES | n/a | YES |

**Five of five engines have at least three of these defects.** Four of five have at least four.

### 6.2 Common root causes

The same root causes appear in multiple engines:

1. **Data lineage is absent across the entire system.** No `provenance.json`, no build scripts for any processed dataset, no documented relationships between `data/raw/` and `data/processed/`. The 14 CSVs in `data/raw/` are not labeled. The processed datasets are not labeled. There is no way to audit "where did this model come from."
2. **The training pipeline is brittle.** `train_borrower_archetype.py` uses `KMeans(4, random_state=42)`. The 1-row cluster that resulted is a fragility, not a bug. KMeans with high-cardinality income data will always produce outliers as singletons. The training script does not check cluster sizes.
3. **No fairness discipline.** E3's "Young Starters" label, E2's P4 override, and E5's silent imputation all operate without demographic disaggregation.
4. **No output quality contract.** E5 outputs a heuristic score with no calibration. E3 outputs a fabricated label. E6 outputs a catch-all with a misleading description. None of the engines ship with a documented output quality guarantee.
5. **No drift monitoring across any engine.** The `audit_log` table records decisions but not input distributions.

### 6.3 Implications for the v1 freeze

The v1.0 freeze, as written in [ML_AUDIT.md](ML_AUDIT.md), was **conditional on E1 only**. The audit's freeze-readiness score of 31/100 reflected E1 alone. **Including E2, E3, E5, E6 brings the score lower.** The systemic diagnosis is:

- E1: replace dataset.
- E2: keep with policy documentation; cannot defend to a regulator without a model card and fairness audit.
- E3: **remove from production response.** The 1-row cluster alone disqualifies it.
- E5: keep with rules-review audit; do not retrain; do not attempt to "ML-ify" it.
- E6: keep with unknown-business fallback.

The v1.0 audit's recommendation (do not freeze, replace dataset) is **strengthened** by Phase 2. The institution is not running a credit model. It is running:

- E1: a CIBIL threshold (100-tree costume)
- E2: a CIBIL threshold (legitimate but undocumented)
- E3: a 1-row cluster masquerading as an archetype
- E5: a rule book (defensible, needs audit)
- E6: a string lookup (defensible, needs fallback)

**None of the five engines is a defensible ML system in the form currently deployed.** The frozen backend is not frozen in the right way — it is frozen at a level of ML discipline that is not yet present.

---

## 7. Per-Engine Recommendations (Binding)

### E1 — REPLACE DATASET (per FORENSIC_AUDIT.md)

No change. The verdict stands. Dataset replacement is the binding action.

### E2 — DOCUMENT AS POLICY, NOT MODEL

- Write a model card describing E2 as a policy threshold, not a learned model.
- Pair the P4 override with a quarterly disparate-impact audit.
- Document the 9.2% P1→P3 mismatch in source data as a known source-of-truth caveat.
- After dataset replacement for E1, recompute E2 thresholds against the new observed default rates.

### E3 — REMOVE FROM PRODUCTION RESPONSE

- Stop returning `archetype` in Person A's response until a defensible clustering is in place.
- If a clustering is desired, replace with one of:
  - KMeans(4) with `n_init=10` and explicit minimum-cluster-size enforcement (e.g., drop singletons).
  - Quartile-based bucketing on `NETMONTHLYINCOME` (no fabricated labels).
  - External vendor-provided archetype.
- Do not re-deploy the current `kmeans_model.pkl` artifact. It produces 1-row clusters.

### E5 — RULES REVIEW, NOT RETRAIN

- Add `last_reviewed_by` and `last_reviewed_at` metadata to every rule in `rules_person_a.py` and `rules_person_b.py`.
- Have a senior credit analyst review the 14 rules. Document the review.
- Add a "rank-based improvement area" warning to the API: when `has_low_component` selects two components, surface the *magnitude* of the gap so the officer sees whether the difference is meaningful.

### E6 — UNKNOWN-BUSINESS FALLBACK

- Add an `is_unclassified` flag to the E6 response. When cluster 0 is hit, the flag is `true`.
- The orchestrator should surface this to the loan officer as a "novel business type, manual classification recommended" indicator.
- Build a small unknown-business review queue in production. Review quarterly. Add common-misspellings to the dictionary.
- The current `livelihood_data.csv` (40k rows, one-hot) is **not used by E6**. It is dead weight in the repo. Either remove it or document its purpose.

---

## 8. Production Readiness Verdict

| Engine | Verdict | Binding action |
|---|---|---|
| E1 Eligibility | FAIL | REPLACE DATASET |
| E2 Risk Tier | CONDITIONAL PASS | Document as policy, not model. Add model card. Add fairness audit. |
| E3 Borrower Archetype | **FAIL** | **Remove from production response** OR replace with quartile-based or external-vendor clustering. Do not re-deploy current `kmeans_model.pkl`. |
| E5 Readiness | CONDITIONAL PASS | Rules review. Document. Add `last_reviewed_at` to every rule. |
| E6 Livelihood | CONDITIONAL PASS | Unknown-business fallback. Quarterly unknown-business review. |

**Composite:** 2 FAILS (E1, E3), 3 CONDITIONAL PASSES (E2, E5, E6).

**Is RiskIntel production-ready?** **No.** The v1.0 freeze cannot stand as written. E1 and E3 are not production-suitable. E2, E5, E6 are production-suitable conditional on documentation, fairness audits, and review.

**Is the problem one broken model or systemic?** Systemic. Four of five engines have synthetic-rule risk, hard-threshold risk, or fabricated-label risk. The same root causes (no data lineage, no fairness discipline, no drift monitoring) appear across engines. Replacing the data fixes E1 but not E3. E3 must be removed or rebuilt independently. E2, E5, E6 require policy documentation, not data fixes.

**Re-audit gate for v2 (any engine update):**
1. New dataset passes the forensic suite (FORENSIC_AUDIT.md §8).
2. New model passes the calibration analysis.
3. New fairness audit (demographic parity, equalized odds) is published.
4. Drift monitoring is wired into the deployment pipeline.
5. Model version is pinned (SHA-256 at load time).
6. Engine-specific gates:
   - E1: real-outcome data; no single feature > 50% importance; calibration ≤ 0.05 ECE.
   - E2: thresholds derived from observed default rates on the new data; disparate-impact audit passed.
   - E3: minimum cluster size ≥ 1% of population; no 1-row clusters; narrative labels replaced with neutral descriptions or removed.
   - E5: every rule has `last_reviewed_by` and `last_reviewed_at` metadata; rules review audit dated within 90 days.
   - E6: unknown-business fallback active; `is_unclassified` flag in response; dictionary version pinned.

---

## 9. Summary

| Item | Value |
|---|---|
| E1 Verdict | FAIL — replace dataset (per FORENSIC_AUDIT.md) |
| E2 Verdict | CONDITIONAL PASS — document as policy, add model card, add fairness audit |
| E3 Verdict | **FAIL** — 1-row cluster, fabricated labels, narrative exposure in production |
| E5 Verdict | CONDITIONAL PASS — rules review, no ML-ification |
| E6 Verdict | CONDITIONAL PASS — unknown-business fallback, quarterly review |
| Risk rank | E1 = E3 > E2 > E5 ≈ E6 |
| Systemic vs single | **Systemic.** Four of five engines share the same root causes: no data lineage, no fairness discipline, no output quality contract, no drift monitoring. |
| Production-ready? | **No.** v1.0 freeze cannot stand. E1 and E3 must be replaced or removed before any production deployment. |
| Binding actions | (1) Replace E1 dataset. (2) Remove E3 from production response. (3) Document E2 as policy with fairness audit. (4) Audit E5 rules. (5) Add E6 unknown-business fallback. |

The frozen backend is not a model. It is a collection of three rules engines (E2, E5, E6), one broken KMeans (E3), and one CIBIL threshold (E1) wearing a 100-tree costume. The institution has no ML to ship.
