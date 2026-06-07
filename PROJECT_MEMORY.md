# RiskIntel Context Reconstruction (PROJECT MEMORY)

**Date:** 2026-06-07
**Status:** Core Handoff Artifact

---

# 1. Project Overview

- **Purpose:** A backend-focused Loan Decision Support System that provides transparent, fair loan assessments with plain-language explanations.
- **Intended users:** Loan officers/Underwriters (to reduce manual arithmetic and standardise baseline reports) and Borrowers (to receive fair, explicit evaluations rather than silent rejections).
- **Current scope:** Rule-based routing, readiness scoring for thin-file applicants, livelihood business mapping, and a risk-tier policy engine for bureau-scored applicants.
- **Explicit non-goals:** It is NOT a frontend project or UI showcase. It is NOT an autonomous lending AI. It is NOT an experimental ML playground.

---

# 2. Architecture Overview

### E1 (Eligibility Engine)
- **Purpose:** Assess probability of eligibility for bureau-scored borrowers.
- **Current status:** **DISABLED & REPLACE**. 
- **Dependencies:** `random_forest.joblib` and `eligibility_data.csv`.
- **Inputs:** Borrower profile, CIBIL score.
- **Outputs:** Probability score, Verdict.
- **Governance constraints:** Uncalibrated probabilities, trained on synthetic data. Must be rebuilt with a valid licensed dataset.
- **Future plans:** Sourcing licensed data to train a monotonic, calibrated model.

### E2 (Risk Tier Engine)
- **Purpose:** Map CIBIL scores to standard risk tiers (P1-P4).
- **Current status:** **KEEP & REBUILD (Eventually)**.
- **Dependencies:** `risk_tier_thresholds.json`.
- **Inputs:** CIBIL score.
- **Outputs:** Risk Tier (P1-P4).
- **Governance constraints:** Thresholds (P4 <= 658) carry proxy discrimination risk and require disparate-impact audits.
- **Future plans:** Formally document policy rationale and recompute thresholds post-E1 rebuild.

### E3 (Borrower Archetype Engine)
- **Purpose:** Cluster borrowers into narrative personas.
- **Current status:** **REMOVED**.
- **Dependencies:** `kmeans_model.pkl`, `borrower_archetype_definitions.json`.
- **Inputs:** 4 features (incl. Net Monthly Income).
- **Outputs:** Cluster ID, narrative label.
- **Governance constraints:** Restrictive data license (Home Credit) and fabricated labels (1-row cluster).
- **Future plans:** Replace with quartile-based bucketing or an external vendor.

### E4 (Recommendation Engine)
- **Purpose:** Synthesize outputs from E1-E6 into plain-language strengths, risk factors, and action plans.
- **Current status:** **KEEP**.
- **Dependencies:** Consumes internal outputs from other engines. No ML/Dataset dependencies.
- **Inputs:** Feature values and rule-triggers from E2, E5, E6.
- **Outputs:** `strengths`, `risk_factors`, `recommendations`, `action_plan`.
- **Governance constraints:** Deterministic. Currently rank-based, ignoring magnitude.
- **Future plans:** Interpolate specific borrower metrics into the templated strings.

### E5 (Readiness Engine)
- **Purpose:** Score thin-file (Person B) financial capacity without bureau data.
- **Current status:** **KEEP**.
- **Dependencies:** Internal deterministic rules.
- **Inputs:** Housing stability, financial health, business viability, etc.
- **Outputs:** Readiness Score (0-100) and Band.
- **Governance constraints:** Uses poverty proxies (infrastructure). Must enforce a hard policy floor override.
- **Future plans:** V2 redesign to an additive, proxy-free, cash-flow-centric model.

### E6 (Livelihood Engine)
- **Purpose:** Map free-text business types to standardized macro-categories.
- **Current status:** **KEEP**.
- **Dependencies:** Internal dictionary hash-map.
- **Inputs:** `primary_business` string.
- **Outputs:** Archetype label, Cluster ID, `is_unclassified` boolean.
- **Governance constraints:** Must explicitly flag unclassified businesses to prevent silent failure.
- **Future plans:** Quarterly review queue to add unclassified inputs to the dictionary.

---

# 3. Repository Structure

- `docs/` 
  - **Purpose:** Governance and Policy Documentation. 
  - **Current health:** Cleaned and active.
  - **Status:** Active.
- `archive/` 
  - **Purpose:** Storage for deprecated or unlicensed reference datasets.
  - **Current health:** Offline.
  - **Status:** Active (for historical reference only).
- `backend/app/`
  - **Purpose:** Application logic (FastAPI routers, orchestrator, engine logic).
  - **Current health:** Unknown (startup state unverified).
  - **Status:** Active.
- `backend/tests/`
  - **Purpose:** Health and pipeline tests.
  - **Current health:** Unknown (pass rate unverified).
  - **Status:** Active.
- `data/` (Implied/Root)
  - **Purpose:** Data storage.
  - **Current health:** Non-compliant (Data governance blocker).
  - **Status:** Deprecated/Blocked until `provenance.json` is implemented.

---

# 4. Governance Decisions

- **E1 Disabled (VERIFIED)**: E1 is a Random Forest wrapper around a CIBIL threshold and outputs uncalibrated probabilities. Rebuild required. (2026-06-06).
- **E3 Removed (VERIFIED)**: KMeans artifact built on restrictive, wrong-demographic data with fabricated labels. (2026-06-06).
- **Explicit Thin-File Routing (VERIFIED)**: No silent rerouting. Missing CIBIL scores must route to Person B explicit path. (2026-06-06).
- **No Person B ML Scoring (VERIFIED)**: Thin-file borrowers lack labels required for fair ML. Readiness score is deterministic. (2026-06-06).
- **Data Governance Block (VERIFIED)**: All modeling is paused until datasets have proven commercial licenses and `provenance.json`. (2026-06-06).

