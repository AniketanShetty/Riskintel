# RiskIntel — VIVA DEFENSE
**Date:** 2026-06-06
**Scope:** 50 attack questions across ML, Data, Backend, Fairness, Explainability, Governance, Product.
**Format per question:** Ideal answer · Weak answer · Follow-up attack · Strong defense.
**Stance:** Adversarial. Examiner hunts flaws. Defend with file:line evidence or admit and bound.

---

## ML (10 questions)

### Q1. Your eligibility AUC is 0.9988. Why is that not impressive?
- **Ideal:** The 0.9988 is illusory. CIBIL alone gets 0.97 AUC. A depth-1 tree on CIBIL alone gets 0.972 AUC. The model is a 100-tree wrapper around `cibil_score >= 549.5`. Permutation importance: CIBIL = 94.16%. The 0.9988 measures how well the wrapper approximates a single threshold, not how well it generalises.
- **Weak:** "It is very high accuracy." → provably wrong.
- **Follow-up:** "If CIBIL alone is 0.97, what does the other 10 features contribute? What is the AUC if CIBIL is dropped?"
- **Strong defense:** 0.027 AUC delta. CIBIL alone is 92.9% of the CIBIL-driven gain. SHAP confirms 79.7% attribution. `experiments/scripts/f7_shallow_tree_forensics.py:142-153` flags synthetic-rule data at AUC > 0.95 at depth 4.

### Q2. Why is the model a Random Forest, not logistic regression or a calibrated GBM?
- **Ideal:** No reason. RF was the first thing tried. There is no baseline comparison, no calibration, no A/B. The choice was made before the data was understood to be a single-threshold lookup. A threshold on CIBIL would have done the same job with full transparency.
- **Weak:** "RF is robust to overfitting." → RF here is fitting the threshold plus noise.
- **Follow-up:** "What is the Brier score of your model? ECE? Have you tried Platt or isotonic calibration?"
- **Strong defense:** No calibration anywhere in the codebase. `experiments/metrics/` has no reliability diagram. No `CalibratedClassifierCV`. Brier score is unmeasured. ECE is unmeasured.

### Q3. Show me your validation strategy. What is your train/test split?
- **Ideal:** Random 80/20 with `random_state=42`. **No temporal split.** This is documented in `experiments/scripts/f2_contamination.py:39-40` and is one of the audit's CRITICAL findings (D2). The Person A data has no origination date. A random split on a bureau-score-driven label is temporal leakage: the bureau score may have been pulled *after* the loan outcome.
- **Weak:** "We use stratified random split." → wrong because bureau score is quasi-leaky.
- **Follow-up:** "Where is the origination date in `eligibility_data.csv`? If it does not exist, how do you defend against temporal leakage?"
- **Strong defense:** It does not exist. `experiments/scripts/f6_feature_semantics.py:14-19` flags CIBIL as EXTREME RISK. The leakage window is the gap between the bureau pull and the loan outcome.

### Q4. You report 0.97 AUC for CIBIL alone. Why is that a warning, not a feature?
- **Ideal:** Because in credit data, a single-feature AUC > 0.85 is a leak signature. A real-world model distributes predictive power across many features. Single-feature dominance means the label is a function of that feature. `experiments/scripts/f4_single_feature_auc.json` reports `WARNING` status.
- **Weak:** "CIBIL is a strong predictor; high AUC is expected." → expected for an actual model, not expected for the dataset's label structure.
- **Follow-up:** "Does the depth-1 tree match the depth-2 tree? What is the marginal AUC of adding depth?"
- **Strong defense:** Depth-1 = 0.972 AUC. Depth-2 = 0.972 AUC. Marginal gain = 0.0005. The depth-2 splits never change the predicted class. The dataset's label structure is one split at CIBIL = 549.5.

### Q5. Your SHAP says CIBIL contributes 79.7%. Why is that misleading?
- **Ideal:** It is not misleading. It is accurate. The misleading part is the wrapper that pretends to be a multivariate model. 79.7% SHAP concentration on one feature is consistent with a lookup table. The wrapper obscures the fact that a single feature does almost all the work.
- **Weak:** "SHAP is the right method; we trust it." → SHAP is correct, the conclusion it forces is uncomfortable.
- **Follow-up:** "Why did you not use SHAP in production instead of `treeinterpreter`?"
- **Strong defense:** No documented choice. `experiments/scripts/f9_shap_forensics.py` exists but is not called. Production uses `treeinterpreter`. The two methods can disagree. `ML_AUDIT.md` E1 (MEDIUM).

### Q6. What is your class balance? Is it a problem?
- **Ideal:** 62.2% approved, 37.8% rejected. Mild imbalance. Not a problem for tree ensembles. The problem is not balance — it is that the label is a function of one feature.
- **Weak:** "It is roughly balanced; we are fine." → ignores the structural defect.
- **Follow-up:** "What is the imbalance in your *test* set? Did you stratify?"
- **Strong defense:** `stratify=y` in `train_test_split`. Imbalance is fine. The real issue is label generation. `experiments/metrics/f1_leakage_summary.json`: CIBIL point-biserial = 0.7705, MI = 0.5079.

