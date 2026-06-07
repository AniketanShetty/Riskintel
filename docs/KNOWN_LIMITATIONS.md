# RiskIntel — Known Limitations

**Date:** 2026-06-06
**Purpose:** Honest list of remaining limitations, with why-it-matters, current mitigation, and future work. Source: [ML_AUDIT.md](../ML_AUDIT.md), [ML_AUDIT_PHASE_2.md](../ML_AUDIT_PHASE_2.md), [FORENSIC_AUDIT.md](../FORENSIC_AUDIT.md), [DATA_PROVENANCE_AUDIT.md](../DATA_PROVENANCE_AUDIT.md), [REPOSITORY_REALITY_AUDIT.md](../REPOSITORY_REALITY_AUDIT.md), [DRIFT_REMEDIATION_PLAN.md](../DRIFT_REMEDIATION_PLAN.md).

---

## L-01 · No production-grade ML for E1

- **Why it matters:** The RandomForest model is a wrapper around a single CIBIL threshold. 92.9% of predictive power comes from CIBIL alone. The dataset is statistically consistent with a deterministic rule on CIBIL. Deploying the model adds opacity without adding predictive power. A real production credit model distributes signal across many features.
- **Current mitigation:** E1 is disabled in production lending paths. Shadow mode only. The institution must communicate to risk and compliance that the eligibility "model" is a CIBIL threshold.
- **Future work:** Replace `eligibility_data.csv` with a dataset whose labels come from observed 6–12-month loan performance, not a deterministic rule on CIBIL. Acceptance gates: no feature with point-biserial > 0.50; RF excluding any single feature ≥ 0.75 AUC; SHAP top feature < 50% of importance; depth-1 tree on any single feature ≤ 0.85 AUC; ≥ 50,000 rows; temporal split. Per [FORENSIC_AUDIT.md](../FORENSIC_AUDIT.md) §8 and [REPLACEMENT_DATA_FEASIBILITY.md](../REPLACEMENT_DATA_FEASIBILITY.md) §7.

## L-02 · E3 removed due to 1-row cluster and fabricated label

- **Why it matters:** KMeans(4) on 4 features produced a 1-row cluster (cluster 3 = 1 applicant with `NETMONTHLYINCOME = 2,500,000`). The label "Educated Professionals" applied to this 1-row cluster is fabricated. Narrative labels ("Young Starters", "Highly Tenured Veterans", "Mid-Career Established", "Educated Professionals") prime the loan officer with non-neutral descriptors.
- **Current mitigation:** `archetype` field removed from Person A's API response. KMeans artifact retained on disk for audit. The training script does not validate cluster sizes.
- **Future work:** Replace KMeans with quartile-based bucketing on `NETMONTHLYINCOME` (no fabricated labels) or external vendor clustering. If narrative labels are kept, they must be reviewed by a credit analyst and dated. Per [ML_AUDIT_PHASE_2.md](../ML_AUDIT_PHASE_2.md) §2.11 and §7.

## L-03 · No proven commercial license for any production dataset

- **Why it matters:** Zero of the three production datasets (`eligibility_data.csv`, `risk_tier_thresholds.json`, `borrower_archetype_definitions.json`, plus the upstream raw files) has a valid commercial license. `External_Cibil_Dataset.csv` is Kaggle Home Credit Default Risk, restricted to non-commercial research. `RuralCreditData.csv` has no source. `loan_approval_dataset.csv` has no source.
- **Current mitigation:** The institution operates on unlicensed data. A regulator inquiry cannot be answered.
- **Future work:** License review by legal counsel. Document license terms in `data/provenance.json` per dataset. Negotiation with Home Credit for commercial use, or fallback to Lending Club. Per [DATA_PROVENANCE_AUDIT.md](../DATA_PROVENANCE_AUDIT.md) §4 and §9.

## L-04 · No provenance for raw or processed datasets

