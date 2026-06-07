# RiskIntel Cleanup Execution Plan

**Date:** 2026-06-07
**Objective:** Purge the repository of all illegal, unlicensed, PII-bearing, and broken artifacts to establish a clean state before addressing API or backend fixes.

## Step 1: Purge PII and Bank CSVs
Delete the following orphan files that carry severe legal and PII exposure risk:
- [ ] `BOB.csv`
- [ ] `IDBI.csv`
- [ ] `PNB1.csv`
- [ ] `Syndicate.csv`
- [ ] Any `_df.csv` variants of the above.
- [ ] `Internal_Bank_Dataset.csv`

## Step 2: Purge E3 Artifacts
E3 has been permanently removed by the Model Risk Committee. Delete its artifacts:
- [ ] `kmeans_model.pkl`
- [ ] `scaler.pkl`
- [ ] `borrower_archetype_definitions.json`

## Step 3: Purge Restrictive and Unused Data
Delete datasets that prohibit commercial use or serve no purpose:
- [ ] `External_Cibil_Dataset.csv` (Kaggle Home Credit)
- [ ] `train_modified.csv`
- [ ] `test_modified.csv`
- [ ] `Unseen_Dataset.csv`
- [ ] `states.csv` and `states_df.csv`
- [ ] `myFunction.py` (orphan utility)

## Step 4: Archive Reference Data
Move data used solely for rule authorship into an archive folder so it cannot accidentally be loaded into a predictive pipeline:
- [ ] Create `archive/` directory at the project root.
- [ ] Move `RuralCreditData.csv` to `archive/`
- [ ] Move `readiness_data.csv` to `archive/`
- [ ] Move `livelihood_data.csv` to `archive/`

## Step 5: Isolate E1 Data
E1 is disabled. Its data must be deleted to prepare for a clean rebuild:
- [ ] Delete `eligibility_data.csv`
- [ ] *Note: `random_forest.joblib` and `loan_approval_dataset.csv` must also be tracked for deletion or complete replacement once a legally defensible dataset is procured.*

## Step 6: Verification
Run a final scan. The only configuration file remaining should be `risk_tier_thresholds.json`. No `.csv` or `.pkl` files should exist in the root or `backend/` directory unless they strictly adhere to the new `PROVENANCE_FRAMEWORK.md`.