### Q7. Walk me through your feature engineering. What did you transform?
- **Ideal:** For E1: none. Eleven raw features, integer/float coerced. `eligibility_engine.py:84-95` does `int()` and `float()` with 0 defaults. Silent imputation: missing CIBIL = 0 = P4. There is no feature engineering. There is no scaling, no one-hot, no missing-indicator, no outlier handling. The model cannot tell the difference between a missing value and a 0.
- **Weak:** "The features are already numeric." → false; categorical encoding is done inline (`edu_raw.strip().lower() == 'graduate'`).
- **Follow-up:** "If CIBIL is missing, what happens at inference? What is the verdict?"
- **Strong defense:** It silently maps to 0, which falls into P4 territory. `ML_AUDIT.md` P3 (HIGH). No OOD detection.

### Q8. Why is `treeinterpreter` and not SHAP your production attribution?
- **Ideal:** Historical choice. `treeinterpreter` was the first working library, and SHAP requires `shap` package which was not in the venv. There is no documented decision. The two methods can give different attributions on tree ensembles. The current choice is unprincipled.
- **Weak:** "`treeinterpreter` is fast and tree-specific." → fine; the issue is the missing comparison.
- **Follow-up:** "Show me one example where `treeinterpreter` and SHAP disagree on this dataset. Is that example in the API response?"
- **Strong defense:** No such example. No `f9_shap_forensics.py` call in production. `ML_AUDIT.md` E1 (MEDIUM) and MC6 (HIGH).

### Q9. How do you know the model is not overfitting?
- **Ideal:** I do not know. The reported metrics are on a random holdout. There is no temporal holdout, no cross-validation reported, no learning curve, no validation on a new geography. The 0.9988 test AUC is on the same distribution as training. If the production distribution shifts, performance will collapse.
- **Weak:** "Test AUC is high." → high AUC on in-distribution data does not mean the model generalises.
- **Follow-up:** "What is the test AUC on loans originated 6 months after your training cut-off?"
- **Strong defense:** Unknown. No temporal split. No production data to validate on. `ML_AUDIT.md` P1 (CRITICAL) — no drift monitoring.

### Q10. What does the rule `cibil_score >= 549.5 → approve` get you?
- **Ideal:** 95.36% accuracy on the dataset. 0.97 AUC. Marginally below the 0.9988 of the deployed model. The deployed model adds 0.027 AUC by fitting noise around the boundary. The marginal value of the ML layer is approximately zero.
- **Weak:** "The model is more robust." → unproven; no robustness test exists.
- **Follow-up:** "If the model is 0.027 AUC above a single threshold, and that 0.027 comes from noise, what value does the model add for the institution?"
- **Strong defense:** It adds nothing measurable. It does add opacity: a 100-tree wrapper obscures the fact that the rule is a single threshold. The institution is paying for complexity that hides a simple decision. `FORENSIC_AUDIT.md` §7.

---

## Data (8 questions)

### Q11. Where did `eligibility_data.csv` come from?
- **Ideal:** Unknown. There is no `provenance.json`, no `data/lineage.json`, no build script, no source URL. `preprocess_a.py` reads `loan_approval_dataset.csv` (a 4,269-row CSV with 13 columns that does not match the schema of any known public dataset including the Kaggle "Loan Eligibility Prediction" competition) and writes `eligibility_data.csv`. The original source cannot be reconstructed.
- **Weak:** "It is from Kaggle." → wrong; schema does not match.
- **Follow-up:** "Show me the `provenance.json`. Show me the license. Show me the build script that produces this file from a known source."
- **Strong defense:** None of these exist. `DATA_PROVENANCE_AUDIT.md` §6.1 (CRITICAL). `DATA_LICENSE_VERIFICATION.md` §1.3 (CONFIRMED UNKNOWN).

### Q12. You have a CIBIL score from 300–900. The 4,269 rows. Is that real?
- **Ideal:** I cannot prove it. The forensic suite (f7, f9) shows the labels are statistically consistent with `if cibil_score > 549.5 then 1 else 0` plus noise. The "real" structure is one split. Real credit data does not look like this. It is most likely synthetic — a teaching artifact, a demo, or a derived version of a public dataset with the leaky feature removed.
- **Weak:** "The dataset is from a Kaggle competition." → no Kaggle competition matches this schema.
- **Follow-up:** "What is the probability that the labels were generated by a deterministic rule on CIBIL?"
- **Strong defense:** Per f7, very high. f7 returns `LIKELY_RULE_GENERATED_DATA, FAIL` at depth 4 with AUC 0.996. `FORENSIC_AUDIT.md` §1.

### Q13. Why are 12 of 18 raw datasets orphans?
- **Ideal:** They are abandoned experimental artifacts. Five are Indian bank suits-filed lists (BOB, IDBI, PNB, Syndicate) — a wilful defaulter pipeline that was started and never wired up. `train_modified.csv` (87k rows) and `test_modified.csv` (37k) are a Kaggle disbursement-prediction dataset with a wrong target (`Disbursed`, not default). The rest are duplicates in different formats. None are consumed by any preprocess script.
- **Weak:** "We are keeping them for future work." → they have no documented purpose.
- **Follow-up:** "What is the legal status of the Indian bank suits-filed data? Did you obtain it under the CICRA?"
- **Strong defense:** Unknown. The data is public regulatory publication, but derivative use in a commercial product may require RBI notification. No legal review in the repo. `DATA_PROVENANCE_AUDIT.md` §4 (HIGH).