---

# 5. Technical Debt

**Critical**
- No production datasets have a proven commercial license or provenance.
- Two parallel databases exist with conflicting schemas (`backend/riskintel.db` vs `riskintel.db`).
- HTTP layer startup state is unknown (L-08 states failure at import).

**High**
- E1 lacks calibration and temporal validity.
- E5 has a fairness risk regarding first-time borrowers (penalizes based on poverty proxies like water access).
- No drift monitoring or OOD gating.

**Medium**
- E4 recommendations are rank-based and ignore magnitude (e.g., gap between components is not checked).
- No API authentication, rate limiting, or access logging.

**Low**
- E4 strings are templated and do not interpolate the applicant's specific values.

---

# 6. Current Phase

- **Current phase:** Governance Remediation
- **Current objective:** Convert audit findings into repository artifacts.
- **Blocked work:** Any ML training, model rebuilding, or V2 system deployment.
- **Allowed work:** Governance cleanup, deletion of restrictive artifacts, backend bug fixes, and test repairs.
- **Forbidden work:** Silently rerouting borrowers, bypassing the Model Risk Committee mandates.
- **Success condition:** Repository contains governance documents, model cards, license inventory, provenance framework, and cleanup execution plan.
- **Failure condition:** Attempting to rebuild E1, redesign E5, deploy production systems, or add ML functionality before governance artifacts are completed.

---

# 7. Backend Status

- **`GET /health`** | Purpose: Basic liveness check. | Input: None. | Output: JSON status. | Current health: Unknown. | Evidence: `app/main.py`. | **Audited**
- **`POST /api/assess`** | Purpose: Unified Orchestrator entry point. | Input: Unified payload. | Output: UnifiedResponse. | Current health: Unknown. | Evidence: `app/api/assess.py`. | **Audited**
- **`POST /api/assess/person-a`** | Purpose: Specific Person A routing. | Input: Person A payload. | Output: PersonAResponse. | Current health: Unknown. | Evidence: `app/api/assess.py`. | **Audited**
- **`POST /api/assess/person-b`** | Purpose: Specific Person B routing. | Input: Person B payload. | Output: PersonBResponse. | Current health: Unknown. | Evidence: `app/api/assess.py`. | **Audited**
- **`POST /api/generate`** | Purpose: Generate PDF reports. | Input: Report Request. | Output: Report ID. | Current health: Unknown. | Evidence: `app/api/reports.py`. | **Audited**
- **`GET /api/download/{report_id}`** | Purpose: Fetch PDF file. | Input: Path param. | Output: PDF Blob. | Current health: Unknown. | Evidence: `app/api/reports.py`. | **Audited**

---

# 8. Dataset Registry

- `eligibility_data.csv` | Status: **Delete/Replace** | Reason: Synthetic | License: Unlicensed
- `loan_approval_dataset.csv` | Status: **Delete/Replace** | Reason: Synthetic | License: Unlicensed
- `External_Cibil_Dataset.csv` | Status: **Delete** | Reason: Restrictive Kaggle (Home Credit) | License: Restrictive
- `BOB.csv`, `IDBI.csv`, `PNB1.csv`, `Syndicate.csv` | Status: **Delete** | Reason: Severe PII Exposure | License: Unlicensed
- `risk_tier_thresholds.json` | Status: **Keep** | Reason: Policy Engine (E2) | License: Internal IP
- `borrower_archetype_definitions.json` | Status: **Delete** | Reason: Fabricated E3 Labels | License: Unlicensed
- `RuralCreditData.csv`, `readiness_data.csv`, `livelihood_data.csv` | Status: **Archive** | Reason: Rule Authorship Reference | License: Unknown

---

# 9. Model Registry

- `random_forest.joblib` | Purpose: E1. | Status: **Replace** | Reason: Built on synthetic data, mathematically uncalibrated.
- `kmeans_model.pkl` | Purpose: E3. | Status: **Delete** | Reason: Restrictive data, 1-row cluster.
- `scaler.pkl` | Purpose: E3. | Status: **Delete** | Reason: Dependency for deleted E3.

---

# 10. Future AI Instructions

- **What must never be reopened:** The removal of E3, the disabling of E1 without licensed data, and the strict routing policy for thin-file borrowers (no ML probabilities for Person B).
- **What must always be verified:** Whether a requested model modification violates the current data governance blockade.
- **Evidence required before code changes:** If touching the HTTP layer or DB layer, explicitly check the test pass rate and verify whether the runtime actually starts. Do not assume `main.py` functions natively without running it.
- **Tracking confidence levels:** Explicitly mark claims as VERIFIED (proven by repo files), AUDITED (stated in documentation but not executed by you), or ASSUMED (guessed without proof). Do not execute ASSUMED changes.

---

# 11. Open Questions

- **What is the current `pytest` pass rate?** The state of `backend/tests/` is unknown and requires a terminal run.
- **Does `uvicorn app.main:app` successfully boot?** Documentation states it fails at import due to dead code, but the code exists. Requires terminal execution.
- **What is the current Alembic migration state?** The dual-database issue (`backend/riskintel.db` vs root) means the location of the live audit log is unverified at runtime. Requires running `alembic current`.
