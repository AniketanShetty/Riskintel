# RiskIntel — Decision Log

**Date opened:** 2026-06-06
**Source evidence:** [ML_AUDIT.md](../ML_AUDIT.md), [ML_AUDIT_PHASE_2.md](../ML_AUDIT_PHASE_2.md), [FORENSIC_AUDIT.md](../FORENSIC_AUDIT.md), [DATA_PROVENANCE_AUDIT.md](../DATA_PROVENANCE_AUDIT.md), [REPOSITORY_REALITY_AUDIT.md](../REPOSITORY_REALITY_AUDIT.md), [DRIFT_REMEDIATION_PLAN.md](../DRIFT_REMEDIATION_PLAN.md), [REPLACEMENT_DATA_FEASIBILITY.md](../REPLACEMENT_DATA_FEASIBILITY.md).

Format per entry: ID · Date · Decision · Reason · Evidence · Impact.

---

## D-001 · 2026-06-06 · E1 Eligibility disabled pending dataset replacement

- **Decision:** Disable E1 (RandomForest) in any production lending path until `eligibility_data.csv` is replaced with a real-outcome dataset.
- **Reason:** The training data is statistically consistent with a deterministic rule on CIBIL. CIBIL alone reaches 0.97 AUC. A depth-1 tree on CIBIL alone reaches 0.972 AUC. SHAP shows CIBIL at 79.7% of attribution; permutation importance at 94.16%. The Random Forest is a 100-tree wrapper around `cibil_score >= 549.5`. Deploying it adds opacity without adding predictive power.
- **Evidence:** [FORENSIC_AUDIT.md](../FORENSIC_AUDIT.md) §1–§8, [ML_AUDIT.md](../ML_AUDIT.md) §1, D1 (CRITICAL).
- **Impact:** Until replacement, the eligibility engine runs in shadow mode only. The institution must not make lending decisions on the model's output. The raw CIBIL threshold (if a decision must be made) is preferred over the model's output.

## D-002 · 2026-06-06 · E3 Archetype removed from production response

- **Decision:** Remove the `archetype` field from Person A's API response. Do not return `archetype_label`, `cluster_id`, or `description` for Person A.
- **Reason:** KMeans(4) produced a 1-row cluster (cluster 3 = 1 row) labelled "Educated Professionals." The label is fabricated. Silhouette 0.283. The training set is 88.1% male, gender-imbalanced. The narrative labels ("Young Starters", "Educated Professionals", "Highly Tenured Veterans", "Mid-Career Established") prime the loan officer with a non-neutral descriptor before they read the data.
- **Evidence:** [ML_AUDIT_PHASE_2.md](../ML_AUDIT_PHASE_2.md) §2.11 (FAIL), §2.4 (cluster sizes [19,963, 20,292, 11,080, 1]), [ML_AUDIT.md](../ML_AUDIT.md) F3, E3.
- **Impact:** Production response no longer contains the borrower archetype. The KMeans artifact and `borrower_archetype_definitions.json` remain on disk for audit. A defensible replacement (quartile-based bucketing on `NETMONTHLYINCOME`, or external vendor clustering) is a future-work item.

## D-003 · 2026-06-06 · E2 Risk Tier kept as policy engine, documented separately from ML

- **Decision:** Keep E2 (deterministic CIBIL thresholds) in production. Document it as a policy engine, not a learned model. Pair the P4 override with a model card and a quarterly disparate-impact audit.
- **Reason:** E2 is a 4-tier deterministic function on CIBIL. It does not output a probability. It does not learn from data. Its job is to encode a policy band, not to predict default. As a policy engine it is auditable. The risk is the P4 override (`orchestrator.py:141-144`), which forces a rejection at CIBIL ≤ 658 with no recourse. The override is a policy choice, not a model output, and must be defended on policy grounds.
- **Evidence:** [ML_AUDIT_PHASE_2.md](../ML_AUDIT_PHASE_2.md) §1.6 (CONDITIONAL PASS), [ML_AUDIT.md](../ML_AUDIT.md) F2.
- **Impact:** E2 stays in the response. The model card must list the override as a policy decision. A quarterly fairness audit is mandatory.

## D-004 · 2026-06-06 · E5 Readiness kept, rules-review audit mandatory

- **Decision:** Keep E5 (rule-based) in production. Add a rules-review audit: every rule in `rules_person_a.py` and `rules_person_b.py` annotated with `last_reviewed_by` and `last_reviewed_at`. Add a magnitude indicator for the rank-based improvement-area selection.
- **Reason:** E5 is auditable and deterministic. The rules are defensible as policy (lenders do weight financial health heavily). The risk is silent imputation (house_area defaults to 450 sq ft; income is proxied from monthly_expenses) and rank-based recommendations (two lowest components flagged regardless of magnitude).
- **Evidence:** [ML_AUDIT_PHASE_2.md](../ML_AUDIT_PHASE_2.md) §3.11 (CONDITIONAL PASS), [ML_AUDIT.md](../ML_AUDIT.md) D6, F3.
- **Impact:** Engine remains. Rules must be reviewed by a senior credit analyst within 90 days. Magnitude of the gap between the two lowest components must be surfaced in the API response.

## D-005 · 2026-06-06 · E6 Livelihood kept, unknown-business fallback required