### Q14. Show me the license for the production data.
- **Ideal:** There is none. Zero of the three production datasets has a valid license for commercial use. `loan_approval_dataset.csv` has no license and no source. `RuralCreditData.csv` has no license and no source. `External_Cibil_Dataset.csv` is Kaggle Home Credit Default Risk, released for non-commercial research/competition. Production use is a license violation.
- **Weak:** "Public data is free to use." → false for Kaggle competition terms.
- **Follow-up:** "Have you read the Kaggle competition terms for Home Credit Default Risk? Do they permit commercial derivative use?"
- **Strong defense:** No. The terms restrict use to non-commercial research and competition. `DATA_PROVENANCE_AUDIT.md` §4 (CRITICAL) and §9 (Production ML readiness: 0/3).

### Q15. What is the difference between `eligibility_data.csv` and the source `loan_approval_dataset.csv`?
- **Ideal:** `loan_approval_dataset.csv` has 13 columns; `eligibility_data.csv` has 12. The schema is similar to the Kaggle "Loan Eligibility Prediction" dataset but with these changes: removed `Gender`, `Married`, `CoapplicantIncome`, `Property_Area`, `Credit_History` (the leaky feature); renamed columns to lowercase/abbreviated; added 4 asset value columns and `cibil_score`. **It is a derivative, not a direct download.**
- **Weak:** "It is a preprocessed version." → unstated from where.
- **Follow-up:** "Where is the build script that produced `eligibility_data.csv`? Is the schema change documented?"
- **Strong defense:** `backend/app/utils/preprocess_a.py` exists. It does the rename and column add. The original upstream is unspecified. `DATA_LICENSE_VERIFICATION.md` §1.3.

### Q16. Is the population Indian?
- **Ideal:** **No.** The only Indian-context dataset (`RuralCreditData.csv`) feeds E5 and E6, both of which are rule-based. The E1 model is trained on data whose source cannot be confirmed Indian. The E3 KMeans was trained on Home Credit data (Czech, Russia, Kazakhstan, China). The risk-tier thresholds match CIBIL bands, but the underlying source data is not Indian.
- **Weak:** "The application is for India." → intent does not match the data.
- **Follow-up:** "What is the source population of the 4,269 rows in `eligibility_data.csv`? Did any of them originate in India?"
- **Strong defense:** Unknown. `DATA_PROVENANCE_AUDIT.md` §1.1 row 12.

### Q17. You have 14 separate CSVs in `data/raw/`. Why so many?
- **Ideal:** Evidence of abandoned experiments. Five are Indian bank suits-filed lists (a wilful defaulter pipeline). Three are anonymized train/test (Kaggle, target is `Disbursed`, not default). Six are duplicate format variants (`_df` versions). Two are states reference lists. The 51,336-row `External_Cibil_Dataset` is the only one used in production (for E2/E3). Total orphans: ~182,889 rows, ~50% of all disk data.
- **Weak:** "We collect data aggressively." → unprincipled without lineage.
- **Follow-up:** "Which of these are licensed for commercial use? Which have been deleted under your retention policy?"
- **Strong defense:** None licensed. None deleted. `DATA_PROVENANCE_AUDIT.md` §3 and §7.2.

### Q18. How do you detect dataset drift at the data layer?
- **Ideal:** We do not. There is no PSI computation, no KS test, no input-distribution monitoring, no prediction-distribution monitoring, no scheduled re-training, no input-hash check. The audit lists this as a CRITICAL finding (P1). The system cannot detect when the live CIBIL distribution shifts.
- **Weak:** "The orchestrator logs every request." → logs do not detect drift.
- **Follow-up:** "What is your PSI threshold? What is your alerting path? Who is paged when PSI > 0.2?"
- **Strong defense:** None. No PSI threshold. No alerting path. No pager. `ML_AUDIT.md` P1 (CRITICAL).

---

## Backend (8 questions)

### Q19. Can I run your backend right now?
- **Ideal:** **No.** `python run.py` fails at import (`ImportError: cannot import name 'create_app' from 'app'`). `uvicorn app.main:app` fails at import (`ModuleNotFoundError: No module named 'fastapi'`). The venv is missing FastAPI, uvicorn, SQLAlchemy, Alembic, aiosqlite, pydantic, pydantic-settings, httpx. There is no working HTTP entry point.
- **Weak:** "Yes, run `uvicorn app.main:app`." → fails immediately.
- **Follow-up:** "Show me a `curl http://localhost:8000/api/assess/person-a` that returns 200."
- **Strong defense:** Cannot. Zero HTTP traffic is served. The Flask Blueprint `app/routes/assess.py` is dead code; it is never imported. `REPOSITORY_REALITY_AUDIT.md` F.1 #1.

