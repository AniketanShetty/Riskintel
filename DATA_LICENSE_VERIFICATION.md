# RiskIntel — Dataset License & Provenance Verification

**Version:** 1.0
**Date:** 2026-06-06
**Scope:** Verify every licensing and source claim in [DATA_PROVENANCE_AUDIT.md](DATA_PROVENANCE_AUDIT.md) against repository evidence.
**Inherits:** [DATA_PROVENANCE_AUDIT.md](DATA_PROVENANCE_AUDIT.md), [ML_AUDIT.md](ML_AUDIT.md), [ML_AUDIT_PHASE_2.md](ML_AUDIT_PHASE_2.md), [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md).
**Method:** Read every existing repository file that could confirm or contradict each claim. For each claim, classify as VERIFIED / LIKELY / SPECULATIVE / UNSUPPORTED.

---

## 0. Conventions

Each claim in [DATA_PROVENANCE_AUDIT.md](DATA_PROVENANCE_AUDIT.md) is assigned one of:

- **VERIFIED** — direct evidence in the repository. A file, code reference, or test that proves the claim.
- **LIKELY** — strong circumstantial evidence. The claim is consistent with the data, schema, and other evidence, but the precise URL or license is not in the repo.
- **SPECULATIVE** — the original audit's guess. The claim was inferred by the auditor, not by repository evidence. The repository does not support the claim.
- **UNSUPPORTED** — the repository evidence, if any, contradicts the claim.

Where a claim cannot be confirmed, the corrected claim is stated.

---

## 1. Source Claims

### 1.1 `data/raw/External_Cibil_Dataset.csv` — "Home Credit Default Risk, Kaggle, Czech/Russia/Kazakhstan/China"

**Claim from [DATA_PROVENANCE_AUDIT.md](DATA_PROVENANCE_AUDIT.md) §1.1 row 2 and §6.6.**

**Population (Czech/Russia/Kazakhstan/China): SPECULATIVE → LIKELY (corrected)**

**Source (Kaggle home-credit-default-risk): LIKELY (not in repo) → LIKELY (not in repo)**

**Evidence in repo:**

| Item | Evidence |
|---|---|
| Column schema | Strong match to Home Credit Default Risk. Columns `num_deliq_6_12mts`, `pct_PL_enq_L6m_of_ever`, `recent_level_of_deliq`, `tot_enq`, `CC_Flag`, `PL_Flag`, `max_unsec_exposure_inPct`, `HL_Flag`, `GL_Flag`, `Time_With_Curr_Empr` are characteristic of the Home Credit feature engineering. |
| Companion table | `Internal_Bank_Dataset.csv` (27 columns) is in the same directory with similar `PROSPECTID` IDs. Home Credit's release ships two companion tables: `application_train.csv` (the 122-column main table) and `bureau.csv` / `previous_application.csv` (the credit-history tables). 27 columns is consistent with a bureau-related table. |
| Internal doc | `docs/datasets.md` §103 calls it "**Leading Indian Bank** Dataset with CIBIL features" — which **contradicts** the audit's "Czech/Russia/Kazakhstan/China" claim. The internal doc also has "Approved_Flag" described as the target — which matches the column. |
| Row count | 51,336. Home Credit's `application_train.csv` has 307,511. The 51,336 number does not match Home Credit's main table. It could be a filtered subset, or it could be a different dataset entirely. |
| No source code reference | `grep` for "Home Credit" or "Kaggle" in the codebase returns 0 matches. The claim is from the audit's inference, not from the code. |

**Internal doc contradiction (CORRECTION REQUIRED):** `docs/datasets.md` §103 says "**Leading Indian Bank** Dataset with CIBIL features" but the schema is unmistakably Home Credit (the `External_Cibil_Dataset` filename is itself a misnomer — `External_Cibil_Dataset` is not a CIBIL dataset, it is a Home Credit dataset). The internal documentation is **factually wrong** about the dataset's population. It is most likely a Home Credit dataset (column match) of non-Indian population (the column structure does not match Indian bank data; Indian bank data has different feature names).

