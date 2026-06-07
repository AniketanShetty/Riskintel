# RiskIntel — Audit Summary

**Date:** 2026-06-06
**Scope:** One-page executive summary of repo state, derived from [REPOSITORY_REALITY_AUDIT.md](../REPOSITORY_REALITY_AUDIT.md), [ML_AUDIT.md](../ML_AUDIT.md), [ML_AUDIT_PHASE_2.md](../ML_AUDIT_PHASE_2.md), [FORENSIC_AUDIT.md](../FORENSIC_AUDIT.md), [DATA_PROVENANCE_AUDIT.md](../DATA_PROVENANCE_AUDIT.md), [DATA_LICENSE_VERIFICATION.md](../DATA_LICENSE_VERIFICATION.md), [DRIFT_REMEDIATION_PLAN.md](../DRIFT_REMEDIATION_PLAN.md).

---

## What RiskIntel v1 Is

**Decision-support system.** Not autonomous credit decisioning system.

Reason: v1 returns a verdict, a probability, and advisory recommendations. Final call belongs to a human loan officer. PRD §Accepted Limitations and PRD §Out of Scope make this explicit. No model in v1 is a defensible production ML system as deployed; v1 is a frozen architecture demo with a rule-based engine set wrapped around a CIBIL-threshold surrogate.

---

## Status Table

| Component | Status | Severity | Evidence |
|---|---|---|---|
| **Backend (HTTP layer)** | Not running. Both entry points fail at import. | CRITICAL | [REPOSITORY_REALITY_AUDIT.md](../REPOSITORY_REALITY_AUDIT.md) F.1 #1, C1, C2 |
| **Data Governance** | Zero production datasets have valid commercial license. Zero have `provenance.json`. | CRITICAL | [DATA_PROVENANCE_AUDIT.md](../DATA_PROVENANCE_AUDIT.md) §4, §9 (Production ML readiness: 0/3) |
| **E1 Eligibility (RF)** | FAIL. Synthetic-rule data. CIBIL contributes 92.9% of predictive power. Uncalibrated. | CRITICAL | [FORENSIC_AUDIT.md](../FORENSIC_AUDIT.md) §8, [ML_AUDIT.md](../ML_AUDIT.md) §1, §3 |
| **E2 Risk Tier (deterministic)** | CONDITIONAL PASS. Hard CIBIL thresholds, no fairness audit, no policy documentation. | HIGH | [ML_AUDIT_PHASE_2.md](../ML_AUDIT_PHASE_2.md) §1.6, [ML_AUDIT.md](../ML_AUDIT.md) F2 |
| **E3 Borrower Archetype (KMeans)** | FAIL. 1-row cluster labelled "Educated Professionals." Narrative labels in production. | CRITICAL | [ML_AUDIT_PHASE_2.md](../ML_AUDIT_PHASE_2.md) §2.11 |
| **E5 Readiness (rule-based)** | CONDITIONAL PASS. No calibration possible. Silent imputation. Rank-based recommendations. | MEDIUM | [ML_AUDIT_PHASE_2.md](../ML_AUDIT_PHASE_2.md) §3.11 |
| **E6 Livelihood (string lookup)** | CONDITIONAL PASS. Catch-all cluster 0 mislabels novel businesses. | MEDIUM | [ML_AUDIT_PHASE_2.md](../ML_AUDIT_PHASE_2.md) §4.11 |

---

## Main Findings

### Data: synthetic / untrusted
- `eligibility_data.csv` (4,269 rows) is statistically consistent with a deterministic rule on CIBIL plus noise. f7 returns `LIKELY_RULE_GENERATED_DATA, FAIL`. [FORENSIC_AUDIT.md](../FORENSIC_AUDIT.md) §1, §7.
- `External_Cibil_Dataset.csv` (51,336 rows) is Home Credit Default Risk, Czech/Russia/Kazakhstan/China. Wrong population for India-context use. [DATA_LICENSE_VERIFICATION.md](../DATA_LICENSE_VERIFICATION.md) §1.1.
- `RuralCreditData.csv` (40,000 rows) has no source, no license, no `provenance.json`. [DATA_PROVENANCE_AUDIT.md](../DATA_PROVENANCE_AUDIT.md) §6.2.

