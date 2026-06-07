# RiskIntel — Model Risk Committee Decision

**Date:** 2026-06-07
**Status:** Binding Model Risk Committee Order

## 1. Executive Summary

This document represents the binding, independent go/no-go decision for every decision-support engine in the RiskIntel backend. The system is evaluated strictly as a decision-support system, not an autonomous AI. Any engine lacking data provenance, calibration, or fairness controls has been downgraded or removed.

## 2. Engine Decisions

### 2.1 E1 — Eligibility Engine (Person A)

- **Current State:** RandomForest model trained on synthetic-rule data of unknown origin. `predict_proba` outputs are uncalibrated and treated as confidence. The model fails on valid out-of-distribution CIBIL inputs (raises unhandled exceptions for 7 of 17 CIBIL bands). Probabilities are non-monotonic (a better CIBIL score can yield a lower approval probability).
- **Risk Level:** **CRITICAL**
- **Decision:** **REPLACE**
- **Justification:** E1 is not production-safe. The model is a wrapper around a single CIBIL threshold, trained on synthetic data without a valid commercial license. The output probabilities are mathematically uncalibrated and conceptually non-monotonic. The feature contributions are artifacts, not economic signals, and cannot be defended to a customer or a regulator.
- **Required Actions:**
  - Keep E1 completely disabled in production.
  - Source a new, real-outcome dataset with a documented commercial license and `provenance.json`.
  - Rebuild from scratch. Implement OOD detection, `CalibratedClassifierCV`, and enforce a monotonic constraint.
  - Maintain the `THIN_FILE_NOT_SUPPORTED` explicit fallback for any applicant without a bureau score until the system is rebuilt.

### 2.2 E2 — Risk Tier Engine (Person A)

- **Current State:** Deterministic, hard-coded threshold lookup on integer CIBIL scores. A P4 policy override automatically rejects borrowers below a CIBIL of 658. The thresholds currently lack a documented cost-of-error rationale.
- **Risk Level:** **HIGH**
- **Decision:** **REBUILD**
- **Justification:** E2 is a policy engine, not a learned ML model. It is completely reproducible and technically defensible as a set of rules. However, the thresholds (701/669/658) are not empirically derived from observed default rates, and the P4 override carries a proxy discrimination risk without a disparate-impact audit.
- **Required Actions:**
  - Retain in production as a deterministic lookup.
  - Formally document the policy rationale for the current thresholds in a Model Card.
  - Run a disparate-impact audit on the P4 override.
  - Once E1's replacement dataset is sourced, recompute and update these thresholds based on observed real-world default rates.

### 2.3 E3 — Borrower Archetype Engine (Person A)

- **Current State:** KMeans clustering model returning narrative labels (e.g., "Educated Professionals", "Young Starters"). Trained on Home Credit Group data (wrong geographic population) under a restrictive research-only license. One cluster contains exactly 1 row.
- **Risk Level:** **CRITICAL**
- **Decision:** **REMOVE**
- **Justification:** E3 is fundamentally broken. The cluster labels are fabricated and the 1-row cluster renders the model's centroid mathematics meaningless. The training data represents a Czech/Russia/Kazakhstan demographic, making it entirely inapplicable to the target Indian population. The restrictive data license legally prohibits its use in a commercial production system.
- **Required Actions:**
  - Remove E3 and `get_borrower_archetype` from the production response completely.
  - Delete `borrower_archetype_definitions.json`.
  - Do not replace in v1. Any future segmentation must use quartile bucketing or a licensed external vendor.

### 2.4 E5 — Readiness Engine (Person B / Thin-File)

- **Current State:** Hand-coded, deterministic rule engine that outputs a 0-100 score based on 5 components (financial health, housing stability, infrastructure, household burden, business viability). It includes a hard policy floor override if financial health is below 0.5.
- **Risk Level:** **MEDIUM**
- **Decision:** **KEEP**
- **Justification:** E5 is the only engine capable of defensibly scoring thin-file borrowers without relying on missing bureau data. It contains no ML models, meaning it is 100% reproducible and auditable. Its primary risk is that the component weights (35/20/15/15/15) are authored by intuition rather than empirical policy.
- **Required Actions:**
  - Retain in production as the mandatory thin-file path.
  - Publish a Model Card explicitly documenting the 35/20/15/15/15 weights and the 0.5 floor breach as institutional policy.
  - Add a rule-review timestamp (`last_reviewed_at`) and require a senior credit analyst to sign off on the 14 recommendation rules.

### 2.5 E6 — Livelihood Engine (Person B / Thin-File)

- **Current State:** Deterministic hash-map lookup mapping 100+ business strings to 6 cluster IDs. Unknown inputs fall into Cluster 0 ("General Micro-Enterprise").
- **Risk Level:** **LOW**
- **Decision:** **KEEP**
- **Justification:** E6 is a fully explainable, pure string-matching dictionary. The signature constraint securely isolates the decision from demographic or protected-class features. The only risk is the silent catch-all behavior for novel businesses.
- **Required Actions:**
  - Retain in production.
  - Add an explicit `is_unclassified` boolean flag to the response payload whenever Cluster 0 is triggered.
  - Maintain a quarterly review queue to document and add unclassified business strings to the dictionary.