### Q20. Why are there two parallel architectures?
- **Ideal:** Incomplete migration. The codebase started on Flask, migrated to FastAPI, and the migration is partial. Flask remnants: `app/__init__.py` (no `create_app`), `app/config.py` (Flask `Config` class with `SECRET_KEY`), `app/routes/assess.py` (Blueprint, never registered), `run.py` (Flask entry, broken). FastAPI path: `app/main.py`, `app/api/`, `app/core/`, `app/db/`, `app/models/`, `alembic/` (versions/ missing). The orchestrator works in-process. The HTTP layer does not.
- **Weak:** "We support both." → both are broken.
- **Follow-up:** "Which one is the production path? Why are both still in the repo?"
- **Strong defense:** `DRIFT_REMEDIATION_PLAN.md` says: lock to FastAPI, delete Flask remnants. Plan exists, not executed. `REPOSITORY_REALITY_AUDIT.md` D.1 + D.2.

### Q21. Where is your database? What does it contain?
- **Ideal:** Two SQLite databases on disk. `backend/riskintel.db` has only the `alembic_version` table (empty). `riskintel.db` (repo root) has `audit_log` (2 rows). They disagree. The audit log writes to the root one; the FastAPI config points at the backend one. **No application data has ever been persisted.**
- **Weak:** "SQLite, with the schema." → schema is empty.
- **Follow-up:** "What is the `applicants` table schema? Where are the `assessments` rows?"
- **Strong defense:** `applicants` is defined in `app/models/applicant.py` but `alembic upgrade head` has never been run. There is no migration in `alembic/versions/` (the directory does not exist). `REPOSITORY_REALITY_AUDIT.md` C10, C11, C12.

### Q22. Walk me through your POST `/api/assess/person-a` request lifecycle.
- **Ideal:** The route does not exist. `app/main.py:130` includes only `app.api.health.router` under prefix `/health`. There is no router for `POST /api/assess/person-a`, no `POST /api/assess/person-b`, no `POST /api/report/generate`. The frozen output contract requires these routes. They are not implemented.
- **Weak:** "It goes through the orchestrator." → correct engine call, no HTTP wiring.
- **Follow-up:** "Show me the FastAPI router file that defines the route."
- **Strong defense:** `app/api/v1/assess.py` does not exist. The plan to add it is in `DRIFT_REMEDIATION_PLAN.md` §4.2, not in the repo. `REPOSITORY_REALITY_AUDIT.md` F.1 #5.

### Q23. You have 11 SQLAlchemy models. Can they run on SQLite?
- **Ideal:** **No.** All 11 use `postgresql.UUID(as_uuid=True)` and `postgresql.JSONB`. The `assessment.py` model adds a GIN index. The engine URL is `sqlite+aiosqlite:///riskintel.db`. These types are PostgreSQL-only. Even with `aiosqlite` installed, `Base.metadata.create_all` will fail on the type adapters.
- **Weak:** "SQLAlchemy abstracts the database." → not for vendor-specific types.
- **Follow-up:** "What does `Base.metadata.create_all` produce on SQLite for the `Applicant` model? Walk me through the DDL."
- **Strong defense:** It raises. `REPOSITORY_REALITY_AUDIT.md` C8, F.1 #4.

### Q24. What is the `audit_log`? Why is it fail-closed?
- **Ideal:** `app/audit.py` writes one row per orchestrator run. Fail-closed means: if the audit write fails, the entire response is rejected. The reasoning is regulatory: an unlogged decision is an unauditable decision. The audit captures `correlation_id`, `model_lineage_bind`, `final_verdict`, `engine_statuses`, `triggered_rule_ids`, `policy_override_flags`, `request_payload_hash`. It does **not** capture the input features, so post-hoc fairness audits on the audit log are impossible.
- **Weak:** "It is for debugging." → it is a regulatory artifact.
- **Follow-up:** "If a regulator asks for all decisions made to a specific demographic, can you query the audit log?"
- **Strong defense:** No, because features are not stored. `ML_AUDIT.md` MC9 (MEDIUM). Feature store linkage is required for any post-hoc demographic audit.

### Q25. You have a `treeinterpreter` polyfill. Why?
- **Ideal:** `treeinterpreter` depends on `distutils`, which was removed in Python 3.12. The polyfill in `eligibility_engine.py:13-23` is a hand-rolled `LooseVersion` substitute. It works today. It is a maintenance liability: no test verifies its semantics, and a future Python release could change `LooseVersion` behaviour in ways the polyfill does not capture.
- **Weak:** "It is a quick fix." → it is unprincipled.
- **Follow-up:** "What is your test that locks the polyfill's behaviour? What happens if a future Python release changes string comparison?"
- **Strong defense:** No test. No locking. The polyfill is fragile. `ML_AUDIT.md` P7 (MEDIUM).

