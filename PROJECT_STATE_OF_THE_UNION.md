# RiskIntel: Project State of the Union

**Date:** 2026-06-07
**Purpose:** Single canonical handoff artifact for future AI agent sessions and human developers. This document merges all governance, policy, dataset, workflow, and architecture decisions into one binding reference.

## 1. Settled Governance & Model Risk Decisions

All engines are evaluated strictly as decision-support systems, not autonomous AIs. 

*   **E1 (Eligibility - Person A):** **DISABLED & REPLACE.** The current Random Forest model is trained on synthetic-like data, outputs mathematically invalid uncalibrated probabilities, fails on valid out-of-distribution inputs, and is non-monotonic. It must remain disabled. Rebuilding from scratch requires a legally defensible dataset.
*   **E2 (Risk Tier - Person A):** **KEEP & REBUILD (Eventually).** Kept as a deterministic policy engine mapping CIBIL scores to standard risk tiers (P1-P4). The hard rejection override (P4, CIBIL <= 658) remains but must be formally documented via a Model Card and subjected to a disparate-impact audit.
*   **E3 (Borrower Archetype - Person A):** **REMOVED.** Fundamentally broken (1-row cluster), trained on a wrong demographic (Czech/Russia/Kazakhstan), and encumbered by restrictive data licenses. It must never be executed.
*   **E5 (Readiness - Person B / Thin-File):** **KEEP.** Mandatory V1 thin-file path. It is a deterministic rule-engine scoring financial capacity (35/20/15/15/15 weights) with a hard policy floor override. It requires the addition of rule-review metadata (`last_reviewed_by`, `last_reviewed_at`).
*   **E6 (Livelihood - Person B / Thin-File):** **KEEP.** Mandatory deterministic dictionary lookup mapping stated business types to 6 clusters. Must enforce an explicit `is_unclassified` fallback flag when an unknown business type triggers Cluster 0.

## 2. Thin-File Policy & Borrower Workflow

A borrower is considered "thin-file" (Person B) if their bureau score is absent, 0, or -1. 

*   **Explicit Routing:** No silent rerouting. Missing CIBIL scores must explicitly log a `routing_decision` (`routed_to: "person_b"`, `reason: "no_bureau_score"`) and notify the caller. 
*   **No ML Predictions:** The system must never output a calibrated probability of default or approval for thin-file borrowers. It outputs a Readiness Band only.
*   **Borrower Communication:** Borrowers must see an explicit plain-language notification that they are being assessed via a readiness score based on capacity, not a traditional credit score.
*   **Fail Gracefully:** If a borrower falls into out-of-distribution thresholds, the orchestrator must return a 500 error requiring manual review, not silently fail.

## 3. Dataset Decision Registry

Zero production datasets currently possess a verified commercial use license or complete provenance. Data governance is the absolute primary blocker.

*   **REPLACE (P0):** `eligibility_data.csv` and `loan_approval_dataset.csv`. A real-outcome, commercially licensed dataset must be sourced to rebuild E1.
*   **REMOVE (P0):** `External_Cibil_Dataset.csv` (Restrictive license), `borrower_archetype_definitions.json` (Fabricated labels), `kmeans_model.pkl` and `scaler.pkl`.
*   **DELETE (P0):** All orphan bank CSVs containing PII (`BOB.csv`, `IDBI.csv`, `PNB1.csv`, `Syndicate.csv`, `Internal_Bank_Dataset.csv`). Leftover dev artifacts (`train_modified.csv`, `states.csv`, `Unseen_Dataset.csv`).
*   **ARCHIVE (P1):** `RuralCreditData.csv`, `readiness_data.csv`, `livelihood_data.csv`. Kept strictly for historical offline reference to inform E5/E6 rule design.
*   **KEEP (P1):** `risk_tier_thresholds.json`.

## 4. Loan Officer Workflow Analysis

RiskIntel is a decision-support system, not an autonomous agent. 

*   **What RiskIntel Automates:** Policy mapping (instantly maps CIBIL to P1-P4), Business categorization (standardizes unstructured text into 6 clusters), and Capacity scoring (computes standardized 0-100 readiness). Saves 10-15 minutes per case.
*   **What Remains Manual:** KYC Verification, Fraud Review, Document Review, Field Verification, and the Final Approval/Rejection Decision.
*   **Dangerous Automation (Never Do):** RiskIntel must never automate final approval decisions, fraud/KYC verification, or policy exceptions.

## 5. V1 vs. V2 Decision Boundaries

*   **V1 Immediate Mandatory Scope:** 
    * Explicit `routing_decision` in API payload to fix silent rerouting.
    * Add rule-review metadata to E5 outputs.
    * Add `is_unclassified` flag to E6.
    * Establish fail-closed audit logging without PII/input feature storage.
