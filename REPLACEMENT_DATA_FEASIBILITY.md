# RiskIntel — Replacement Data Feasibility Study (Person A)

**Version:** 1.0
**Date:** 2026-06-06
**Scope:** Identify candidate datasets to replace `data/processed/eligibility_data.csv`.
**Triggered by:** [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md) §8 — verdict REPLACE DATASET.
**Method:** Research and planning. No code. No downloads. No training. No model rebuild.

---

## 1. Requirements for the replacement dataset

The replacement must satisfy the acceptance gates stated in [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md) §8. Summarized:

- Labels derived from observed 6–12-month loan performance, not a deterministic rule on CIBIL.
- No single feature with point-biserial correlation > 0.50 with target. Current: CIBIL = 0.77.
- RF excluding any single feature achieves ≥ 0.75 AUC. Current: 0.60.
- SHAP top feature < 50% of total importance. Current: 79.7%.
- Depth-1 tree on any single feature achieves ≤ 0.85 AUC. Current: 0.97.
- Temporal train/test split (loan origination date, not random).
- ≥ 50,000 rows.

Additional implicit requirements from the architecture and the Indian-style lending use case:

- Features compatible with `PersonARequest` schema in `backend/app/schemas/requests.py` (dependents, education, self_employed, annual_income, loan_amount, loan_term, cibil_score, residential_assets_value, commercial_assets_value, luxury_assets_value, bank_asset_value). Or schema must be revised and the engines re-trained, which is in scope.
- The MFI use case targets thin-file and rural borrowers. The replacement dataset should not be exclusively prime / urban / US-only.
- Licensing must permit commercial use, derivative work, and redistribution inside a financial product.
- Schema must allow temporal train/test split (origination date field required).
- Outcome must be a clear binary or survival target that the institution can defend to a regulator.

---

## 2. Candidate Datasets

### 2.1 Home Credit Default Risk