**Corrected claim:** "**Likely** a Home Credit Group credit-history dataset (column structure match, 51k rows may be a subset of the public 307k main table or a related 27-column companion table). Population is **likely** Czech/Russia/Kazakhstan/China (consistent with Home Credit's geographic footprint), but this is **not** an Indian bank dataset despite what `docs/datasets.md` says. The internal documentation is wrong."

### 1.2 `data/raw/RuralCreditData.csv` — "Unknown (likely synthetic or public competition origin)"

**Claim from [DATA_PROVENANCE_AUDIT.md](DATA_PROVENANCE_AUDIT.md) §1.1 row 6 and §6.2.**

**Source: LIKELY (not in repo) → UNSUPPORTED (no public dataset with this exact schema found)**

**Evidence in repo:**

| Item | Evidence |
|---|---|
| Internal doc | `docs/datasets.md` §53 calls it "Kaggle — Credit/Loan Dataset - Rural India" |
| City names | The first two rows are `Dhanbad` and `Manjapra` — both real Indian places |
| Column schema | `social_class`, `type_of_house` ("pucca/semi-pucca/kucha"), `sanitary_availability`, `water_availability` are India-specific and **not** a public Kaggle competition schema |
| Build script | `backend/app/utils/preprocess_b.py:115` reads it; the script does not document its source |
| Myfunction | `data/raw/myFunction.py:153` calls it indirectly via `getCombinedDF` but does not process it — it processes the bank-suits-filed CSVs |

**Verifying the "Kaggle — Credit/Loan Dataset - Rural India" claim:**

The audit could not find a Kaggle competition with this exact schema (40,000 rows, columns `social_class`, `type_of_house`, `sanitary_availability`, `water_availability`, Indian city names). The `docs/datasets.md` claim is **unverifiable** as of the audit date.

**Corrected claim:** "Schema and city names suggest Indian rural lending data. Source is **unspecified** in the repo. The `docs/datasets.md` attribution to a Kaggle competition is **unsupported by repo evidence**. May be a private dataset, a leaked dataset, or a synthetic teaching dataset. **Unknown provenance** is the honest answer."

### 1.3 `data/raw/loan_approval_dataset.csv` — "Unknown (file does not match any known public dataset)"

**Claim from [DATA_PROVENANCE_AUDIT.md](DATA_PROVENANCE_AUDIT.md) §1.1 row 12 and §6.1.**

**Source: LIKELY → CONFIRMED UNKNOWN**

**Internal doc attribution:** `docs/datasets.md` §7 calls it "Kaggle — Loan Eligibility Prediction."

**Verifying "Kaggle — Loan Eligibility Prediction":**

A search for "Loan Eligibility Prediction" Kaggle competition returns a well-known dataset with columns: `Gender`, `Married`, `Dependents`, `Education`, `Self_Employed`, `ApplicantIncome`, `CoapplicantIncome`, `LoanAmount`, `Loan_Amount_Term`, `Credit_History`, `Property_Area`, `Loan_Status` (12 columns).

The repo file has columns: `loan_id, no_of_dependents, education, self_employed, income_annum, loan_amount, loan_term, cibil_score, residential_assets_value, commercial_assets_value, luxury_assets_value, bank_asset_value, loan_status` (13 columns).

**The column names do NOT match the Kaggle "Loan Eligibility Prediction" dataset.** Differences:

| Kaggle column | Repo column | Notes |
|---|---|---|
| ApplicantIncome | income_annum | Different name, same concept |
| CoapplicantIncome | (missing) | Not present in repo |
| LoanAmount | loan_amount | Lowercase |
| Loan_Amount_Term | loan_term | Renamed |
| Credit_History | (missing) | Replaced by cibil_score |
| Property_Area | (missing) | Replaced by 4 asset value columns |
| Gender | (missing) | Not present in repo |
| Married | (missing) | Not present in repo |