- **Why it matters:** Zero `provenance.json` files. Zero `data/lineage.json`. Zero build-script references. The 4,269-row `eligibility_data.csv` is untraceable. The 51,336-row `External_Cibil_Dataset.csv` is consistent with Home Credit but unconfirmed. The 40,000-row `RuralCreditData.csv` has unknown source.
- **Current mitigation:** None. The data lineage is a black box.
- **Future work:** Generate `provenance.json` per file (`source_url`, `license`, `license_url`, `geographic_population`, `rows`, `columns`, `sha256`, `download_date`, `build_date`, `build_script`, `build_operator`). Generate `data/lineage.json` for the full graph. Per [DATA_PROVENANCE_AUDIT.md](../DATA_PROVENANCE_AUDIT.md) §5.2 and §8.

## L-05 · No drift monitoring or OOD gating

- **Why it matters:** Credit markets shift. COVID-era India saw 90-day delinquencies rise from 1.5% to 4% in months. A model trained on pre-COVID data silently misfires in a post-COVID distribution. The current system cannot detect when the live CIBIL distribution shifts. The audit lists this as CRITICAL.
- **Current mitigation:** None. No PSI, no KS test, no input-distribution monitoring, no prediction-distribution monitoring, no alerting thresholds, no scheduled re-training.
- **Future work:** Add a drift service that logs feature distribution summary statistics hourly, computes PSI weekly, triggers an alert when PSI > 0.2 on any feature. Add OOD detection: for each input feature, compare the live value against the training distribution (min, max, 1st/99th percentile). If outside, return `OUT_OF_DISTRIBUTION` error envelope and refuse the assessment. Per [ML_AUDIT.md](../ML_AUDIT.md) P1, P3, MC3.

## L-06 · First-time borrower fairness risk

- **Why it matters:** Person B (new-to-credit) has no approval labels. The readiness score is a heuristic; the bands are author-intuition. The recommendations engine uses the lowest-two-components rule, which can systematically flag the same components across a rural population. The system cannot prove it does not disadvantage first-time borrowers. RBI's Fair Practices Code requires equal treatment of similarly situated borrowers.
- **Current mitigation:** No approval probability is shown for Person B. The recommendations are framed as educational, not financial advice. The financial_health floor override (`_FINANCIAL_HEALTH_FLOOR_THRESHOLD = 0.5`) is a documented policy.
- **Future work:** Disaggregated fairness audit across sex, social_class, and rural/urban status. Document the `type_of_house` and `water_availability` proxy concern. Add an unknown-business fallback for E6 cluster 0. Per [ML_AUDIT_PHASE_2.md](../ML_AUDIT_PHASE_2.md) §3.9 and §4.11.

## L-07 · No calibration, no reliability diagram, no Brier or ECE

- **Why it matters:** `predict_proba` is consumed as a probability, but RandomForest probabilities are uncalibrated by default. The displayed 0.68 implies a frequentist interpretation that is not supported by the data. The verdict thresholds (0.80, 0.60, 0.40) are hardcoded and not derived from a cost-of-error ratio.
- **Current mitigation:** The displayed probability is rounded to 4 decimals. The ML invariant `bias + sum(contribs) = probability` is checked at runtime (`orchestrator.py:91-92, 198-206`). This catches numerical drift, not calibration drift.
- **Future work:** Wrap `predict_proba` in `CalibratedClassifierCV` with isotonic or Platt scaling. Add a reliability diagram to `experiments/`. Add a Brier score to the audit log. Recalibrate verdict thresholds against the institution's actual loss tolerance. Per [ML_AUDIT.md](../ML_AUDIT.md) C1, C2.

## L-08 · Production HTTP layer cannot start

- **Why it matters:** `python run.py` fails at import. `uvicorn app.main:app` fails at import. The Flask Blueprint `app/routes/assess.py` is dead code. The FastAPI `app/main.py` includes only the health router. There is no working endpoint.
- **Current mitigation:** The orchestrator works in-process. The 15/15 engine tests pass. The plan to fix this exists in [DRIFT_REMEDIATION_PLAN.md](../DRIFT_REMEDIATION_PLAN.md).
- **Future work:** Execute the 22-step remediation plan: install missing deps, fix `PROJECT_ROOT` depth, strip PostgreSQL types from 11 models, generate first alembic migration, register assess and reports routers, add conftest.py. Per [REPOSITORY_REALITY_AUDIT.md](../REPOSITORY_REALITY_AUDIT.md) F.1.

## L-09 · Two parallel databases with conflicting schemas