| Field | Value |
|---|---|
| Source | [Kaggle competition](https://www.kaggle.com/c/home-credit-default-risk), sponsored by Home Credit Group (Czech Republic / international) |
| Row count | 307,511 application rows (train) + 48,744 (test); supplementary tables `bureau.csv` (1.7M), `bureau_balance.csv` (27M), `previous_application.csv` (1.6M), `POS_CASH_BALANCE.csv` (10M), `installments_payments.csv` (13.6M), `credit_card_balance.csv` (3.8M) |
| Feature count | 122 in main `application_train.csv`; 320+ across all tables |
| Target definition | Binary: 1 = client had payment difficulties (XNA, > 30 DPD on first installment, or 60–90 DPD on subsequent installments), 0 = no payment difficulties. Multi-class `TARGET` ranges 0/1. Outcome measured 12 months after origination. |
| Availability | Free download from Kaggle. Requires Kaggle account. ~600MB compressed. |
| Licensing | Public competition. Data is "as-is". Home Credit released it for non-commercial research and competition use. **Commercial use is restricted.** Must verify terms before production. |
| Indian-style suitability | **High conceptual fit but not Indian population.** Home Credit operates in Russia, Kazakhstan, China, Czech Republic. The product is for underbanked borrowers — same target population as Indian MFI. Features include age, employment, income, contract type, credit history, previous applications, installment payments. **No explicit CIBIL-equivalent.** CIBIL-like score derivable from prior-application features. **Geographic and economic mismatch is the principal concern.** |
| Expected preprocessing | High. 122 features, heavy missingness, multiple supplementary tables require joins. 6 tables, ~30M rows total. Mixed types. Categorical encoding. Bureau credit history aggregation. Out-of-time split (Home Credit provides an `application_date` proxy via `DAYS_DECISION` and other time features). Reference: top Kaggle solutions reach AUC 0.80–0.81 with extensive feature engineering. |
| Fairness suitability | **High.** Home Credit provides age, gender, education, occupation type. Disaggregated fairness audit possible. |
| Provenance | Documented. Public competition, schema published, multiple published benchmarks for reproducibility. |
| Recommendation | **Strong candidate for realistic underwriting.** Must negotiate license for commercial use. Must bridge feature gap to Indian underwriting. |

### 2.2 Lending Club

| Field | Value |
|---|---|
| Source | [LendingClub.com statistics](https://www.lendingclub.com/info/download-data.action) (now peer-to-peer closed; data frozen) |
| Row count | ~2.3M loans (2007–2018) in the canonical `accepted` dataset. The most useful subset for default modeling is `accepted_2007_to_2018Q4.csv.gz`, ~1.7M rows. |
| Feature count | ~150 (loan_amnt, term, int_rate, installment, grade, sub_grade, emp_title, emp_length, home_ownership, annual_inc, verification_status, issue_d, purpose, dti, delinq_2yrs, earliest_cr_line, inq_last_6mths, open_acc, pub_rec, revol_bal, revol_util, total_acc, etc.) |
| Target definition | Multiple possible: `loan_status` is categorical (Fully Paid, Current, Charged Off, Late, In Grace Period). Binary: 1 = Charged Off (default) or Late, 0 = Fully Paid. **"Current" loans must be excluded from training** (outcome unknown at observation). |
| Availability | Direct download from LendingClub.com. ~500MB. Public. |
| Licensing | Public dataset, free to use. No explicit commercial restriction, but LendingClub terms-of-use should be reviewed. |
| Indian-style suitability | **Low population fit.** US P2P borrowers. Income is `annual_inc` (USD). No CIBIL-equivalent. `grade` is LendingClub's internal grade, useful only for stratified sampling. **Lending Club's `grade` is a leaky feature** — it is the lender's pre-decision grade; using it in the model is target leakage by proxy. |
| Expected preprocessing | Moderate. Categorical encoding, missingness treatment, time-based split (`issue_d`). Filtering on `loan_status ∈ {Fully Paid, Charged Off, Late}`. The dataset's churn (Closed/Funded) requires care: "Current" loans are unlabeled and must be excluded. |
| Fairness suitability | **Moderate.** Gender is unavailable in recent vintages; age, state, zip allow geographic disaggregation. Income is the principal protected proxy. |
| Provenance | Documented. Public. Multi-decade record. Loan-level outcomes observed. |
| Recommendation | **Good for academic project.** Best-documented multi-year performance data. Not suitable for Indian MFI without major feature engineering. The `grade` leakage is a known footgun. |

### 2.3 Give Me Some Credit (GMSC)

| Field | Value |
|---|---|
| Source | [Kaggle competition](https://www.kaggle.com/c/GiveMeSomeCredit), 2011 |
| Row count | 250,000 (training) + 101,503 (test) |
| Feature count | 11 (10 features + 1 target) |
| Target definition | Binary: 1 = serious delinquency (90+ DPD) in next 2 years, 0 = no serious delinquency. Outcome measured 2 years out. |
| Availability | Free download from Kaggle. |
| Licensing | Public. Commercial use generally permitted (check terms). |
| Indian-style suitability | **Low direct fit.** US population. Thin feature set. Age, income, debt ratio, monthly income, number of dependents, credit lines, real estate loans. No bureau score. No CIBIL. |
| Expected preprocessing | **Low.** 11 features, mostly numeric, minimal missingness. |
| Fairness suitability | **High.** Age, monthly income, dependents, number of credit lines — all protected proxies (age, family status). Disaggregated fairness audit possible. |
| Provenance | Public. Single-purpose. Two-year outcome window. |
| Recommendation | **Best for academic project. Best for fairness evaluation.** Smallest dataset, cleanest preprocessing, fairness-rich. Not suitable for realistic Indian underwriting — feature set is too thin and population is wrong. |

### 2.4 German Credit (UCI Statlog)

| Field | Value |
|---|---|
| Source | [UCI Machine Learning Repository](https://archive.ics.uci.edu/ml/datasets/Statlog+(German+Credit+Data)) |
| Row count | 1,000 |
| Feature count | 20 (categorical and numeric; 24 in the original attribute names file) |
| Target definition | Binary: 1 = good credit, 2 = bad credit. |
| Availability | Free. |
| Licensing | Public. |
| Indian-style suitability | **Lowest population fit.** German borrowers, 1,000 rows. No bureau score. Categorical features (status, savings, employment) require German-language domain knowledge. |
| Expected preprocessing | Low. Small dataset, mostly categorical encoding. |
| Fairness suitability | **High in a unique way.** The dataset encodes explicitly `personal_status` (sex + marital status) and `foreign_worker` — both protected classes. A classic dataset for studying disparate-impact measurement. |
| Provenance | Documented, 30+ years old, widely cited. |
| Recommendation | **Best for fairness methodology only.** Too small, too old, too geographic. Useful as a teaching artifact. Not for production. |

### 2.5 HELOC (Home Equity Line of Credit)

| Field | Value |
|---|---|
| Source | FICO's "Explainable Machine Learning Challenge" on [Kaggle](https://www.kaggle.com/c/home-credit-default-risk/overview) (HELOC dataset released by FICO, 2018) |
| Row count | ~10,000 (anonymized HELOC applications) |
| Feature count | 23 (all numeric, derived from credit bureau) |
| Target definition | Binary: 1 = applicant repaid HELOC within 2 years, 0 = applicant was at least 90 days delinquent. |
| Availability | Free. Requires signing a research-use agreement. |
| Licensing | **Research-only. Commercial use requires separate agreement with FICO.** |
| Indian-style suitability | **Poor population fit.** US HELOC applicants. Bureau features only. No Indian-context features (no house type, no business type, no MFI-segment features). |
| Expected preprocessing | Low. Numeric features, minimal missingness. Heavy use of "RiskPerformance" in the academic literature. |
| Fairness suitability | **High.** Age, marital status, family composition are in the dataset or derivable. Disaggregated audit possible. |
| Provenance | Documented. FICO publication. |
| Recommendation | **Academic / methodology only.** Useful for explainability research and SHAP case studies. Not for production Indian underwriting. |

---

## 3. Comparison Matrix

| Dataset | Rows | Features | Target quality | License for production | Indian fit | Preprocessing effort | Fairness | Recommended role |
|---|---|---|---|---|---|---|---|---|
| Home Credit Default Risk | 307k + 1.6M history | 122 + supplements | Observed 12mo, multi-table, 0.80+ AUC achievable | **Restricted** (research/competition) | Conceptual fit, wrong geography | **High** (multi-table joins, heavy missingness) | **High** (age, gender, education) | **Realistic underwriting (after licensing)** |
| Lending Club | ~1.7M | ~150 | Observed multi-year, leakage from `grade` | Free, terms unclear | Low (US P2P) | **Moderate** (time-based split, status filter) | Moderate (state, income) | **Academic project** |
| Give Me Some Credit | 250k | 11 | Observed 2yr | Free | Low (US) | **Low** | **High** (thin features) | **Fairness / academic** |
| German Credit | 1,000 | 20 | Historical | Free | Lowest | **Low** | **High** | **Methodology only** |
| HELOC (FICO) | ~10k | 23 | Observed 2yr | **Research-only** | Poor (US) | **Low** | **High** | **Methodology / explainability** |

---

## 4. Recommendations

### 4.1 Best dataset for academic project

**Lending Club.**

Reasoning: largest publicly available dataset with observed multi-year loan outcomes. Time-stamped (`issue_d`) for proper temporal splits. Well-documented in the Kaggle community (hundreds of published notebooks for reproducibility). The `grade` leakage is a known and well-discussed footgun; a disciplined approach (dropping `grade` and `sub_grade` from the feature set) is a learning opportunity. 1.7M rows is enough to demonstrate methodology at any required scale.

### 4.2 Best dataset for realistic underwriting

**Home Credit Default Risk.**

Reasoning: closest conceptual match to the Indian MFI use case. Underbanked borrowers. Bureau-style features. Multi-table credit history. Documented at length. Proven 0.80+ AUC achievable with public benchmarks. **License must be negotiated for production.** If Home Credit's terms are not commercially usable, the fallback is Lending Club (still 0.75+ AUC achievable with discipline).

### 4.3 Best dataset for fairness evaluation

**Give Me Some Credit.**

Reasoning: smallest feature set, most protected proxies per row, cleanest disaggregation. The thin feature set forces the auditor to ask "is this model discriminating by age or by credit utilization?" — exactly the question RiskIntel needs to answer. 250k rows is enough for stable fairness metrics across demographic subgroups.

**Alternative:** German Credit has the most explicit protected-class fields but only 1,000 rows. The age effect on 1,000 rows is statistically noisy. GMSC at 250k is preferred.

---

## 5. Migration Plan

### 5.1 Phase 0 — Decision and licensing (week 0)

**Decision:** choose dataset based on the institution's commercial-use posture.
- If commercial license is obtainable: **Home Credit**.
- If not: **Lending Club** for realistic underwriting, **GMSC** for fairness.
- HELOC and German Credit are out for production.

**License review** with legal counsel. Document the license terms in `data/provenance.json` per the FORENSIC_AUDIT.md §8 acceptance gates.

### 5.2 Phase 1 — Data acquisition and provenance (week 1–2)

- Download the chosen dataset to `data/raw/<dataset_name>/`.
- Generate `data/raw/<dataset_name>/provenance.json`:
  - Source URL
  - Download date
  - File hashes (sha256)
  - License reference
  - Field reference (link to schema documentation)
  - Build date
  - Build script
- Generate `data/processed/<dataset_name>.provenance.json` with the same fields after preprocessing.
- All data lineage is now auditable from disk.

### 5.3 Phase 2 — Schema mapping (week 2–3)

Map the chosen dataset's features to `PersonARequest` or revise the schema. Two paths:

**Path A — adapt the data to the schema:**
- Income → annual_income (units convert if needed).
- Debt-to-income → recompute from balances.
- Bureau features → derive a CIBIL-equivalent (e.g., a calibrated 300–900 score from payment history).
- Loan term → standardize to months.
- Asset fields → populate from appraised values where available; mark as `null` where not.
- Dependents → integer count.
- Self-employed, education, gender, marital status → categorical mappings per `PersonARequest`.

**Path B — revise the schema:**
- Add fields the dataset has natively (e.g., `bureau_score_external`, `prior_default_count`).
- Remove fields the dataset lacks (e.g., `luxury_assets_value`).
- Update `backend/app/schemas/requests.py` and `eligibility_engine.py` to match.

**Recommendation:** Path B for Home Credit and Lending Club (the data is richer). Path A for GMSC.

### 5.4 Phase 3 — Outcome target construction (week 3)

For the chosen dataset, construct a binary target with the same semantics as the current `loan_status`:

- `1 = serious delinquency` (90+ DPD, charge-off, default).
- `0 = no serious delinquency` (fully paid, current at end of observation window).

For Lending Club, this means filtering to `loan_status ∈ {Fully Paid, Charged Off, Late (31-120 days)}` and excluding "Current" loans. Document the filter and the cohort size in the provenance.

For Home Credit, the `TARGET` column is already the outcome. No filter needed.

For GMSC, the `SeriousDlqin2yrs` column is the outcome. No filter needed.

### 5.5 Phase 4 — Temporal split and feature/target table (week 4)

- **Temporal split.** Loans originated before `T` train. Loans originated between `T` and `T+6mo` validation. Loans between `T+6mo` and `T+12mo` test.
- Choose `T` so the training set has ≥ 50,000 rows.
- Save the split indices (or `application_date` cutoffs) for reproducibility. Save in `data/processed/<dataset>.split.json`.
- Construct the final feature/target table at `data/processed/<dataset>_features.csv` and `data/processed/<dataset>_target.csv` (or single combined file).

### 5.6 Phase 5 — Baseline model and forensic re-audit (week 5)

Re-run the forensic suite from [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md) on the new dataset. The gate is:

- No single feature has point-biserial correlation > 0.50 with target.
- RF excluding any single feature achieves ≥ 0.75 AUC.
- SHAP top feature < 50% of total importance.
- Depth-1 tree on any single feature ≤ 0.85 AUC.

If the new dataset fails any gate, the institution has not solved the underlying problem (the new data may be synthetic too) and must source a third dataset. The forensic suite is the contract.

Save the forensic results to `experiments/metrics/replacement_forensic_<dataset>.json` for the audit trail.

### 5.7 Phase 6 — Retrain the production model (week 6)

- Retrain the Random Forest with the same hyperparameters as the current deployment (`n_estimators=100, max_depth=10, random_state=42`) on the new training split.
- Compare the retrained model's metrics to the forensic-suite gates.
- Re-run the calibration analysis from the previous turn (Brier, ECE, reliability diagram). The new model must also be calibrated post-training via `CalibratedClassifierCV`.
- Save the model to `models/eligibility/random_forest_v2.joblib`. Do not overwrite the v1 artifact. Both stay in the repo until v2 is deployed.

### 5.8 Phase 7 — Re-audit the system (week 7)

Re-run the same forensic suite that produced [ML_AUDIT.md](ML_AUDIT.md), [VISUAL_ACCEPTANCE_CRITERIA.md](VISUAL_ACCEPTANCE_CRITERIA.md) was not affected (frontend), and [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md) was the trigger. The v2 re-audit must include:

| Section | What changed |
|---|---|
| f1 — Target leakage | Re-run. Expect top-feature correlation ≤ 0.5. |
| f4 — Single feature AUC | Re-run. Expect top single feature ≤ 0.85. |
| f5 — Random label test | Re-run. Expect PASS. |
| f7 — Shallow tree forensics | Re-run. Expect depth-4 AUC < 0.95. |
| f9 — SHAP forensics | Re-run. Expect top feature < 50%. |
| C1 — Calibration | Re-run. Add Brier decomposition and reliability diagram. |
| F1 — Fairness | **New.** Compute demographic parity, equalized odds on the new dataset's protected columns. |
| P1 — Drift monitoring | **New.** Add PSI computation in the deployment pipeline. |
| P2 — Model version pin | **New.** SHA-256 verification at load time. |
| P3 — OOD detection | **New.** Reject inputs outside training distribution. |

The re-audit is the gate. The new model ships only if every gate passes.

### 5.9 Phase 8 — Frontend implications (week 8)

If the schema changes (Path B in Phase 2), the frontend requires changes:

- `backend/app/schemas/requests.py` — input schema.
- `backend/app/engines/eligibility/eligibility_engine.py` — feature coercion and column order.
- The frontend components in `COMPONENT_SPEC.md` (frozen) are unaffected unless the displayed feature set changes. If the new dataset has features the officer must see, the `BreakdownTable` and `DriverList` components are extended; no new components.
- The `ProbabilityRange` and verdict thresholds in `eligibility_engine.py:115-122` are recalibrated per [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md) Fix 11.

### 5.10 Phase 9 — Cutover (week 9)

- Deploy v2 in shadow mode. Run v1 and v2 in parallel; log disagreement.
- After 30 days, compare v2's shadow performance to v1's. Decision to promote v2 to active is a credit-committee call, not an engineering call.
- After promotion, deprecate v1. Do not delete the artifact — it is part of the audit trail.

---

## 6. Decision matrix

| If the institution is… | Choose |
|---|---|
| Allowed to negotiate a commercial license and has 6 months | Home Credit Default Risk. Best realism, best fairness. |
| Constrained to public-only and has 4 months | Lending Club. Largest available. Watch the `grade` leakage. |
| Building a fairness-only case study | Give Me Some Credit. Cleanest disaggregation. |
| Building a methodology paper or teaching artifact | German Credit or HELOC. Documented, cited, 1,000–10k rows. |

---

## 7. Re-audit gate (the bar v2 must clear)

The v2 model ships only if **all** of the following are true on a held-out temporal test set:

1. `f1.max_corr ≤ 0.50`
2. `f4.rf_cibil_only_auc ≤ 0.85` (or equivalent top-single-feature AUC)
3. `f5.random_label_auc ∈ [0.45, 0.55]`
4. `f7.depth4_auc ≤ 0.95`
5. `f9.top_feature_pct ≤ 50%`
6. `f2.contaminated_pct = 0`
7. `f0.constant_columns = ∅`
8. Calibration: Brier ≤ 0.20, ECE ≤ 0.05
9. **NEW** Fairness: demographic parity ratio ∈ [0.8, 1.25] across all reported subgroups
10. **NEW** Drift: PSI ∈ [0, 0.10] on the production cohort vs. training

If any gate fails, the institution has not solved the problem. The v2 model is not deployed.

---

## 8. What this document does not do

- It does not download any dataset.
- It does not write code.
- It does not retrain any model.
- It does not modify the architecture, the design brief, the design tokens, the component spec, the visual acceptance criteria, the prior forensic audit, or the prior ML governance audit.
- It does not commit to a single dataset — the choice depends on the institution's licensing posture, which only the institution can determine.

The decision space is now bounded. The forensic audit established that the data is the problem. The feasibility study establishes what data is available and what it costs to use it. The migration plan establishes the path from the current state to a defensible v2. The institution owns the choice.

---

## Summary

| Question | Answer |
|---|---|
| Best dataset for academic project | **Lending Club** |
| Best dataset for realistic underwriting | **Home Credit Default Risk** (if license obtainable) |
| Best dataset for fairness evaluation | **Give Me Some Credit** |
| Migration effort | 9 phases, 9 weeks, one re-audit gate before deployment |
| Hardest constraint | Licensing. Home Credit's terms must be reviewed by legal counsel before any acquisition. |
| Easiest first step | Phase 0: download Lending Club and GMSC today. Run the forensic suite on both. The one that passes more gates is the working candidate. |

The institution is not running a credit model today. The migration plan is the path to a defensible one.