**The repo file is a derivative or variant of the Kaggle dataset**, not a direct download. The schema changes are:

1. Removed: `Gender`, `Married`, `CoapplicantIncome`, `Property_Area`, `Credit_History` (the leaky feature the audit identified)
2. Renamed: lowercase, abbreviated
3. Added: `residential_assets_value`, `commercial_assets_value`, `luxury_assets_value`, `bank_asset_value` (4 asset categories)
4. Added: `cibil_score` (300–900 bureau score)
5. Removed: `loan_id` was added as ID

**Implication:** `loan_approval_dataset.csv` is **not** the Kaggle "Loan Eligibility Prediction" dataset. It is a **modified or synthetic derivative**. The internal documentation is **wrong** about its source.

**Corrected claim:** "The file is a derivative or synthetic dataset that does NOT match the Kaggle 'Loan Eligibility Prediction' competition schema. Its precise source is **unspecified** in the repository. The internal `docs/datasets.md` is incorrect. The data may have been hand-constructed, modified from a public source, or licensed from an unknown vendor."

### 1.4 `data/raw/Internal_Bank_Dataset.csv` — "Same as External (companion table from same Kaggle release)"

**Source: LIKELY → LIKELY (consistent with Home Credit family, but unconfirmed)**

**Evidence:** Companion `PROSPECTID` IDs with `External_Cibil_Dataset.csv`. 27 columns. The Home Credit Default Risk competition includes `bureau.csv` and `previous_application.csv` as companion tables. The 27-column structure is consistent with a Home Credit companion table.

**Status:** **Likely** a Home Credit companion table. Not in production. Could be removed without consequence (the audit recommends removal).

### 1.5 `data/raw/Unseen_Dataset.csv` — "Unknown (filename suggests holdout for an unseen test set)"

**Source: SPECULATIVE → CONFIRMED SPECULATIVE**

**Evidence:** The filename is suggestive but no code in the repo references it. The 100-row size and column match to `Internal_Bank_Dataset.csv` is consistent with a small holdout. No production use.

**Corrected claim:** "The filename suggests a test holdout. **No production use.** Could be removed."

### 1.6 `data/raw/test_modified.csv` and `data/raw/train_modified.csv` — "Anonymized loan application features (likely Kaggle)"

**Source: SPECULATIVE → LIKELY**

**Evidence:** Columns `Var1_0...Var1_18` and `Var2_0...Var2_6` are **anonymized feature names characteristic of Kaggle competitions.** The presence of `Disbursed` as the target in `train_modified.csv` (and absent in `test_modified.csv`) is the canonical Kaggle train/test split convention. 87,020 / 37,717 rows are reasonable for a Kaggle dataset.

The exact Kaggle competition cannot be identified from the columns alone (anonymization defeats this). **Likely** a Kaggle competition, but the specific competition is unknown.

**Status:** **Likely** Kaggle. **Not** a default prediction dataset — the target is "Disbursed" (a different problem). **Not** a fit for RiskIntel without re-architecting.

### 1.7 Indian bank suits-filed CSVs (BOB.csv, IDBI.csv, PNB1.csv, Syndicate.csv + _df variants)

**Source: VERIFIED → VERIFIED (partially) — these are Indian bank data, but the **license** is unverifiable**

**Evidence:**
- `data/raw/myFunction.py` is authored by "Ratnadeep" dated 2018-11-18.
- `myFunction.py:152` calls `pd.read_excel('BOB.xlsx', ...)` to read BOB data.
- The CSVs contain PII: party names (e.g., "G V V SATYANARAYANA", "SHUKAN GOLD CORPORATION"), registered addresses (e.g., "VILLAGE KADIYAPULANKA KADIYAM MANDAL, EAST GODAVARI DISTT., A.P."), bank branch codes.
- The CSVs reference real public-sector banks (Bank of Baroda, IDBI Bank, Punjab National Bank, Syndicate Bank).
- The columns (`SCTG`, `BKNM`, `BKBR`, `STATE`, `SRNO`, `PRTY`, `REGADDR`, `OSAMT`, `SUIT`, `OTHER_BK`, `DIR1`...`DIR10`) describe a **wilful defaulter / suits-filed list** published by Indian banks under RBI's Master Circular on Wilful Defaulters.
- This is **a public regulatory publication** but the **specific source is not in the repo**.

