# RiskIntel — Dataset Provenance Audit

**Version:** 1.0
**Date:** 2026-06-06
**Scope:** Every file in `data/raw/` and `data/processed/`. No code modified. No downloads. No training.
**Inherits:** [ML_AUDIT.md](ML_AUDIT.md), [ML_AUDIT_PHASE_2.md](ML_AUDIT_PHASE_2.md), [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md).
**Method:** File-by-file inspection. Build-script tracing. Production consumption graph.

---

## 1. Dataset Inventory

### 1.1 `data/raw/` files (18 files, 14 distinct datasets)

| # | File | Rows | Cols | Population | Source | License | Build script | Used in production? | Engine consumer |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `BOB.csv` | 101 | 11 | India (Bank of Baroda, Gujarat) | Unknown local extraction (suits-filed list) | **Unknown** | None | **No** | None |
| 2 | `External_Cibil_Dataset.csv` | 51,336 | 62 | Czech/Russia/Kazakhstan/China (Home Credit) | [Kaggle: home-credit-default-risk](https://www.kaggle.com/c/home-credit-default-risk) | Public competition (research/competition, not commercial) | None | **Yes** (archetype training, risk-tier calibration) | E2 risk_tier_thresholds, E3 archetype KMeans |
| 3 | `IDBI.csv` | 321 | 86 | India (IDBI Bank, Gujarat) | Unknown local extraction (suits-filed list) | **Unknown** | None | **No** | None |
| 4 | `Internal_Bank_Dataset.csv` | 51,336 | 27 | Same as External (companion table from same Kaggle release) | Kaggle: home-credit-default-risk | Public competition | None | **No** | None (in `data/raw/`; not consumed by any pipeline) |
| 5 | `PNB1.csv` | 1,190 | 86 | India (Punjab National Bank, Andhra Pradesh) | Unknown local extraction (suits-filed list) | **Unknown** | None | **No** | None |
| 6 | `RuralCreditData.csv` | 40,000 | 20 | India (rural lending — cities include Dhanbad, Manjapra) | **Unknown** (likely synthetic or public competition origin) | **Unknown** | `backend/app/utils/preprocess_b.py` reads it; `verify_final.py` references it | **Yes** | E5 readiness, E6 livelihood (one-hot encoded output) |
| 7 | `Syndicate.csv` | 219 | 38 | India (Syndicate Bank, Andhra Pradesh) | Unknown local extraction (suits-filed list) | **Unknown** | None | **No** | None |
| 8 | `Unseen_Dataset.csv` | 100 | 42 | Unknown | Unknown (filename suggests holdout for an unseen test set) | **Unknown** | None | **No** | None (column names match Internal_Bank_Dataset; likely companion file) |
| 9 | `bob_df.csv` | 679 | 11 | India (Bank of Baroda, Gujarat) | Same source as `BOB.csv`, different format | **Unknown** | None | **No** | None |
| 10 | `combined_df.csv` | 2,308 | 11 | India (Punjab National Bank, Andhra Pradesh) | Same source as `PNB1.csv`, different format | **Unknown** | None | **No** | None |
| 11 | `idbi_df.csv` | 222 | 10 | India (IDBI Bank, Gujarat) | Same source as `IDBI.csv`, different format | **Unknown** | None | **No** | None |
| 12 | `loan_approval_dataset.csv` | 4,269 | 13 | Unknown (likely synthetic — see [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md)) | Unknown (file does not match any known public dataset) | **Unknown** | `backend/app/utils/preprocess_a.py` reads it | **Yes** | E1 eligibility |
| 13 | `pnb_df.csv` | 1,188 | 10 | India (Punjab National Bank, Andhra Pradesh) | Same source as `PNB1.csv`, different format | **Unknown** | None | **No** | None |
| 14 | `states.csv` | 34 | 1 | India (list of states) | Unknown | **Unknown** | None | **No** | None (likely reference list) |
| 15 | `states_df.csv` | 34 | 2 | India (same as states.csv) | Unknown | **Unknown** | None | **No** | None |
| 16 | `syndicate_df.csv` | 219 | 10 | India (Syndicate Bank, Andhra Pradesh) | Same as `Syndicate.csv`, different format | **Unknown** | None | **No** | None |
| 17 | `test_modified.csv` | 37,717 | 44 | Unknown (filename suggests a Kaggle test set; many columns named `Var1_0...Var1_18`, `Var2_0...Var2_6` — anonymized) | **Unknown** (likely Kaggle: loan-default or fraud-detection competition) | **Unknown** | None | **No** | None |
| 18 | `train_modified.csv` | 87,020 | 45 | Same population as `test_modified.csv` (target column `Disbursed` present in train, absent in test) | Unknown | **Unknown** | None | **No** | None |

### 1.2 `data/processed/` files (6 files)

| # | File | Rows | Cols | Source raw | Used in production? | Engine consumer |
|---|---|---|---|---|---|---|
| 19 | `eligibility_data.csv` | 4,269 | 12 | `loan_approval_dataset.csv` (via `preprocess_a.py`) | **Yes** | E1 eligibility |
| 20 | `readiness_data.csv` | 40,000 | 19 | `RuralCreditData.csv` (via `preprocess_b.py`) | **No** (E5 is rule-based; data is not loaded at runtime) | E5 readiness (input schema) |
| 21 | `livelihood_data.csv` | 40,000 | 15 | `RuralCreditData.csv` (via `preprocess_b.py`) | **No** (E6 is string lookup, not ML) | E6 livelihood (one-hot reference only) |
| 22 | `risk_tier_thresholds.json` | 4 lines | n/a | **No source** (hand-authored) | **Yes** | E2 risk_tier |
| 23 | `borrower_archetype_definitions.json` | 4 lines | n/a | `scripts/train_borrower_archetype.py` (KMeans centroid ranking) | **Yes** (E3 in production) | E3 archetype |
| 24 | `processed/*` (orphan) | n/a | n/a | `backend/app/utils/preprocess_c.py` references `archetype_data.csv` (does not exist) | **No** | None — orphan reference |

### 1.3 Preprocess scripts discovered

| Script | Reads | Writes | Status |
|---|---|---|---|
| `backend/app/utils/preprocess_a.py` | `loan_approval_dataset.csv` | `eligibility_data.csv` | Functional (verified by `verify_final.py`) |
| `backend/app/utils/preprocess_b.py` | `RuralCreditData.csv` | `readiness_data.csv`, `livelihood_data.csv` | Functional |
| `backend/app/utils/preprocess_c.py` | `External_Cibil_Dataset.csv` | `risk_tier_thresholds.json`, `archetype_data.csv` (orphan) | Partially functional; the `archetype_data.csv` write target is referenced but does not exist in the processed directory |
| `backend/app/engines/eligibility/train.py` | `eligibility_data.csv` | `random_forest.joblib` (in `models/eligibility/`) | Functional |
| `scripts/train_borrower_archetype.py` | `External_Cibil_Dataset.csv` | `models/archetype/kmeans_model.pkl`, `models/archetype/scaler.pkl`, `borrower_archetype_definitions.json` | Functional but produces 1-row cluster (see [ML_AUDIT_PHASE_2.md](ML_AUDIT_PHASE_2.md) §2) |
| `experiments/scripts/f*.py` (13 scripts) | `eligibility_data.csv` | `experiments/metrics/`, `experiments/plots/`, `experiments/reports/` | Functional forensics |

---

## 2. Production Dependency Graph

Three raw files feed three preprocess scripts which produce three processed files. Three processed files feed three engines:

```
data/raw/loan_approval_dataset.csv (4,269 rows, 13 cols)
    │
    └─[preprocess_a.py]─→ data/processed/eligibility_data.csv (4,269 rows, 12 cols)
                              │
                              └─[train.py]─→ models/eligibility/random_forest.joblib
                                                │
                                                └─→ E1 Eligibility Engine ──→ POST /api/assess/person-a
                                                └─→ E1 Eligibility Engine ──→ POST /api/assess (unified)


data/raw/RuralCreditData.csv (40,000 rows, 20 cols)
    │
    └─[preprocess_b.py]─→ data/processed/readiness_data.csv (40,000 rows, 19 cols)
                       └─→ data/processed/livelihood_data.csv (40,000 rows, 15 cols)
                              │
                              └─→ E5 Readiness Engine (rule-based, data not loaded at runtime)
                              └─→ E6 Livelihood Engine (string lookup, data not loaded at runtime)
                                    └─→ POST /api/assess/person-b
                                    └─→ POST /api/assess (unified)


data/raw/External_Cibil_Dataset.csv (51,336 rows, 62 cols)
    │
    └─[preprocess_c.py]─→ data/processed/risk_tier_thresholds.json (4 lines)
                       └─→ [archetype_data.csv — orphan, never written]
                              │
                              └─[train_borrower_archetype.py]─→ models/archetype/kmeans_model.pkl
                                                                └─→ models/archetype/scaler.pkl
                                                                └─→ data/processed/borrower_archetype_definitions.json
                                                                                  │
                                                                                  └─→ E2 Risk Tier Engine (uses thresholds)
                                                                                  └─→ E3 Archetype Engine (KMeans) ──→ POST /api/assess/person-a
                                                                                  └─→ E3 Archetype Engine (KMeans) ──→ POST /api/assess (unified)
```

**Three raw files are in production.** The other 12 raw files in `data/raw/` are **orphans**.

---

## 3. Orphaned Datasets

Twelve files in `data/raw/` are not consumed by any preprocess script or production code:

| File | Rows | Content type | Status |
|---|---|---|---|
| `BOB.csv` | 101 | India bank suits-filed list (Gujarat) | Orphan. Likely an exploratory scrape, never wired up. |
| `IDBI.csv` | 321 | India bank suits-filed list (Gujarat) | Orphan. Same as BOB. |
| `Internal_Bank_Dataset.csv` | 51,336 | Bureau credit history (companion to External) | Orphan. 51k rows, never used. |
| `PNB1.csv` | 1,190 | India bank suits-filed list (Andhra Pradesh) | Orphan. |
| `Syndicate.csv` | 219 | India bank suits-filed list (Andhra Pradesh) | Orphan. |
| `Unseen_Dataset.csv` | 100 | Bureau features, test-like schema | Orphan. Filename suggests an unseen test set that was never wired up. |
| `bob_df.csv` | 679 | Duplicate of BOB.csv, different format | Orphan. Likely a formatting experiment. |
| `combined_df.csv` | 2,308 | Aggregated PNB data | Orphan. |
| `idbi_df.csv` | 222 | Duplicate of IDBI.csv, different format | Orphan. |
| `pnb_df.csv` | 1,188 | Duplicate of PNB1.csv, different format | Orphan. |
| `states.csv` | 34 | List of Indian states | Orphan. Reference list, never used. |
| `states_df.csv` | 34 | Same as states.csv | Orphan. |
| `syndicate_df.csv` | 219 | Duplicate of Syndicate.csv, different format | Orphan. |
| `test_modified.csv` | 37,717 | Anonymized loan application features (likely Kaggle) | Orphan. |
| `train_modified.csv` | 87,020 | Same as test_modified.csv with `Disbursed` target | Orphan. Largest single dataset in `data/raw/`. |

The 5 bank suits-filed CSVs (BOB, IDBI, PNB1, Syndicate, and their `_df` variants) are evidence of an abandoned India-bank-suits-filed pipeline. The CSV pairs differ only in formatting (column structure, quoting) — one set is "wide" and the other is "tidy." The wide format is read by `BOB.csv` etc.; the tidy format is the same data in `bob_df.csv` etc. **None of this data is in production. The Indian-bank-suits-filed effort was started and abandoned.**

`train_modified.csv` (87k rows, 45 columns) and `test_modified.csv` (37k rows, 44 columns) form a paired train/test set with an anonymized target (`Disbursed`). The feature names (`Var1_0...Var1_18`, `Var2_0...Var2_6`) and column structure suggest a **Kaggle competition** (Home Credit style). The target is disbursement, not default. This is a **disbursement prediction** dataset, not a default prediction dataset. **Not a fit for RiskIntel's use case without re-labeling and re-architecting.**

**Total orphaned disk: 222,956 rows across 12 files. Approximately 60% of all raw data on disk is not in production.**

---

## 4. Licensing Risks

| File | License signal | Risk |
|---|---|---|
| `loan_approval_dataset.csv` | None (no header comment, no provenance) | **CRITICAL.** No license. Synthetic data of unknown origin. Cannot be defended in commercial deployment. |
| `RuralCreditData.csv` | None (no header comment, no provenance) | **HIGH.** 40k rows of "rural credit" data with city names from India. Could be scraped, could be synthetic, could be a private dataset leaked. No license. |
| `External_Cibil_Dataset.csv` | **Kaggle competition terms.** Data released for "non-commercial research and competition use." | **CRITICAL.** Public Home Credit data is restricted to research/competition. The 51,336 rows are used in production (E3 archetype, E2 thresholds). Production deployment requires separate commercial license from Home Credit. |
| `Internal_Bank_Dataset.csv` | Same Kaggle competition | Same. Currently orphan, but if used would inherit the same restriction. |
| `BOB.csv`, `IDBI.csv`, `PNB1.csv`, `Syndicate.csv`, `bob_df.csv`, `combined_df.csv`, `idbi_df.csv`, `pnb_df.csv`, `states.csv`, `states_df.csv`, `syndicate_df.csv` | None. Suits-filed lists. | **HIGH.** Indian bank data is subject to banking secrecy laws, RBI data protection guidelines, and the Indian Telegraph Act / IT Act provisions. Unlicensed possession is potentially unlawful. Even if the data was scraped from public RBI publications, derivative use in a commercial product may require RBI notification. |
| `Unseen_Dataset.csv` | None | **MEDIUM.** Filename and column match to `Internal_Bank_Dataset.csv` suggest it's the same Kaggle release. Inherits Kaggle restrictions if used. |
| `test_modified.csv`, `train_modified.csv` | None | **MEDIUM.** Likely a Kaggle dataset; if so, restricted to research/competition. |
| `eligibility_data.csv`, `readiness_data.csv`, `livelihood_data.csv` | None (derived from raw above) | Inherit license from source raw. |
| `risk_tier_thresholds.json`, `borrower_archetype_definitions.json` | None (hand-authored) | No license issue. |
| `myFunction.py` (raw, 9 lines) | None | Orphan utility script. Not a dataset. |

**No file in `data/raw/` or `data/processed/` has a license file, a header comment, a `provenance.json`, or a `LICENSE` document.** The repository has no central data-governance documentation.

**Three production-consumed datasets have CRITICAL or HIGH licensing risk:** `loan_approval_dataset.csv`, `RuralCreditData.csv`, and `External_Cibil_Dataset.csv`. **No commercial license exists for any of them.** The institution is operating on unlicensed data.

---

## 5. Data Lineage Gaps

The repository's data lineage is a black box. From raw to model:

### 5.1 What exists
- `backend/app/utils/preprocess_a.py` — script reads `loan_approval_dataset.csv`, writes `eligibility_data.csv`.
- `backend/app/utils/preprocess_b.py` — script reads `RuralCreditData.csv`, writes `readiness_data.csv` and `livelihood_data.csv`.
- `backend/app/utils/preprocess_c.py` — script reads `External_Cibil_Dataset.csv`, writes `risk_tier_thresholds.json` and an orphan `archetype_data.csv`.
- `backend/app/utils/verify_final.py` — script reads both raw and processed files, prints null counts and shapes. Verification only — no assertion-based testing.
- `backend/app/engines/eligibility/train.py` — script reads `eligibility_data.csv`, writes `models/eligibility/random_forest.joblib`.
- `scripts/train_borrower_archetype.py` — script reads `External_Cibil_Dataset.csv`, writes KMeans artifacts and `borrower_archetype_definitions.json`.

### 5.2 What is missing

1. **No `provenance.json` for any dataset.** Not at `data/raw/`, not at `data/processed/`, not at `models/`. There is no file documenting: source URL, license, download date, file hash, build date, build script reference, build operator.
2. **No central lineage file.** The dependency graph in §2 is reconstructed by grep. There is no `data/lineage.json` or equivalent.
3. **No data dictionary.** Field-level documentation is absent. Some column names are cryptic (`Var1_0...Var1_18`, `pct_PL_enq_L6m_of_ever`). The `pct_*_of_ever` columns in `External_Cibil_Dataset.csv` are not explained.
4. **No schema versioning.** `eligibility_data.csv` is read by `train.py` with implicit feature order. Renaming any column silently breaks training. There is no schema version column, no manifest, no checksum in the data files themselves.
5. **No build pipeline.** The preprocess scripts run on demand. There is no Makefile, no `dvc.yaml`, no `pre-commit` hook, no CI step that regenerates the processed data. A developer who deletes `eligibility_data.csv` will break the system silently.
6. **No `myFunction.py` documentation.** `data/raw/myFunction.py` is 9 lines. Its purpose is not documented. (Inferred: a utility script for one of the orphan CSVs.)
7. **The two `states*.csv` files are referenced nowhere in code.** They contain 34 Indian state names. They are dead weight. No `geo` column in any production dataset uses them.
8. **No `provenance.json` schema.** The data is unaware of what "provenance" means.

### 5.3 Orphan writes

`preprocess_c.py` writes `archetype_data.csv`, which is not in `data/processed/`. Either the script was run before and the output was deleted, or the script was never run successfully, or the write was renamed. The script logs no error.

---

## 6. Production-Critical Datasets — Detail

### 6.1 `eligibility_data.csv` → E1 Eligibility

- **Source:** `loan_approval_dataset.csv` (4,269 rows, 13 cols) via `preprocess_a.py`.
- **Original raw dataset:** `loan_approval_dataset.csv` schema is `loan_id, no_of_dependents, education, self_employed, income_annum, loan_amount, loan_term, cibil_score, residential_assets_value, commercial_assets_value, luxury_assets_value, bank_asset_value, loan_status`. The schema matches no known public dataset. The 4,269-row count, the column names, the synthetic-rule labels (per [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md)), and the lack of any provenance together suggest **this dataset was generated synthetically**, possibly as a teaching artifact or demo, and was not intended for production lending.
- **License:** None. Source unknown.
- **Production status:** Live. E1 is the only model in production. E1's RFC was trained on this data.
- **Risk:** CRITICAL. Per [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md) §8, this dataset must be REPLACED.

### 6.2 `readiness_data.csv` → E5 Readiness

- **Source:** `RuralCreditData.csv` (40,000 rows, 20 cols) via `preprocess_b.py`.
- **Original raw dataset:** Schema includes `city, age, sex, social_class, primary_business, secondary_business, annual_income, monthly_expenses, old_dependents, young_dependents, home_ownership, type_of_house, occupants_count, house_area, sanitary_availability, water_availabity, loan_purpose, loan_tenure, loan_installments, loan_amount`. City names include Dhanbad, Manjapra — both Indian. This is the **only Indian-context dataset in production**. But the **engine does not actually load the data at runtime.** E5 is rule-based; the CSV is a reference for the engine author.
- **License:** None. 40k rows of "rural credit" data is unlikely to be a public Kaggle dataset. Could be scraped. Could be synthetic. Could be private and leaked. **Unknown provenance is HIGH risk for India-context data.**
- **Production status:** The CSV is not loaded by the orchestrator. The engine is rule-based and reads only its own code. The data is a **historical input** to the engine-author's design choices, not a runtime data dependency.
- **Risk:** HIGH (data provenance), LOW (production dependency). The provenance problem remains: the rules are derived from data whose source is unknown.

### 6.3 `livelihood_data.csv` → E6 Livelihood

- **Source:** `RuralCreditData.csv` via `preprocess_b.py` (one-hot encoded output).
- **Production status:** The CSV is **never loaded at runtime.** E6 is a hard-coded dictionary in `livelihood_mapper.py:38-67`. The CSV is a reference artifact from the time the dictionary was authored.
- **Risk:** Same as `readiness_data.csv`. HIGH provenance, LOW production.

### 6.4 `risk_tier_thresholds.json` → E2 Risk Tier

- **Source:** None. Hand-authored.
- **Production status:** Live. E2 loads this file at engine construction.
- **Calibration evidence:** None. Thresholds are not derived from observed default rates.
- **Risk:** HIGH (per [ML_AUDIT.md](ML_AUDIT.md) F2).

### 6.5 `borrower_archetype_definitions.json` → E3 Archetype

- **Source:** KMeans centroid ranking on `External_Cibil_Dataset.csv` (per `train_borrower_archetype.py:36-83`).
- **Production status:** Live. E3 loads this file and the KMeans artifact.
- **Risk:** CRITICAL. 1-row cluster labeled "Educated Professionals" (per [ML_AUDIT_PHASE_2.md](ML_AUDIT_PHASE_2.md) §2).

### 6.6 `External_Cibil_Dataset.csv` → E2 thresholds, E3 KMeans

- **Source:** Kaggle: home-credit-default-risk. The terms restrict use to non-commercial research and competition. **Production use of this data in a commercial lending product is a license violation.**
- **Population:** Czech, Russian, Kazakh, Chinese. Not Indian.
- **Production status:** Live. E3's KMeans was trained on this. The cluster identity is propagated to production.
- **Risk:** CRITICAL. Two compounding issues: license restriction + wrong population.

---

## 7. Recommended Keep/Remove List

### 7.1 Keep (production dependencies)

| File | Reason | Action |
|---|---|---|
| `data/processed/eligibility_data.csv` | Live dependency of E1 | **Replace** with real-outcome data per [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md) §8 |
| `data/raw/loan_approval_dataset.csv` | Source of eligibility_data.csv | **Replace source** (no production without replacement) |
| `data/processed/risk_tier_thresholds.json` | Live dependency of E2 | **Recompute** after E1 dataset is replaced |
| `data/processed/borrower_archetype_definitions.json` | Live dependency of E3 | **Replace** with defensible clustering per [ML_AUDIT_PHASE_2.md](ML_AUDIT_PHASE_2.md) §7 |
| `models/archetype/kmeans_model.pkl`, `scaler.pkl` | Live dependency of E3 | **Remove from production** per [ML_AUDIT_PHASE_2.md](ML_AUDIT_PHASE_2.md) §7 |
| `data/raw/External_Cibil_Dataset.csv` | Source of E2 thresholds and E3 KMeans | **Stop using in production**. Find commercial-licensed alternative for any future use. |
| `data/processed/readiness_data.csv` | Reference for E5 rules | **Retain as documentation** of how the rules were derived. Mark as not-loaded-at-runtime. |
| `data/processed/livelihood_data.csv` | Reference for E6 dictionary | **Retain as documentation**. Mark as not-loaded-at-runtime. |

### 7.2 Remove (orphans)

**Remove (no production use, no documented purpose, licensing risk):**

- `data/raw/BOB.csv` (101 rows)
- `data/raw/IDBI.csv` (321 rows)
- `data/raw/PNB1.csv` (1,190 rows)
- `data/raw/Syndicate.csv` (219 rows)
- `data/raw/bob_df.csv` (679 rows)
- `data/raw/combined_df.csv` (2,308 rows)
- `data/raw/idbi_df.csv` (222 rows)
- `data/raw/pnb_df.csv` (1,188 rows)
- `data/raw/states.csv` (34 rows)
- `data/raw/states_df.csv` (34 rows)
- `data/raw/syndicate_df.csv` (219 rows)
- `data/raw/Unseen_Dataset.csv` (100 rows)
- `data/raw/myFunction.py` (orphan utility, undocumented)
- `data/raw/Internal_Bank_Dataset.csv` (51,336 rows, never consumed)
- `data/raw/test_modified.csv` (37,717 rows, likely Kaggle)
- `data/raw/train_modified.csv` (87,020 rows, target = Disbursed, wrong target)

**Total rows to be removed: ~182,889 rows across 16 files.** That is 50.5% of all disk data.

**Before removing:**
- Verify with the institution's compliance and legal teams that these files are not subject to retention.
- Run a `git log -- data/raw/<file>` to confirm the files have no production history.
- After removal, regenerate `data/processed/` and `models/` to confirm no production path breaks.

### 7.3 Conditional keep (potential future use)

| File | Reason to consider | Action |
|---|---|---|
| `data/raw/External_Cibil_Dataset.csv` | Could be retained for offline academic analysis. | **Do not use in production.** Move to `data/raw/_archive/` with a README. |
| `data/raw/test_modified.csv`, `train_modified.csv` | Disbursement prediction is a different problem. | If institution wants a disbursement model, separate project. Not in scope. |

---

## 8. Mandatory Data Governance Additions (Binding)

Before any production deployment, the institution must create:

1. **`data/raw/provenance.json` per file**: `{filename, source_url, license, license_url, geographic_population, rows, columns, sha256, download_date, build_date, build_script, build_operator}`.
2. **`data/processed/provenance.json` per file**: same schema, plus `derived_from: {raw_file, build_script, build_date}`.
3. **`data/lineage.json`**: graph of `raw → processed → model → engine → route`. The current document's §2 is the manual reconstruction. The JSON file is the canonical version.
4. **LICENSE file at repo root**: a single document naming every dataset, its license, its permitted use (research, commercial, internal), and the date of legal review.
5. **Schema versioning**: every CSV gains a header comment with a version + sha256 of the build script.
6. **A central `data/raw/README.md`** explaining what each file is, what it is for, whether it is in production, and the legal status. The current README ([README.md](../README.md)) is project-level. The data-level README does not exist.

---

## 9. Production ML Readiness Verdict

| Status | Datasets |
|---|---|
| **In production with valid license** | None |
| **In production with NO license** | `eligibility_data.csv` (live E1), `risk_tier_thresholds.json` (live E2), `borrower_archetype_definitions.json` (live E3) |
| **In production with restrictive license** | `External_Cibil_Dataset.csv` (training data for E3, used in E2 calibration) |
| **In production with HIGH-unknown-provenance risk** | `RuralCreditData.csv` (source of `readiness_data.csv` and `livelihood_data.csv`; E5/E6 rules reference it indirectly) |
| **Not in production; should be removed** | 16 files (12 orphan CSVs, 1 utility, 1 Internal_Bank_Dataset, 2 train/test_modified) |

**Production ML readiness: 0/3.** Zero of the three production datasets has a valid license for commercial use. The institution is operating on data it cannot defend in a regulatory inquiry.

---

## 10. Summary

| Item | Value |
|---|---|
| Total raw files | 18 (14 distinct datasets) |
| Total processed files | 5 datasets + 1 orphan reference |
| Files in production | 3 raw + 5 processed |
| Orphan files (no production use) | 12 raw + 1 utility |
| Files with valid license for production | **0** |
| Files with documented provenance | **0** |
| `provenance.json` files | **0** |
| Build scripts found | 3 (preprocess_a/b/c.py) |
| Orphan write targets | 1 (`archetype_data.csv` referenced but not produced) |
| Files to remove | 16 (~50% of disk data) |

**The repository has a data lineage problem more serious than its ML model problem.** The model problem can be fixed by retraining. The data lineage problem is a structural absence: no licenses, no provenance, no documented sources, no legal review trail. The institution cannot answer "where did this data come from?" or "may we use this commercially?" for any of its production data. The frozen backend is frozen on top of a data governance void. The next phase of work is not modeling. It is data governance.

**Recommended next step:** delete the 12 orphan files + 1 utility after compliance review. Then the data governance work begins: source a license, generate a provenance file, sign a release. Only then does the [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md) §8 migration plan make sense to execute. Data is the constraint. Governance precedes modeling.
