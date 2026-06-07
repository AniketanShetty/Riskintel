# RiskIntel — Data Governance Plan

**Date:** 2026-06-07
**Status:** Enforceable Production Plan

## 1. Full Dataset Inventory

| Dataset | Type | Engine | Description |
|---|---|---|---|
| `eligibility_data.csv` | Processed | E1 | Synthetic-rule-like data for eligibility |
| `loan_approval_dataset.csv` | Raw | E1 | Source for eligibility |
| `risk_tier_thresholds.json` | Processed | E2 | Hard-coded policy thresholds |
| `borrower_archetype_definitions.json` | Processed | E3 | KMeans cluster labels (Fabricated) |
| `kmeans_model.pkl` | Model Artifact| E3 | KMeans clustering model |
| `scaler.pkl` | Model Artifact| E3 | Feature scaler for E3 |
| `External_Cibil_Dataset.csv` | Raw | E2, E3 | Czech/Russia/Kazakhstan/China population |
| `Internal_Bank_Dataset.csv` | Raw | None | Orphan / Companion to External |
| `RuralCreditData.csv` | Raw | E5, E6 | India-specific reference data |
| `readiness_data.csv` | Processed | None | E5 reference |
| `livelihood_data.csv` | Processed | None | E6 reference |
| `Unseen_Dataset.csv` | Raw | None | Orphan |
| `BOB.csv`, `IDBI.csv`, `PNB1.csv`, `Syndicate.csv` (+ `_df` variants) | Raw | None | Orphan Indian bank suits-filed CSVs with PII |
| `states.csv`, `states_df.csv` | Raw | None | Orphan |
| `test_modified.csv`, `train_modified.csv` | Raw | None | Orphan (Kaggle) |
| `myFunction.py` | Utility | None | Orphan utility script |
| `random_forest.joblib` | Model Artifact| E1 | RandomForest model |

## 2. Dataset Status & Priority

| Dataset | Source | License | Legal Status | Prod. Use | Provenance | Priority |
|---|---|---|---|---|---|---|
| `eligibility_data.csv` | Unknown | Unknown | Unlicensed | YES (E1) | MISSING | **P0 Replace** |
| `External_Cibil_Dataset.csv` | Home Credit | Restrictive | Unauthorized | YES (E2/E3)| MISSING | **P0 Replace/License** |
| `RuralCreditData.csv` | Unknown | Unknown | Unlicensed | Indirect | MISSING | P1 Document |
| `risk_tier_thresholds.json`| Hand-authored| N/A | Reviewable | YES (E2) | N/A | P1 Document |
| `borrower_archetype_definitions.json` | Hand-authored| N/A | Reviewable | YES (E3) | N/A | **P0 Remove** |
| Orphan Bank CSVs | RBI Defaulters? | Unknown | PII exposure| NO | MISSING | **P0 Delete** |
| Other Orphans | Unknown | Unknown | Unlicensed | NO | MISSING | P2 Archive/Delete |

## 3. Classification

| Dataset | Classification | Reason |
|---|---|---|
| **Zero Datasets** | **SAFE** | No production dataset currently has a valid commercial license and complete provenance. |
| `RuralCreditData.csv` | **QUESTIONABLE** | Can remain as reference material if provenance and license are established. Not loaded at runtime. |
| `risk_tier_thresholds.json` | **QUESTIONABLE** | Can be kept, but thresholds must be justified as policy. |
| `External_Cibil_Dataset.csv` | **QUESTIONABLE** | Can only be used if a commercial license from Home Credit is negotiated. |
| `eligibility_data.csv` | **UNUSABLE** | Synthetic-rule-like labels cannot be used for predictive modeling. |
| `borrower_archetype_definitions.json` | **UNUSABLE** | 1-row cluster and fabricated labels based on wrong population. |
| Orphan Bank CSVs | **UNUSABLE** | Unjustified processing of PII. |
| All other orphans | **UNUSABLE** | No production use; restrictive or unknown licenses. |

## 4. Required Governance Artifacts

Before any further modeling or deployment, the following artifacts must be created:
- **`provenance.json`**: Required for every raw and processed dataset. Must detail source URL, license, population, rows, columns, SHA256, and build script.
- **`data/lineage.json`**: A master file documenting the full dependency graph (`raw → processed → model → engine`).
- **License Review Log**: A central, living document (e.g., `LICENSE_INVENTORY.md`) tracking the legal status of all datasets.
- **Model Cards**: `MODEL_CARD_{engine}.md` for each engine, defining intent, limitations, and policy weights/thresholds.
- **Schema Versioning**: Header comments in every processed CSV detailing the schema version and build script hash.
- **`data/raw/README.md`**: A registry of all raw files detailing their geographic population, intended use, and production status.

## 5. Concrete Replacement Strategy

- **What must be replaced first (P0):** `eligibility_data.csv`. A real-outcome, commercially licensed dataset must be sourced to rebuild E1. 
- **What must be removed first (P0):** E3 (`kmeans_model.pkl` and `borrower_archetype_definitions.json`). Must be disabled from production responses immediately.
- **What must be deleted (P0):** All orphan bank CSVs containing PII (`BOB.csv`, `IDBI.csv`, etc.).
- **What can remain as reference only (P1):** `RuralCreditData.csv`. Kept strictly to inform E5/E6 rule design. Must establish provenance.

## 6. Production Readiness Gates

**What must exist before any E1 rebuild:**
1. A new, real-outcome dataset with a valid commercial license.
2. Complete `provenance.json` for the new dataset.
3. Explicit sign-off in the License Review Log.

**What must exist before any deployment claim:**
1. E1 model is disabled or fully replaced.
2. E3 is removed from the production response.
3. Every production dataset has an accompanying `provenance.json`.
4. A complete `data/lineage.json` exists.
5. All PII-bearing orphan files are deleted.
6. A CI gate enforces that no unprovenanced data can enter the build pipeline.