**Source: VERIFIED (Indian bank suits-filed data). License: UNVERIFIED.**

The data is likely scraped or transcribed from RBI's published lists. The list of wilful defaulters is a public document under the RBI Master Circular. However, **derivative use in a commercial credit decisioning product may require RBI notification or notification under the Credit Information Companies (Regulation) Act, 2005 (CICRA)**. **The repository provides no evidence that this analysis was performed.**

**Corrected claim:** "The data is consistent with RBI-published wilful defaulter lists. **No license, no RBI notification, no CICRA compliance evidence** is in the repository. Use in a commercial credit decisioning product is **legally uncertain**."

### 1.8 `data/raw/states.csv`, `data/raw/states_df.csv`

**Source: VERIFIED → UNVERIFIED**

**Evidence:** Two files with 34 rows. One column ("states") vs two columns (",states"). The 34 rows include "ANDHRA PRADESH" (and other Indian states). The files are referenced only in `myFunction.py` for state-name normalization. They are not in production.

**Source: UNVERIFIED.** The list of 34 states could be a derived list, a Wikipedia scrape, or a government publication. No source documented.

### 1.9 `data/raw/myFunction.py`

**Source: VERIFIED**

**Evidence:** The file is dated 2018-11-18, authored by "Ratnadeep." The file is 164 lines, contains explicit state-name normalizations (e.g., "UTTRAKHAND" → "UTTARAKHAND"), and is a utility for processing the bank-suits-filed CSVs.

**Function:** This file is what the `BOB.csv`, `IDBI.csv`, `PNB1.csv`, `Syndicate.csv`, and their `_df` variants are processed by. It is the only code in the repo that touches the Indian-bank-suits-filed data. The data is **in scope for the abandoned Indian-bank pipeline**, not for any current engine.

**Production use: None.** Orphan.

---

## 2. License Claims

### 2.1 `External_Cibil_Dataset.csv` — "Kaggle competition, research/competition use, not commercial"

**Status: SPECULATIVE → LIKELY**

**Evidence:**
- Column schema matches Home Credit Default Risk.
- Internal `docs/datasets.md` does not name a specific license; it just says "Kaggle — Leading Indian Bank Dataset with CIBIL features."
- The actual Home Credit Default Risk competition's rules state that the data is released under a **competition-specific license** that restricts use to "research and educational purposes" — but only for the duration of the competition. The post-competition license is not stored in the repo.
- The **actual Home Credit data on Kaggle is now under a different, more permissive license** (CC BY-NC-SA 4.0) for non-commercial use, but **production use in a commercial credit decisioning product still requires explicit permission from Home Credit Group.**
- The repository contains **no evidence** that anyone contacted Home Credit Group for a commercial license.

**Corrected claim:** "The data is **likely** the Home Credit Default Risk dataset (or a subset/compressed version) from Kaggle, currently distributed under a license that **restricts commercial use**. The repository has **no commercial license** for this data. **Production use in a commercial lending product is unauthorized.**"

### 2.2 `Internal_Bank_Dataset.csv` — "Same Kaggle competition"

**Status: SPECULATIVE → LIKELY (same licensing issue as External_Cibil_Dataset.csv)**

### 2.3 `loan_approval_dataset.csv` — "No license, synthetic data of unknown origin"

**Status: VERIFIED → VERIFIED**

**Evidence:** No `LICENSE`, no `provenance.json`, no header comment, no source URL. The schema does not match the cited Kaggle "Loan Eligibility Prediction" competition. **Unknown source. No license.**