### Q26. Where is your test suite? How much coverage?
- **Ideal:** 15/15 engine tests pass (`backend/tests/engines/test_livelihood_mapper.py` + `test_recommendation_engine.py`). **7 of 9** `backend/tests/*.py` files cannot be collected because they import `from fastapi.testclient import TestClient` and `fastapi` is not in the venv. There is no `conftest.py`, no `pytest.ini`, no shared fixtures, no transactional rollback. The legacy e2e tests in `legacy_archive/` and the top-level `test_audit_fail_closed.py` / `test_ml_contract_fuzzing.py` import modules that do not exist.
- **Weak:** "317 tests pass." → only 15 are runnable.
- **Follow-up:** "Show me a passing e2e test for the eligibility path. Run it live."
- **Strong defense:** Cannot. `REPOSITORY_REALITY_AUDIT.md` F.2 #6, #8, #9.

### Q27. What is your API rate limiting? Auth? CORS?
- **Ideal:** CORS is configured (`localhost:5173`, `localhost:3000`). No authentication. No rate limiting. No middleware implemented (the `app/middleware/` directory is empty). Any client can call any endpoint without a token. No request signing, no mTLS, no API key. The audit log records who-callled (the IP, if at all) by default.
- **Weak:** "Internal network only." → unstated.
- **Follow-up:** "If a regulator asks for the access log, what can you produce? Who has API keys?"
- **Strong defense:** Nothing. No auth, no rate limit, no access log. The audit log captures `correlation_id` and payload hash, not the caller.

---

## Fairness (8 questions)

### Q28. Where are your protected-class features?
- **Ideal:** Absent from `eligibility_data.csv` (E1). Present in `readiness_data.csv` (`sex`, `social_class`) and `External_Cibil_Dataset.csv` (`GENDER`, `MARITALSTATUS`, `EDUCATION`) used for E3 KMeans. The E1 model cannot directly discriminate by gender because the feature is not in the data. **But absence of the feature is not fairness** — proxies remain.
- **Weak:** "We do not use gender." → correct, but the proxy problem remains.
- **Follow-up:** "Is CIBIL a proxy for gender? For caste? For income?"
- **Strong defense:** CIBIL is correlated with socioeconomic status, income, and (documented in CIBIL annual reports) gender. The CIBIL threshold is a textbook proxy. `ML_AUDIT.md` F2 (CRITICAL).

### Q29. What is your disparate-impact ratio for the P4 override?
- **Ideal:** Unmeasured. The P4 override (`orchestrator.py:141-144`) fires for CIBIL ≤ 658. There is no demographic-parity, equalized-odds, or disparate-impact computation anywhere in the codebase. I cannot answer this question because the metric is not measured.
- **Weak:** "CIBIL is objective." → objective features can still produce disparate impact.
- **Follow-up:** "Run f13_fairness.py on the 4,269 rows, broken down by simulated gender, and report the P4 rate ratio."
- **Strong defense:** `f13_fairness.py` does not exist. The plan to add it is in `ML_AUDIT.md` Fix 3. `ML_AUDIT.md` F5 (MEDIUM), MC1 (CRITICAL).

### Q30. A borrower with CIBIL 658 gets P4. A borrower with CIBIL 700 gets P2. Is that fair?
- **Ideal:** The hard threshold produces a discontinuous function at CIBIL = 658.5. Two borrowers who differ by 2 points get materially different treatments. Without a recourse mechanism, a borrower at 660 cannot easily move to 700. CIBIL updates monthly. There is no margin of safety, no warning, no escalation.
- **Weak:** "The threshold is policy." → policy without recourse is not defensible.
- **Follow-up:** "What is the recourse path for a borrower at 659? How do they know what to do?"
- **Strong defense:** The recommendations engine produces advice, but it is generic and not tied to the override. There is no recourse workflow. `ML_AUDIT.md` F2 (CRITICAL).

### Q31. Your KMeans cluster has 1 row. How is that defensible?
- **Ideal:** It is not. The 1-row cluster (`Educated Professionals` in `borrower_archetype_definitions.json`) is a fragility of KMeans with high-cardinality income. One applicant with `NETMONTHLYINCOME = 2,500,000` is its own cluster. The label "Educated Professionals" applied to this one applicant is meaningless. A new applicant similar to this 1-row applicant will either join the cluster (making it 2 rows) or shift cluster boundaries. The cluster identity is not stable.
- **Weak:** "KMeans is unsupervised." → that does not excuse a 1-row cluster labelled with a narrative.
- **Follow-up:** "What is your minimum cluster size policy? Did the training script check it?"
- **Strong defense:** No policy. No check. The training script `scripts/train_borrower_archetype.py:55-57` does not validate cluster sizes. The audit verdict is **FAIL — remove from production**. `ML_AUDIT_PHASE_2.md` §2.11.

### Q32. Your label "Young Starters" goes to a loan officer. Is that biased?
- **Ideal:** Yes. The label is age-anchored and gender-correlated through the training data. The KMeans was trained on data where 88.1% of rows are male; the "Young Starters" cluster is 89.3% male. A loan officer seeing "Young Starters" has been primed with a narrative descriptor before reading the data. The label is not neutral.
- **Weak:** "It is just a label." → labels bias decisions.
- **Follow-up:** "Did you A/B test officer decisions with and without the narrative label?"
- **Strong defense:** No A/B test. The label was added to the response contract. `ML_AUDIT.md` E3 (MEDIUM), F3 (HIGH).