- **Decision:** Keep E6 (string lookup) in production. Add `is_unclassified` flag to the response. When cluster 0 is hit, surface "novel business type, manual classification recommended" to the loan officer.
- **Reason:** E6's signature constraint (accepts only a `primary_business` string) isolates the prediction from social_class, gender, and infrastructure. The catch-all cluster 0 ("General Micro-Enterprise") mislabels novel businesses. The dictionary has 100+ entries but is not exhaustive.
- **Evidence:** [ML_AUDIT_PHASE_2.md](../ML_AUDIT_PHASE_2.md) §4.11 (CONDITIONAL PASS), §4.5, [ML_AUDIT.md](../ML_AUDIT.md) F4.
- **Impact:** Engine remains. The `is_unclassified` flag is added to the API response. A quarterly unknown-business review queue is required.

## D-006 · 2026-06-06 · Thin-file borrowers handled explicitly, no silent rerouting

- **Decision:** Borrowers with no bureau score (CIBIL = -1 or absent) are routed to the Person B path explicitly. The API response must include a `routing_decision` field with `routed_to: "person_b"`, `reason: "no_bureau_score"`, and the original `user_type`. No silent rerouting.
- **Reason:** The thin-file population is structurally different from the bureau population. They must not be evaluated by a model trained on bureau-rich data. The current `routing.py` re-routes silently; the re-route must be disclosed.
- **Evidence:** [ML_AUDIT.md](../ML_AUDIT.md) §1 (F1), PRD §Person B Workflow, [THIN_FILE_POLICY.md](THIN_FILE_POLICY.md).
- **Impact:** API contract gains a `routing_decision` field. The audit log captures the original `user_type` and the re-route reason. Borrower-facing copy explains the path taken.

## D-007 · 2026-06-06 · Data governance takes priority over modeling

- **Decision:** All modeling work is paused until data governance prerequisites are met: (1) `provenance.json` per dataset, (2) `data/lineage.json` for the full graph, (3) valid commercial license for every production dataset, (4) DPIA-equivalent review.
- **Reason:** The current data has no documented source, no license, no build script. Three production datasets have CRITICAL or HIGH licensing risk. The ML problem cannot be fixed until the data problem is fixed. Retraining the same model on the same data reproduces the same defect.
- **Evidence:** [DATA_PROVENANCE_AUDIT.md](../DATA_PROVENANCE_AUDIT.md) §4, §9 (Production ML readiness 0/3), [REPLACEMENT_DATA_FEASIBILITY.md](../REPLACEMENT_DATA_FEASIBILITY.md) §1.
- **Impact:** No new model training. No E1 retrain. No E3 rebuild. The next deliverable is a data governance package (provenance files, lineage JSON, license inventory, DPIA-equivalent document). Modeling resumes only after the governance package is complete.

## D-008 · 2026-06-06 · Persona labeling is descriptive, not verdict-bearing

- **Decision:** E5 and E6 outputs (Person B's `readiness_band` and `archetype_label`) are descriptive of the applicant's current data. They are not credit verdicts. The API contract does not show an approval probability for Person B. The borrower-facing copy makes the descriptive intent explicit.
- **Reason:** Person B has no approval labels in the training data. The PRD §Accepted Limitation 2 is explicit: "Readiness ≠ Approval Probability." Calling a "Ready" band an approval signal is a category error.
- **Evidence:** [PRD.md](../PRD.md) §Person B Workflow, §Accepted Limitation 2, [ML_AUDIT_PHASE_2.md](../ML_AUDIT_PHASE_2.md) §3.4.
- **Impact:** `verdict` is not returned for Person B. `readiness_band` is returned with a borrower-facing disclaimer. Recommendation strings are framed as educational, not financial advice.

## D-009 · 2026-06-06 · Composite v1 freeze cannot stand

- **Decision:** The v1.0 freeze is not a production deployment gate. It is an architecture freeze. The system is a v1.0 demo, not a production lending system.
- **Reason:** Composite readiness score is 31/100. Two engines FAIL (E1, E3). Three are CONDITIONAL PASS. Audit log does not store features. No drift monitoring. No calibration. No fairness audit. No model version pin.
- **Evidence:** [ML_AUDIT.md](../ML_AUDIT.md) §9 (DO NOT FREEZE), [ML_AUDIT_PHASE_2.md](../ML_AUDIT_PHASE_2.md) §8.
- **Impact:** The frozen backend is frozen on top of a data governance void. Re-audit required after the governance package and dataset replacement are complete. The v1.0 freeze does not entitle the system to production deployment.

## D-010 · 2026-06-06 · Audit log is fail-closed, feature store linkage required for fairness audits

- **Decision:** The `audit_log` table remains fail-closed (no decision without log). The log captures `correlation_id`, `request_payload_hash`, `engine_statuses`, `triggered_rule_ids`, `policy_override_flags`, `model_lineage_bind`. A separate feature store is required for any post-hoc demographic fairness audit.
- **Reason:** Fail-closed is the regulatory intent: no unlogged decisions. The log does not store PII or input features, which is privacy-positive. But a regulator query for "all decisions to a specific demographic" cannot be answered from the log alone. A feature store is a separate concern.
- **Evidence:** [ML_AUDIT.md](../ML_AUDIT.md) MC9, [REPOSITORY_REALITY_AUDIT.md](../REPOSITORY_REALITY_AUDIT.md) §A.12, `app/audit.py:14`.
- **Impact:** Audit log unchanged in v1. Feature store is a v2 dependency for any demographic audit. Borrower-facing privacy is preserved; institutional auditability is limited until v2.

End of decision log.