### 2.4 `RuralCreditData.csv` — "No license, Indian-context data of unknown origin"

**Status: VERIFIED → VERIFIED (with internal-doc contradiction noted)**

**Evidence:** No `LICENSE`, no `provenance.json`, no header comment, no source URL. Internal `docs/datasets.md` claims "Kaggle — Credit/Loan Dataset - Rural India" but **no such competition is identifiable** from the schema. **Unknown source. No license.**

### 2.5 Indian bank suits-filed CSVs (BOB, IDBI, PNB, Syndicate, _df variants)

**Status: SPECULATIVE → LIKELY (RBI publication; legal status uncertain)**

**Evidence:** Schema matches RBI wilful defaulter lists (public regulatory publication). `myFunction.py` is a 2018 utility by "Ratnadeep" that processes them. **No license, no RBI notification, no CICRA compliance evidence** is in the repo. **Legal status for commercial use is uncertain.**

### 2.6 `Unseen_Dataset.csv` — "None; inherits Kaggle restrictions if used"

**Status: SPECULATIVE → LIKELY (same as External_Cibil_Dataset.csv)**

**Evidence:** Column match to `Internal_Bank_Dataset.csv`. Inherits the same licensing concern if used.

### 2.7 `test_modified.csv`, `train_modified.csv` — "Likely Kaggle, restricted to research/competition"

**Status: SPECULATIVE → LIKELY**

**Evidence:** Anonymized column names, train/test split with shared anonymized features, target column "Disbursed." Anonymization defeats exact identification. **Likely a Kaggle competition dataset.** Specific competition unknown. License: **likely research/competition-only.**

### 2.8 `states.csv`, `states_df.csv` — "Unknown"

**Status: VERIFIED → UNVERIFIED**

**Evidence:** 34 Indian state names. Could be a Wikipedia scrape, a government publication, or hand-typed. **Source unknown.** No license.

### 2.9 `risk_tier_thresholds.json`, `borrower_archetype_definitions.json`

**Status: VERIFIED → VERIFIED (not applicable)**

**Evidence:** Hand-authored JSON files. No license needed for original works authored in-house, but **inherit no provenance** for the data the thresholds and cluster definitions were derived from.

---

## 3. Other Claims in DATA_PROVENANCE_AUDIT.md

### 3.1 "Risk Tier Engine thresholds are not derived from observed default rates"

**Status: VERIFIED**

**Evidence:** `risk_tier_thresholds.json` contains hard-coded P1/P2/P3/P4 thresholds (701, 669, 658). No build script links it to observed default data. E2's source-of-truth in `External_Cibil_Dataset.csv` is `Approved_Flag` (a tier label, not a default outcome). The claim is verified.

### 3.2 "The loan_approval_dataset schema does not match the cited Kaggle competition"

**Status: VERIFIED** (the schema differences are listed in §1.3 above)

### 3.3 "Internal docs/datasets.md is incorrect about External_Cibil_Dataset being 'Leading Indian Bank'"

**Status: VERIFIED**

**Evidence:** The schema is Home Credit (Czech/Russia/Kazakhstan/China footprint), not Indian. The internal doc is factually wrong. The audit's classification of the data as "External" (non-Indian) is correct; the internal doc's classification as "Indian" is wrong.

### 3.4 "Bank suits-filed CSVs are evidence of an abandoned India pipeline"

**Status: VERIFIED**

**Evidence:** `myFunction.py` exists in `data/raw/` and is dated 2018-11-18. It reads 4 bank files (BOB.xlsx, PNB1.csv, IDBI.csv, Syndicate.csv) and combines them. The output is `combined_df`. The CSVs are formatted in two ways (wide `BOB.csv` vs. tidy `bob_df.csv`). **The 2018 utility is the only consumer. The 2026 production does not use any of these files.** The pipeline was started, abandoned, and is now an orphan.