### Q33. Your readiness engine uses `type_of_house` and `water_availability`. Are these protected proxies?
- **Ideal:** Likely. `type_of_house` ("R", "T1", "T2") correlates with rural/urban status. `water_availability` ("none", "partial", "full") and `sanitary_availability` correlate with socioeconomic status. The engine uses these as inputs. A borrower in a rural area with partial water access is structurally disadvantaged by the rule.
- **Weak:** "They are infrastructure features." → infrastructure is a proxy for class.
- **Follow-up:** "What is the readiness score gap between rural and urban applicants at the same income?"
- **Strong defense:** Unmeasured. No disaggregated fairness audit. `ML_AUDIT_PHASE_2.md` §3.9 (MEDIUM).

### Q34. Catch-all cluster 0 ("General Micro-Enterprise") labels novel businesses. Is that fair?
- **Ideal:** It is a known source of bias. Borrowers whose `primary_business` is not in the dictionary ("computer repair", "tutoring center", "boutique") are silently classified as cluster 0 with description "Unclassified." This is misclassification presented as a result. The audit recommends adding an `is_unclassified` flag and an unknown-business fallback.
- **Weak:** "It is a fallback." → the fallback is silent and mislabelled.
- **Follow-up:** "Show me the API response for a borrower whose business is not in the dictionary. Does the loan officer see 'Unclassified'?"
- **Strong defense:** Yes. `ML_AUDIT_PHASE_2.md` §4.5, F4 (MEDIUM).

### Q35. RBI fair-lending code requires adverse-action reasons. Where are yours?
- **Ideal:** Not implemented. The PRD §Out of Scope explicitly excludes "Regulatory Adverse Action Notices." There is no FCRA/ECOA equivalent for India, but RBI's Fair Practices Code requires lenders to communicate specific reasons for rejection. The current API returns a verdict and a generic recommendation list. There is no per-rejection explanation that names the feature(s) that drove the decision.
- **Weak:** "The recommendations engine produces reasons." → the recommendations are generic, not applicant-specific quantification.
- **Follow-up:** "For a rejected borrower, can you produce a list of the top 3 specific factors that caused rejection, with applicant-specific values?"
- **Strong defense:** No. The recommendation rules use rank-based heuristics, not threshold-based, and the rationale string is generic. `ML_AUDIT.md` E2 (MEDIUM).

---

## Explainability (6 questions)

### Q36. The API returns `feature_contributions` for E1. Is that the same as SHAP?
- **Ideal:** No. `treeinterpreter` is used (`eligibility_engine.py:101`). It returns per-feature contributions to the prediction, but the method is not SHAP. `treeinterpreter` decomposes the bias + per-feature contributions; SHAP satisfies efficiency and local accuracy. They can disagree on attribution. There is no documented canonical choice. `experiments/scripts/f9_shap_forensics.py` exists but is not called in production.
- **Weak:** "It is explainability." → wrong method, no comparison.
- **Follow-up:** "Show me one example where `treeinterpreter` and SHAP give different attributions for the same input."
- **Strong defense:** No such example. `ML_AUDIT.md` E1 (MEDIUM), MC6 (HIGH).

### Q37. A borrower asks "why was I rejected?" What do you show them?
- **Ideal:** The API response includes `verdict`, `probability`, `bias`, `feature_contributions` (11 features), and `recommendations` (a list of generic strings keyed to top negative contributors). The borrower sees: a probability, a list of features ranked by negative contribution, and 2–4 generic recommendation strings. The recommendations are anchored (`A-RISK-001`, `A-RISK-002`) but the rule rationale is not surfaced as plain text. The loan officer sees the rule ID in the audit log, not in the response.
- **Weak:** "The recommendations engine produces explanations." → the explanations are templated.
- **Follow-up:** "For a borrower rejected with `verdict=Unlikely, probability=0.32`, what is the borrower-facing message?"
- **Strong defense:** Templated: "Borrowers with lower loan-to-income ratios generally demonstrate stronger repayment capacity" (if `loan_amount` is top negative). The borrower does not see their own value compared to a threshold.

### Q38. The ML invariant `bias + sum(contribs) = probability` — how do you enforce it?
- **Ideal:** `orchestrator.py:91-92` raises if `abs(bias + sum - probability) > 1e-4`. The check is in-process. `orchestrator.py:198-206` re-checks at `1e-3` tolerance and logs a warning. The invariant holds for `treeinterpreter` on a Random Forest by construction. The check exists to catch numerical drift.
- **Weak:** "The model returns it." → correct, but a runtime guard is needed because of float arithmetic.
- **Follow-up:** "If the invariant breaks at tolerance 1e-4, what does the orchestrator do? Does the borrower get a 500?"
- **Strong defense:** `CriticalEngineError` is raised; the response is rejected. The audit log is not written. The caller gets a 500.

