# RiskIntel Task — Dataset Decision Registry

## Constitution Check
RiskIntel exists to:
1. Give borrowers transparent and fair assessments.
2. Give loan officers structured reports that reduce manual work.

---

## Current Audited Reality
The audits found:
* Zero production datasets have complete provenance.
* Zero production datasets have verified commercial licensing.
* E1 training data is synthetic-rule-like.
* E3 training data is wrong-population and license restricted.
* Multiple orphan datasets exist.
* Multiple files contain PII.
* Data governance is currently the primary blocker.

---

## Dataset Decision Registry

### Raw Datasets

#### File Name: `loan_approval_dataset.csv`
- **Current Purpose:** Source data for training the E1 Eligibility model.
- **Used By:** E1 Eligibility Engine (Training).
- **License Status:** Unknown / Unverified.
- **Provenance Status:** Missing.
- **Risks:** Synthetic-rule-like data, uncalibrated, unlicensed.
- **Decision:** **REPLACE**
- **Justification:** The concept of eligibility assessment is needed, but the current source is not acceptable or legally defensible.
- **Required Action:** Source a commercially licensed, real-world credit dataset to rebuild E1.

#### File Name: `External_Cibil_Dataset.csv`
- **Current Purpose:** Source data for E3 (Archetype).
- **Used By:** E3 Borrower Archetype Engine.
- **License Status:** Restrictive (Kaggle Home Credit).
- **Provenance Status:** Missing formal JSON, but known to be non-Indian population.
- **Risks:** Wrong geographic population, restrictive license prohibiting commercial use.
- **Decision:** **REMOVE**
- **Justification:** E3 is being removed from production. The dataset should never exist in a commercial production environment.
- **Required Action:** Delete the file from the repository.

#### File Name: `RuralCreditData.csv`
- **Current Purpose:** Reference data used to design E5/E6 rules.
- **Used By:** None directly at runtime (Offline reference).
- **License Status:** Unknown.
- **Provenance Status:** Missing.
- **Risks:** Unlicensed.
- **Decision:** **ARCHIVE**
- **Justification:** Not needed for production runtime today, but useful to retain as historical reference for how the E5/E6 rules were originally authored.
- **Required Action:** Move to an `archive/` directory.

#### File Name: `Internal_Bank_Dataset.csv`
- **Current Purpose:** Companion dataset to External_Cibil.
- **Used By:** None (Orphan).
- **License Status:** Unknown.
- **Provenance Status:** Missing.
- **Risks:** Unlicensed, unused, potential PII.
- **Decision:** **REMOVE**
- **Justification:** Orphan dataset that should never exist in production.
- **Required Action:** Delete the file.

#### File Name: `BOB.csv`, `IDBI.csv`, `PNB1.csv`, `Syndicate.csv`
- **Current Purpose:** Unknown.
- **Used By:** None (Orphans).
- **License Status:** Unknown.
- **Provenance Status:** Missing.
- **Risks:** High risk of PII exposure (Indian bank suits-filed lists).
- **Decision:** **REMOVE**
- **Justification:** Extreme legal and compliance risk with zero production utility. Should never exist in the repo.
- **Required Action:** Immediately delete the files.

#### File Name: `train_modified.csv`, `test_modified.csv`
- **Current Purpose:** Kaggle competition leftovers.
- **Used By:** None (Orphans).
- **License Status:** Unknown / Restrictive.
- **Provenance Status:** Missing.
- **Risks:** Clutter, licensing risk.
- **Decision:** **REMOVE**
- **Justification:** Leftover development artifacts with no place in production.
- **Required Action:** Delete the files.

#### File Name: `Unseen_Dataset.csv`
- **Current Purpose:** Unknown testing data.
- **Used By:** None (Orphan).
- **License Status:** Unknown.
- **Provenance Status:** Missing.
- **Risks:** Unlicensed.
- **Decision:** **REMOVE**
- **Justification:** Unused and legally indefensible.
- **Required Action:** Delete the file.

#### File Name: `states.csv`, `states_df.csv`
- **Current Purpose:** Unknown lookup tables.
- **Used By:** None (Orphans).
- **License Status:** Unknown.
- **Provenance Status:** Missing.
- **Risks:** Clutter.
- **Decision:** **REMOVE**
- **Justification:** Unused artifacts.
- **Required Action:** Delete the files.

---

### Processed Datasets

#### File Name: `eligibility_data.csv`
- **Current Purpose:** Processed data used to train the E1 RandomForest.
- **Used By:** E1 Training script.
- **License Status:** Unknown.
- **Provenance Status:** Missing.
- **Risks:** Contains the same synthetic artifacts as the raw dataset.
- **Decision:** **REPLACE**
- **Justification:** The concept is needed to rebuild E1, but this file is unusable.
- **Required Action:** Delete and generate a new processed file once replacement raw data is sourced.

#### File Name: `readiness_data.csv`
- **Current Purpose:** Processed reference data for E5.
- **Used By:** None directly at runtime.
- **License Status:** Unknown.
- **Provenance Status:** Missing.
- **Risks:** Unlicensed derivative.
- **Decision:** **ARCHIVE**
- **Justification:** Retain for historical reference only. Not needed for production.
- **Required Action:** Move to an `archive/` directory.