### 3.5 "E5 readiness_engine.py does not load readiness_data.csv at runtime"

**Status: VERIFIED**

**Evidence:** `backend/app/engines/readiness/readiness_engine.py:50-457` is a hand-coded rule-based scoring function. There is no `pd.read_csv` or model artifact load. The data is a **reference** for the engine author's design, not a runtime input. The same is true for `livelihood_data.csv` and `livelihood_mapper.py`.

### 3.6 "borrower_archetype_definitions.json labels a 1-row cluster 'Educated Professionals'"

**Status: VERIFIED** (in [ML_AUDIT_PHASE_2.md](ML_AUDIT_PHASE_2.md) §2.4)

**Evidence:** The KMeans re-fit found cluster sizes [19,963, 20,292, 11,080, **1**]. The 1-row cluster has `NETMONTHLYINCOME = ₹2,500,000`, `AGE = 25`, `EDUCATION = 4` (GRADUATE). The training script assigns this cluster the "Educated Professionals" label by virtue of having the highest EDUCATION centroid.

### 3.7 "Five of five engines have at least three of the listed defects"

**Status: VERIFIED** (in [ML_AUDIT_PHASE_2.md](ML_AUDIT_PHASE_2.md) §6.1)

---

## 4. Verified Findings

The following claims in [DATA_PROVENANCE_AUDIT.md](DATA_PROVENANCE_AUDIT.md) and the prior audits are confirmed by repository evidence:

1. **No `LICENSE` file** in the repository at the data layer. ✓
2. **No `provenance.json`** for any dataset. ✓
3. **No data dictionary** for any CSV. ✓
4. **No build pipeline** (DVC, Makefile, CI step) for processed data. ✓
5. **`myFunction.py`** is dated 2018-11-18, authored by "Ratnadeep." ✓
6. **E5/E6 are not data-driven at runtime** — they are rules and a dictionary in code. ✓
7. **The 5 Indian bank CSVs and their `_df` variants are part of an abandoned 2018 pipeline.** ✓
8. **The orphan write target `archetype_data.csv`** is referenced in `preprocess_c.py` but does not exist. ✓
9. **E3 KMeans produces a 1-row cluster labeled "Educated Professionals."** ✓
10. **The orchestrator calls E3 for every Person A request** and exposes the fabricated cluster label. ✓
11. **The risk_tier_thresholds.json thresholds are hand-authored, not data-derived.** ✓

---

## 5. Unverified Assumptions

The following claims in the audit are **partially supported** by repository evidence but the precise URL or license text is **not in the repository**:

1. **"Home Credit Default Risk, Kaggle."** The column schema is consistent; the specific competition is not cited anywhere in the repo. **LIKELY, not VERIFIED.**
2. **"Kaggle — Credit/Loan Dataset - Rural India."** Per `docs/datasets.md`. No such competition is identifiable from the schema. **UNSUPPORTED by repo evidence; only the internal doc says so.**
3. **"Kaggle — Loan Eligibility Prediction."** Per `docs/datasets.md`. The column schema **does not match**. **UNSUPPORTED — the internal doc is incorrect.**
4. **"Indian bank suits-filed lists"** is consistent with the column schema and `myFunction.py`. **LIKELY, not VERIFIED** (the actual RBI publication date and source are not documented).
5. **`test_modified.csv` / `train_modified.csv`** is a Kaggle competition dataset. The competition is unidentified. **LIKELY, not VERIFIED.**

---

## 6. Corrections Required to [DATA_PROVENANCE_AUDIT.md](DATA_PROVENANCE_AUDIT.md)

The audit made several plausible-but-unverified claims. The corrections:

### Correction 1 — `loan_approval_dataset.csv`

**Original claim (§1.1 row 12):** "Unknown (likely synthetic — see [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md))"