### Q39. The `archetype_label` ("Young Starters") — is that a feature or a verdict?
- **Ideal:** Neither, formally. It is a cluster ID with a narrative name assigned by a hand-coded ranking. The cluster identity is the result of KMeans on 4 features. The label is a marketing-style descriptor. The loan officer sees "Young Starters" adjacent to the verdict. There is no documented "this is a cluster label, not a credit signal" disclosure.
- **Weak:** "It is a clustering." → clusters are not neutral.
- **Follow-up:** "Where in the response is the disclaimer that the label is a cluster identity and not a credit recommendation?"
- **Strong defense:** Nowhere. `ML_AUDIT.md` E3 (MEDIUM).

### Q40. Your recommendation rules use rank-based selection. Why not thresholds?
- **Ideal:** Historical. `rules_person_b.py:9-15` selects the two lowest-scoring components as "improvement areas" regardless of magnitude. A borrower with components at 50, 51, 80, 80, 80 gets the same "low" flag as a borrower at 5, 6, 90, 90, 90. The first is borderline; the second is structural. The same rule fires.
- **Weak:** "It is simple." → simple is fine, but the rule does not surface magnitude.
- **Follow-up:** "What is the magnitude of the gap between the two lowest components in a typical response? Is the gap shown to the officer?"
- **Strong defense:** No. The audit recommends adding a magnitude indicator. `ML_AUDIT.md` F3 (HIGH).

### Q41. Walk me through a recommendation for a borderline rejected borrower.
- **Ideal:** E1 returns verdict=`Unlikely`, probability≈0.35, top negative contributors = `cibil_score` and `loan_amount`. E2 returns P4. E3 returns "Young Starters" or similar. The override fires (`OVERRIDE_E2_P4_REJECTION`). E4 produces: `risk_factors` includes "Current credit score falls below optimal premium tier thresholds" (A-RISK-002) and "Requested loan amount poses a high debt-to-income burden" (A-RISK-001) if `loan_amount` is top negative. `action_plan` includes "Monitor credit profile" and "Review if a lower principal amount meets core requirements". None of these strings contain the borrower's specific value. The borrower sees generic advice.
- **Weak:** "Personalized recommendations." → templated.
- **Follow-up:** "Does the action plan reference the borrower's specific CIBIL value or loan amount?"
- **Strong defense:** No. The recommendation strings are constant. `recommendation_engine.py` interpolates a `{score}` placeholder for the A-STR-001 rule, but most rules do not interpolate. `ML_AUDIT.md` E2 (MEDIUM).

---

## Governance (6 questions)

### Q42. Is this model production-ready?
- **Ideal:** **No.** Audit verdict is **DO NOT FREEZE**. E1 is FAIL (synthetic-rule data). E3 is FAIL (1-row cluster, narrative labels). E2, E5, E6 are CONDITIONAL PASS. Composite readiness 31/100. The v1.0 freeze cannot stand.
- **Weak:** "It is frozen and documented." → frozen does not mean production-ready.
- **Follow-up:** "What is the regulatory sign-off? Who is the model validator?"
- **Strong defense:** No model validator. No regulatory sign-off. `ML_AUDIT.md` §9. The system is a v1.0 demo of the architecture. Not a production lending model.

### Q43. What is your model risk management framework?
- **Ideal:** There is none. The audit lists 10 missing controls (MC1–MC10): no fairness audit, no calibration monitoring, no drift detection, no model registry with version pinning, no shadow mode, no SHAP at inference, no data lineage, no rule content review, no protected-class suppression, no model card. Each is a control that industry practice (SR 11-7, RBI guidance, Basel III expectations) requires.
- **Weak:** "We have a repo with code." → code is not a framework.
- **Follow-up:** "Show me your model card. Show me your monitoring dashboard. Show me your MRM sign-off."
- **Strong defense:** None of these exist. `ML_AUDIT.md` §7.

### Q44. What is your model version pin strategy?
- **Ideal:** The model is loaded by file path (`models/eligibility/random_forest.joblib`). There is no SHA-256 verification at load. The model lineage metadata is in `model_lineage_bind` (read by `app/lineage.py`), but the engine does not verify the loaded file matches the declared lineage. If the artifact is replaced, the engine silently uses the new model. Audit log records model_lineage_bind at the system level, not per-decision.
- **Weak:** "We commit the file." → git history is not a runtime check.
- **Follow-up:** "If someone replaces the joblib file with a different model tonight, will the audit log detect it?"
- **Strong defense:** No. `ML_AUDIT.md` P2 (CRITICAL), MC4 (HIGH).

### Q45. RBI's Digital Lending Guidelines require a Data Protection Impact Assessment. Where is yours?
- **Ideal:** Not performed. There is no DPIA document. There is no legal review of the data sources. The Indian bank suits-filed data, if any is used, may require RBI notification under CICRA. The `RuralCreditData.csv` has no license, no source, no DPIA. The Kaggle Home Credit data is restricted to non-commercial research. **Three production datasets have CRITICAL or HIGH licensing risk.**
- **Weak:** "We are not a regulated entity." → unverified.
- **Follow-up:** "Have you read the RBI Master Circular on Wilful Defaulters? Have you checked CICRA for the bureau data?"
- **Strong defense:** No DPIA. No legal review. `DATA_PROVENANCE_AUDIT.md` §4.