*   **V2 Future Scope:**
    * Rebuild E1 using real-world licensed data with calibration.
    * Redesign E5 to be an additive, proxy-free, cash-flow-centric model. Remove Infrastructure and Physical Housing material dependencies (poverty proxies).
    * Build a dedicated feature store for post-hoc demographic fairness audits.
    * Quartile-based bucketing replacement for E3.

## 6. Current Blocker Hierarchy

1.  **Data Governance (Absolute P0):** No new modeling can begin without a complete `provenance.json` for every raw/processed dataset, a `data/lineage.json` for the dependency graph, a License Review Log, and Model Cards for existing policy engines.
2.  **API/Backend Initialization:** The production HTTP layer cannot start (`app/routes/assess.py` is dead code). Database schemas conflict between `backend/riskintel.db` and the repo root `riskintel.db`.

## 7. Rejected Approaches

*   **Machine Learning for Person B (Thin-File) Scoring:** Rejected. Thin-file borrowers lack the target labels required to train a fair ML model without severe proxy discrimination.
*   **Composite V1 Freeze as Production Gate:** Rejected. The system is a V1 demo. The backend is frozen on top of a data governance void. Deployment requires fixing governance and completing re-audits.
*   **Approval Probability for Person B:** Rejected. Person B has no approval labels. The output is strictly descriptive readiness, not a credit verdict.

## 8. Open Questions & Known Limitations

*   **Calibration & Drift:** Unresolved. `predict_proba` is uncalibrated. No drift monitoring (PSI, KS test) or Out-Of-Distribution (OOD) gating exists.
*   **Model Versioning:** Unresolved. Models are loaded by path with no SHA-256 verification.
*   **Security:** Unresolved. No API authentication, rate limiting, request signing, or access logging.
*   **Recommendation Nuance:** Unresolved. Rank-based recommendations ignore magnitude (a 1-point gap triggers the same rule as a 50-point gap). Recommendations are generic, not interpolated with borrower-specific metrics.
*   **Fairness Testing:** Unresolved. First-time borrower fairness risk remains until a disaggregated fairness audit (sex, social_class, rural/urban) is run against E5.

## 9. Next Execution Order

1.  **Cleanup & Archival:** Delete all PII-bearing orphan CSVs, unknown models, and restrictive Kaggle datasets. Move reference data to `/archive`.
2.  **Documentation & Policy:** Write `provenance.json` for all retained files, consolidate a `LICENSE` inventory, and draft `MODEL_CARD_{engine}.md` for E2 and E5.
3.  **Backend Fixes:** Consolidate databases to `backend/riskintel.db`, repair API routers, and ensure `uvicorn app.main:app` runs cleanly.
4.  **V1 Immediate Requirements:** Implement explicit routing (`routing_decision`), E6 `is_unclassified` fallback, and E5 metadata in the backend responses.
5.  **Stop Point:** After step 4, the repository is legally and structurally clean. Rebuilding E1 and creating a V2 E5 are strictly deferred until post-governance data procurement.

## 10. Current Phase

**Project Phase:** Governance Remediation

**Status:**
- Architecture audit complete
- Model audit complete
- Dataset audit complete
- Thin-file policy finalized
- Workflow analysis finalized

**Current Objective:** Convert audit findings into repository artifacts.

**Success Condition:** Repository contains governance documents, model cards, license inventory, provenance framework, and cleanup execution plan.

**Failure Condition:** Any attempt to rebuild E1, redesign E5, deploy production systems, or add ML functionality before governance artifacts are completed.

## 11. Settled Decisions (Do Not Reopen)

1. E3 is permanently removed.
2. Thin-file borrowers never receive approval probabilities.
3. No ML scoring for Person B.
4. No silent rerouting.
5. Final lending decision remains human.
6. Frontend work is not a priority.
7. Data Governance precedes all modeling work.
8. Current E5 remains active in V1.
9. E1 remains disabled until licensed data exists.

## 12. Confidence Levels

**Verified:**
- E3 is removed by policy.
- Dataset registry decisions exist.
- Thin-file policy exists.
- Workflow analysis exists.

**Audited But Not Yet Verified In Current Code:**
- Explicit routing implementation.
- E6 is_unclassified fallback.
- E5 metadata injection.
- Fail-closed audit logging.

**Unknown:**
- Current runtime state.
- Current API startup state.
- Current test pass rate.
- Current database migration state.

## 13. Mandatory AI Behavior

Future AI sessions must:
1. Read this document first.
2. Challenge assumptions.
3. Do not automatically agree with the user.
4. Verify whether a decision is already settled.
5. Prefer governance correctness over implementation speed.
6. Ask for evidence when repository state is unknown.
7. Distinguish VERIFIED, AUDITED, and ASSUMED facts.