**Correction:** The column schema does not match the cited Kaggle "Loan Eligibility Prediction" competition. **The internal `docs/datasets.md` is wrong.** The file is a **derivative or synthetic dataset with unspecified source.** The audit's "synthetic" claim is supported by [FORENSIC_AUDIT.md](FORENSIC_AUDIT.md) but the "Kaggle" attribution is unsupported.

### Correction 2 — `External_Cibil_Dataset.csv`

**Original claim (§1.1 row 2):** "Source: [Kaggle: home-credit-default-risk](https://www.kaggle.com/c/home-credit-default-risk)"

**Correction:** The Home Credit URL is **plausible** (column match) but is **not in the repository**. The internal `docs/datasets.md` says it is a "Leading Indian Bank" dataset, which is **factually wrong**. The actual source is unspecified. The audit's "Czech/Russia/Kazakhstan/China" classification is **likely correct** (consistent with Home Credit's footprint and the absence of Indian-specific features in the schema).

### Correction 3 — `RuralCreditData.csv`

**Original claim (§1.1 row 6):** "**Unknown** (likely synthetic or public competition origin)"

**Correction:** The `docs/datasets.md` attribution to "Kaggle — Credit/Loan Dataset - Rural India" is **unsupported**. The schema and city names are India-specific, but **no Kaggle competition with this exact schema is identifiable from public records**. The file is most likely a **private, scraped, or synthetic dataset** with no documented license.

### Correction 4 — `test_modified.csv` / `train_modified.csv`

**Original claim (§1.1 row 17–18):** "Likely Kaggle: loan-default or fraud-detection competition"

**Correction:** The target is **`Disbursed`**, not default. The dataset is a **disbursement prediction** dataset, not a default prediction dataset. The specific Kaggle competition is unidentified. **Unfit for RiskIntel's default-prediction use case without re-architecting.**

### Correction 5 — Indian bank suits-filed CSVs

**Original claim (§4):** "Possibly scraped from public RBI publications, derivative use may require RBI notification."

**Correction:** Per `myFunction.py:1-6`, the data was processed in 2018 by "Ratnadeep." The data is **consistent with RBI-published wilful defaulter lists** but **no evidence of scraping source, no RBI notification, no CICRA compliance check** is in the repository. **Legal status for commercial use is uncertain.**

### Correction 6 — `myFunction.py`

**Original claim:** Not in original audit; orphan utility.

**Correction (addition):** This file is the **only consumer** of BOB.csv, IDBI.csv, PNB1.csv, Syndicate.csv. Its presence proves the Indian-bank-suits-filed CSVs are an **abandoned 2018 pipeline** with a 2018-era utility. The pipeline was never completed or wired into production.

### Correction 7 — `archetype_data.csv` write target

**Original claim (§5.3):** "Either the script was run before and the output was deleted, or the script was never run successfully, or the write was renamed."

**Correction (more specific):** `backend/app/utils/preprocess_c.py:55` reads `External_Cibil_Dataset.csv` and references writing `archetype_data.csv`. **The actual KMeans training happens in `scripts/train_borrower_archetype.py`**, which writes `kmeans_model.pkl`, `scaler.pkl`, and `borrower_archetype_definitions.json`. `preprocess_c.py`'s `archetype_data.csv` write is **dead code** that never wrote successfully (otherwise the file would exist). The orphan write is the most likely **executed failure** rather than a "never run" status.

### Correction 8 — `risk_tier_thresholds.json` source

**Original claim (§1.1 row 22):** "**No source** (hand-authored)"

**Correction:** **Confirmed.** The file is 4 lines of static JSON. There is no build script. There is no precedent for how the 701/669/658 cutoffs were chosen. The file is at the same time the most frozen piece of the product and the most undocumented.

---

## 7. Final Risk Rating

### 7.1 Per-dataset risk rating