### Q46. What is your feature store? Can you reproduce a decision from 6 months ago?
- **Ideal:** No feature store. The audit log captures `correlation_id`, payload hash, engine statuses, rule IDs, and the lineage bind. It does **not** capture the input features. To reproduce a decision, you would need the original payload, which is not stored. The model artifact is on disk; the data is reproducible. The exact input that produced a decision is not.
- **Weak:** "The audit log has the correlation ID." → without features, the correlation ID is not enough.
- **Follow-up:** "A regulator asks: 'Show me all decisions to borrowers named X in March 2026.' Can you do it?"
- **Strong defense:** No. The audit log does not store PII. The features are not stored. `ML_AUDIT.md` MC9 (MEDIUM).

### Q47. Your audit log is fail-closed. What if the database is unavailable?
- **Ideal:** The orchestrator raises `AuditLogError` and rejects the response. The decision is not returned. The borrower gets a 500. The institution has no way to make a decision without logging. This is the regulatory intent (no unlogged decisions), but operationally it means a DB outage blocks all decisions. There is no read-after-write fallback, no async log buffer.
- **Weak:** "We log everything." → we log only when the DB is up.
- **Follow-up:** "What is your RTO/RPO for the audit log? Can you lose 5 minutes of decisions?"
- **Strong defense:** No defined RTO/RPO. No async buffer. Single SQLite file. `app/audit.py` fail-closed at line 14.

### Q48. If your model makes a discriminatory decision tomorrow, how do you find out?
- **Ideal:** You do not. There is no demographic-parity monitoring, no outcome monitoring by subgroup, no disparate-impact alarm. The only feedback is borrower complaints, which are not in the audit pipeline. The institution learns about discrimination from external complaint, not from internal monitoring.
- **Weak:** "We have a complaints process." → reactive, not proactive.
- **Follow-up:** "What is the demographic disaggregation of your P4 rejections over the last 90 days?"
- **Strong defense:** Unmeasured. `ML_AUDIT.md` P1 (CRITICAL), MC1 (CRITICAL).

---

## Product (4 questions)

### Q49. The borrower gets a verdict. What do they do with it?
- **Ideal:** The PRD says "Eligibility Assessment" with four bands (Highly Likely, Likely, Borderline, Unlikely). The product does **not** show an approval probability to Person B (explicitly). The recommendations are advisory and educational, not financial advice. A borderline borrower sees a probability and generic advice. There is no recourse workflow, no escalation path, no human handoff, no follow-up.
- **Weak:** "They get a clear answer." → they get a probability and generic advice.
- **Follow-up:** "If a borderline borrower asks 'what can I do in 6 months to improve,' what does the system tell them?"
- **Strong defense:** The action plan lists 2–4 generic strings. No timeline. No specific threshold to hit. No connection to the CIBIL or income factors that drove the verdict. `recommendation_engine.py` is rule-based; rules are static.

### Q50. Why is this a loan decision support system and not a loan decision system?
- **Ideal:** Because the predictions are uncalibrated, the data is synthetic-rule, and the bias risk is unmeasured. Calling it "decision support" rather than "decision making" is a regulatory hedge. The bank employee workflow generates a PDF for human review, not an automated decision. The PRD's §Accepted Limitations document this: "Recommendations are advisory and educational. Not financial advice."
- **Weak:** "The bank employee makes the final call." → true but the bank employee's call is shaped by the model's output.
- **Follow-up:** "If the loan officer approves a borrower the model scored Unlikely, is that the model's fault or the officer's?"
- **Strong defense:** It is the officer's call, but the model's output biases the call. The narrative label, the probability, the override flags — all shape the officer's decision. The system is a "decision support" only in name. `ML_AUDIT.md` F3, E3, E2.

---

## Cross-Cutting Strong-Defense Posture

If the examiner opens a new line:

- **"Your system cannot start."** True. The HTTP layer is unwired. The plan to fix it exists (`DRIFT_REMEDIATION_PLAN.md`), but it is not executed. The 317-test claim in `ML_AUDIT.md` is wrong — only 15 tests run, 7 cannot be collected.
- **"Your data is unlicensed."** True. Zero of three production datasets has a valid commercial license.
- **"Your model is a CIBIL threshold."** True. The audit's four-way forensic convergence (f1, f4, f7, f9) is reproducible.
- **"Your fairness is unmeasured."** True. No demographic-parity, no equalized-odds, no disparate-impact.
- **"Your E3 has a 1-row cluster."** True. Cluster 3 = 1 row, labelled "Educated Professionals."
- **"Your audit log does not store features."** True. Privacy-positive default, but post-hoc fairness audits require a feature store.
- **"Your drift monitoring is absent."** True. No PSI, no KS, no alerting, no scheduled re-training.
- **"Your deployment is impossible."** True. No CI, no docker-compose, no Alembic migration, no model version pin.

The honest answer to most questions is: "The audit flagged this. The fix is in the plan. It is not done. The v1.0 freeze should not stand." The composite readiness is 31/100. The institution has a v1.0 demo of the architecture. It does not have a production lending system.

End of defense.