#### File Name: `livelihood_data.csv`
- **Current Purpose:** Processed reference data for E6.
- **Used By:** None directly at runtime.
- **License Status:** Unknown.
- **Provenance Status:** Missing.
- **Risks:** Unlicensed derivative.
- **Decision:** **ARCHIVE**
- **Justification:** Retain for historical reference only. Not needed for production.
- **Required Action:** Move to an `archive/` directory.

---

### Model Artifacts

#### File Name: `random_forest.joblib`
- **Current Purpose:** Trained E1 eligibility model.
- **Used By:** E1 Eligibility Engine runtime.
- **License Status:** N/A (Trained artifact).
- **Provenance Status:** Missing (Lineage to data is broken).
- **Risks:** Uncalibrated, mathematically invalid probabilities.
- **Decision:** **REPLACE**
- **Justification:** The model is broken and built on synthetic data, but an eligibility concept is needed in the future.
- **Required Action:** Keep E1 disabled. Train a new artifact once licensed data is procured.

#### File Name: `kmeans_model.pkl`
- **Current Purpose:** Trained E3 clustering model.
- **Used By:** E3 Borrower Archetype Engine.
- **License Status:** N/A (Trained artifact from restrictive data).
- **Provenance Status:** Missing.
- **Risks:** Fabricated clusters (1-row cluster), wrong geographic population.
- **Decision:** **REMOVE**
- **Justification:** E3 is being completely removed. The artifact should never exist in production.
- **Required Action:** Delete the file.

#### File Name: `scaler.pkl`
- **Current Purpose:** Feature scaler for E3.
- **Used By:** E3 Borrower Archetype Engine.
- **License Status:** N/A.
- **Provenance Status:** Missing.
- **Risks:** Supports a broken engine.
- **Decision:** **REMOVE**
- **Justification:** E3 is removed.
- **Required Action:** Delete the file.

---

### Configuration / Definitions

#### File Name: `risk_tier_thresholds.json`
- **Current Purpose:** Hardcoded thresholds for assigning P1-P4 risk tiers.
- **Used By:** E2 Risk Tier Engine.
- **License Status:** Internal Bank IP.
- **Provenance Status:** Explicitly authored policy.
- **Risks:** Thresholds lack documented empirical justification.
- **Decision:** **KEEP**
- **Justification:** Still needed, legally defensible as internal policy, and operationally useful.
- **Required Action:** Document the rationale for the thresholds in a Model/Policy Card.

#### File Name: `borrower_archetype_definitions.json`
- **Current Purpose:** Cluster labels mapping to the KMeans model.
- **Used By:** E3 Borrower Archetype Engine.
- **License Status:** Internal text based on restrictive data.
- **Provenance Status:** Fabricated labels.
- **Risks:** Highly misleading text describing foreign populations.
- **Decision:** **REMOVE**
- **Justification:** E3 is being completely removed.
- **Required Action:** Delete the file.

---

### Utility Files

#### File Name: `myFunction.py`
- **Current Purpose:** Legacy/Orphan script.
- **Used By:** None.
- **License Status:** Unknown.
- **Provenance Status:** Missing.
- **Risks:** Clutter.
- **Decision:** **REMOVE**
- **Justification:** Should never exist in a production repository.
- **Required Action:** Delete the file.

---

## 1. Dataset Inventory Summary

- **KEEP:** 1
- **REPLACE:** 3
- **REMOVE:** 12
- **ARCHIVE:** 3

## 2. Production-Critical Files
Only the following file is required for Minimum Viable RiskIntel data operations:
- `risk_tier_thresholds.json` (as policy configuration)
*(Note: E5 and E6 operate using internal, hardcoded dictionaries/logic and do not require external file loading at runtime).*

## 3. Immediate Cleanup Actions
1. Delete `External_Cibil_Dataset.csv` to remove restrictive license risk.
2. Delete `BOB.csv`, `IDBI.csv`, `PNB1.csv`, `Syndicate.csv` to eliminate severe PII exposure risk.
3. Delete `Internal_Bank_Dataset.csv`.
4. Delete `kmeans_model.pkl` and `scaler.pkl`.
5. Delete `borrower_archetype_definitions.json`.
6. Delete `train_modified.csv`, `test_modified.csv`, `Unseen_Dataset.csv`, and `states*.csv`.
7. Delete `myFunction.py`.
8. Move `RuralCreditData.csv`, `readiness_data.csv`, and `livelihood_data.csv` to an `archive/` folder.
9. Delete `eligibility_data.csv` to prepare for a clean slate rebuild.
10. Ensure `random_forest.joblib` is isolated and not loaded by the orchestrator.

## 4. Final Verdict

**Can the repository proceed to E1 rebuilding?**

**NO.**

**Justification:** The repository currently has zero production datasets with a verified commercial license and complete provenance. Before any E1 rebuilding can begin, the organization must legally procure a real-outcome dataset, verify its commercial use license, and generate a complete `provenance.json` artifact. Proceeding to modeling before the data governance foundation is laid is a direct violation of the Model Risk Committee's mandates.