- **Why it matters:** `backend/riskintel.db` has only `alembic_version` (empty). `riskintel.db` (repo root) has `audit_log` (2 rows). They disagree. The audit log writes to one; the FastAPI config points at the other.
- **Current mitigation:** The orchestrator writes to the root DB via `app/audit.py:14` (`parents[2]` resolves to repo root).
- **Future work:** Consolidate to `backend/riskintel.db`. Fix `app/audit.py:14` to point at `parents[1]` (backend). Per [REPOSITORY_REALITY_AUDIT.md](../REPOSITORY_REALITY_AUDIT.md) C10, C11, C12.

## L-10 · No authentication, rate limiting, or access logging

- **Why it matters:** CORS is configured for `localhost:5173` and `localhost:3000`. No auth. No rate limit. No middleware implemented. Any client can call any endpoint without a token. A regulator query for "who called the API on date X" cannot be answered.
- **Current mitigation:** None.
- **Future work:** Add API key auth, rate limiting, request signing, and an access log table. The `app/middleware/` directory is empty; this is a structural gap. Per [REPOSITORY_REALITY_AUDIT.md](../REPOSITORY_REALITY_AUDIT.md) F.4 #19.

## L-11 · No model version pin or SHA verification

- **Why it matters:** The model is loaded by file path. There is no SHA-256 verification at load. If the artifact is replaced (intentionally or otherwise), the engine silently uses the new model. The audit log records lineage bind at the system level, not per-decision.
- **Current mitigation:** The model file is committed to git. Git history is not a runtime check.
- **Future work:** Store SHA-256 of the model artifact at training time. Verify at load. Add `model_version` field to the audit log per decision. Refuse to serve if SHA mismatches. Per [ML_AUDIT.md](../ML_AUDIT.md) P2, MC4.

## L-12 · Recommendation rules are templated, not applicant-specific

- **Why it matters:** A borrower rejected with `verdict=Unlikely, probability=0.32` sees generic advice: "Borrowers with lower loan-to-income ratios generally demonstrate stronger repayment capacity." The borrower's own CIBIL value and loan amount are not interpolated into the message. The action plan is 2–4 generic strings. No timeline. No specific threshold to hit.
- **Current mitigation:** Rule IDs (`A-RISK-001`, `B-IMP-001`) are logged in the audit log. Loan officers can map the ID to the rationale.
- **Future work:** Interpolate the borrower's specific values into the recommendation string. Add a magnitude indicator. Add a timeline ("improve CIBIL by 50 points in 6 months"). Per [ML_AUDIT.md](../ML_AUDIT.md) E2.

## L-13 · Rank-based recommendation selection ignores magnitude

- **Why it matters:** A borrower with components at 50, 51, 80, 80, 80 gets the same "low" flag as a borrower at 5, 6, 90, 90, 90. The first is borderline; the second is structural. The same rule fires for both. The officer cannot tell the cases apart from the recommendation.
- **Current mitigation:** None. The selection is rank-based.
- **Future work:** Add a magnitude indicator. Surface the gap between the two lowest components. If the gap is < 5 points, suppress the recommendation. Per [ML_AUDIT.md](../ML_AUDIT.md) F3.

## L-14 · Engine status is partial

- **Why it matters:** `engine_statuses` is populated per engine but does not include model version or commit hash. If the model is updated, a historical decision cannot be reproduced from the audit log alone.
- **Current mitigation:** `model_lineage_bind` is captured at the system level via `app/lineage.py`.
- **Future work:** Add per-decision `model_version` and `commit_hash` to the audit log. Per [ML_AUDIT.md](../ML_AUDIT.md) E4.

## L-15 · No model card, no MRM sign-off

- **Why it matters:** Industry practice (SR 11-7, RBI guidance, Basel III expectations) requires a model card per model, MRM sign-off, and a documented governance framework. The current repository has none of these.
- **Current mitigation:** Architecture frozen at V1.1. Output contracts frozen at V1.1.
- **Future work:** Write a model card per model (intended use, out-of-scope use, training data summary, performance metrics on holdout, fairness metrics, known limitations, retraining cadence). Engage a model validator for sign-off. Per [ML_AUDIT.md](../ML_AUDIT.md) §7 MC10.

End of limitations.
