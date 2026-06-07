# RiskIntel License Inventory

**Date:** 2026-06-07
**Status:** Canonical Tracker for Dataset Licensing

**OVERALL REPOSITORY STATUS: NON-COMPLIANT**
Zero production datasets currently possess a verified commercial use license. 

## 1. Production Datasets (Currently Blocking)

| Dataset File | Used By | License Status | Reason | Action Required |
|---|---|---|---|---|
| `eligibility_data.csv` | E1 | Unlicensed (Synthetic) | Unknown source, untraceable. | **REPLACE**. Must procure a commercially licensed credit dataset. |
| `loan_approval_dataset.csv` | E1 | Unlicensed (Synthetic) | Upstream raw for eligibility. | **REPLACE**. Delete and replace with licensed raw data. |
| `External_Cibil_Dataset.csv` | E2, E3 | Restrictive (Kaggle) | Academic/Research only. Prohibits commercial use. | **REMOVE**. Must negotiate a commercial license from Home Credit or delete entirely. |
| `risk_tier_thresholds.json` | E2 | Internal Policy | Internally authored. | **VERIFY**. Requires formal sign-off by legal/risk team as institutional IP. |

## 2. Deprecated / Removed Datasets (To Be Deleted)

| Dataset File | Reason for Deletion |
|---|---|
| `kmeans_model.pkl` | E3 is permanently removed from the system. |
| `scaler.pkl` | E3 dependency. |
| `borrower_archetype_definitions.json` | E3 dependency. Fabricated labels. |
| `BOB.csv`, `IDBI.csv`, `PNB1.csv`, `Syndicate.csv` | Severe PII exposure. Indian bank suits-filed lists. |
| `Internal_Bank_Dataset.csv` | Unused orphan. |
| `train_modified.csv`, `test_modified.csv` | Kaggle leftovers. |
| `states.csv`, `Unseen_Dataset.csv` | Unused orphans. |

## 3. Reference Datasets (To Be Archived)

These datasets are not loaded at runtime but were used to author rules. They cannot be used for predictive modeling without explicit licenses.

| Dataset File | Used For | Planned Status |
|---|---|---|
| `RuralCreditData.csv` | E5/E6 rule reference | Move to `/archive` |
| `readiness_data.csv` | E5 reference | Move to `/archive` |
| `livelihood_data.csv` | E6 reference | Move to `/archive` |

## 4. Policy for Future Datasets

Before any dataset can be placed in `data/raw/` or `data/processed/`, a legal review must take place, and an entry must be added to this document with a link to the explicit license terms.