### Missing provenance
- Zero `provenance.json` files. Zero `data/lineage.json`. Zero build-script references for any processed dataset. [DATA_PROVENANCE_AUDIT.md](../DATA_PROVENANCE_AUDIT.md) §5.2.

### Licensing risks
- `loan_approval_dataset.csv`: no license, no source, no provenance. [DATA_LICENSE_VERIFICATION.md](../DATA_LICENSE_VERIFICATION.md) §1.3.
- `External_Cibil_Dataset.csv`: Kaggle competition terms restrict to non-commercial research. [DATA_PROVENANCE_AUDIT.md](../DATA_PROVENANCE_AUDIT.md) §4.
- `RuralCreditData.csv`: unknown license. Indian bank suits-filed CSVs (BOB, IDBI, PNB1, Syndicate) may require RBI notification under CICRA. [DATA_PROVENANCE_AUDIT.md](../DATA_PROVENANCE_AUDIT.md) §4.

### Fairness risks
- No demographic-parity, no equalized-odds, no disparate-impact computation. [ML_AUDIT.md](../ML_AUDIT.md) F5, MC1.
- CIBIL is a proxy for gender, caste, income (CIBIL annual reports). Hard P4 override at CIBIL ≤ 658. [ML_AUDIT.md](../ML_AUDIT.md) F2.
- 1-row KMeans cluster labelled with narrative ("Educated Professionals"). [ML_AUDIT_PHASE_2.md](../ML_AUDIT_PHASE_2.md) §2.11.
- "Young Starters" label is age-anchored and gender-correlated. [ML_AUDIT.md](../ML_AUDIT.md) F3, E3.

### Explainability issues
- Production uses `treeinterpreter`, not SHAP. Two methods can disagree. No documented canonical choice. [ML_AUDIT.md](../ML_AUDIT.md) E1, MC6.
- Recommendation rules are rank-based, not threshold-based. Magnitude of gap is not surfaced. [ML_AUDIT.md](../ML_AUDIT.md) F3.
- Recommendation strings are templated. Borrower's specific value not interpolated into the action plan. [ML_AUDIT.md](../ML_AUDIT.md) E2.

### Drift / calibration / monitoring
- No PSI, no KS test, no input-distribution monitoring, no prediction-distribution monitoring. [ML_AUDIT.md](../ML_AUDIT.md) P1.
- No Brier score, no ECE, no reliability diagram. `predict_proba` consumed as-is. [ML_AUDIT.md](../ML_AUDIT.md) C1.
- No model version pin. No SHA-256 verification at load. [ML_AUDIT.md](../ML_AUDIT.md) P2.
- No OOD detection. Missing CIBIL silently maps to 0. [ML_AUDIT.md](../ML_AUDIT.md) P3.

### Engines removed or kept

| Engine | Verdict | Action |
|---|---|---|
| E1 Eligibility | FAIL | REPLACE DATASET. Until replaced, shadow mode only. [FORENSIC_AUDIT.md](../FORENSIC_AUDIT.md) §8 |
| E2 Risk Tier | CONDITIONAL PASS | KEEP as policy engine. Document as policy, not model. Add fairness audit. |
| E3 Archetype | FAIL | REMOVE from production response. Do not serve `archetype` field for Person A. |
| E5 Readiness | CONDITIONAL PASS | KEEP. Add rules-review audit. Document every rule with `last_reviewed_at`. |
| E6 Livelihood | CONDITIONAL PASS | KEEP. Add unknown-business fallback. Surface `is_unclassified` flag. |

---

## Verdict

RiskIntel v1.0 freeze cannot stand as a production lending system. The system is a frozen architecture demo, not a deployed model. The composite readiness score is 31/100 ([ML_AUDIT.md](../ML_AUDIT.md) §9). The next phase of work is data governance and dataset replacement, not modeling. Per [REPLACEMENT_DATA_FEASIBILITY.md](../REPLACEMENT_DATA_FEASIBILITY.md), the migration plan spans 9 phases. Until dataset replacement is complete, the institution must not deploy the eligibility engine in any production lending path.

End of summary.