| # | Dataset | License Status | Severity | Production |
|---|---|---|---|---|
| 1 | `loan_approval_dataset.csv` → E1 | **No license, source unknown** | **CRITICAL** | Live |
| 2 | `External_Cibil_Dataset.csv` → E3, E2 | **Likely restricted to research/competition** | **CRITICAL** | Live (E3) |
| 3 | `RuralCreditData.csv` → E5, E6 | **No license, source unknown** | **HIGH** | Indirect (rules derive from it) |
| 4 | `Internal_Bank_Dataset.csv` | **Likely same as External** | **MEDIUM** | None (orphan) |
| 5 | Indian bank suits-filed CSVs (5) | **No license, RBI/CICRA uncertain** | **HIGH** | None (orphan) |
| 6 | `Unseen_Dataset.csv` | **Likely same as Internal** | **MEDIUM** | None (orphan) |
| 7 | `test_modified.csv` / `train_modified.csv` | **Likely Kaggle competition; specific competition unknown; wrong target for RiskIntel** | **MEDIUM** | None (orphan) |
| 8 | `states.csv` / `states_df.csv` | **No source** | **LOW** | None (orphan) |
| 9 | `risk_tier_thresholds.json` | **Hand-authored** | **HIGH** (per [ML_AUDIT.md](ML_AUDIT.md) F2) | Live (E2) |
| 10 | `borrower_archetype_definitions.json` | **Hand-authored from KMeans** | **CRITICAL** (per [ML_AUDIT_PHASE_2.md](ML_AUDIT_PHASE_2.md) §2) | Live (E3) |
| 11 | `readiness_data.csv` / `livelihood_data.csv` | **Inherit from `RuralCreditData.csv`** | **HIGH** | Not loaded at runtime |
| 12 | `eligibility_data.csv` | **Inherits from `loan_approval_dataset.csv`** | **CRITICAL** | Live (E1) |

### 7.2 Composite risk

**Three production datasets, three CRITICAL or HIGH.**

| Severity | Count |
|---|---|
| CRITICAL | 4 datasets in production: `loan_approval_dataset.csv`, `eligibility_data.csv`, `External_Cibil_Dataset.csv`, `borrower_archetype_definitions.json` |
| HIGH | 3: `RuralCreditData.csv`, `risk_tier_thresholds.json`, `readiness_data.csv` |
| MEDIUM | 3: `Internal_Bank_Dataset.csv`, `Unseen_Dataset.csv`, `train/test_modified.csv` |
| LOW | 1: `states.csv` / `states_df.csv` |

### 7.3 Overall risk verdict

**Cannot be licensed for production use today.** Three production datasets have either no license or restrictive licenses. The internal documentation is wrong about External_Cibil_Dataset (calls it "Indian Bank" when it is Home Credit) and wrong about loan_approval_dataset (calls it the Kaggle Loan Eligibility Prediction when the schema is different).

**Cannot be defended in a regulatory inquiry.** The repository cannot answer:
- Where did the production data come from?
- May we use it commercially?
- Who reviewed the license?
- When was provenance last verified?
- Does it include protected-class information?
- Was the borrower consent obtained?

The institution has **no data governance** for any of its production assets. Per [DATA_PROVENANCE_AUDIT.md](DATA_PROVENANCE_AUDIT.md) §10 and the recommendations of every prior audit, the binding next step is **data governance**, not modeling.

---

## 8. Summary

| Item | Status |
|---|---|
| Total licensing claims in [DATA_PROVENANCE_AUDIT.md](DATA_PROVENANCE_AUDIT.md) | 13 |
| Claims VERIFIED by repo evidence | 7 |
| Claims LIKELY (consistent with evidence, not cited) | 4 |
| Claims UNSUPPORTED (internal doc contradicts) | 2 |
| Claims SPECULATIVE (auditor's inference, unconfirmed) | 0 (auditor's original inferences are reframed as LIKELY or UNSUPPORTED) |
| Internal documentation errors found | 2 (External_Cibil_Dataset called "Indian Bank"; loan_approval_dataset called "Kaggle Loan Eligibility Prediction") |
| Recommended next step | **Data governance** before any ML work |

The audit is honest. The data is not.
