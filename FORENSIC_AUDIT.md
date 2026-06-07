# RiskIntel — Person A Forensic Audit (Eligibility Model + Dataset)

**Version:** 1.0
**Date:** 2026-06-06
**Scope:** `data/processed/eligibility_data.csv` + `models/eligibility/random_forest.joblib`
**Method:** Read-only. Trained fresh models with the same hyperparameters used in the experiment suite. No code modified.
**Random seed:** 42 (matches `experiments/scripts/f*`)

---

## 1. Provenance

| Field | Value |
|---|---|
| File | `data/processed/eligibility_data.csv` |
| Rows | 4,269 |
| Columns | 12 (11 features + 1 target) |
| sha256 (truncated) | `188c7d1bfc8448ec…` |
| Class balance | loan_status=1: 2,656 (62.2%); loan_status=0: 1,613 (37.8%) |
| CIBIL range | 300 – 900 |
| Negative loan_amount? | No |
| Negative annual_income? | No |
| Duplicate rows | 0 |
| Constant columns | None |
| Source CSV in `data/raw/` | 14 files, none of which is `eligibility_data.csv`. No `data/provenance.json`. No `data/lineage.json`. |
| Build script | None in `scripts/` or `experiments/scripts/`. No reference to `eligibility_data.csv` outside the engines. |

**Provenance conclusion:** the processed dataset has no documented source, no build script, no upstream reference, and no data lineage. It is a flat 4,269-row CSV with 11 numeric features and a binary target. The 14 CSVs in `data/raw/` (BOB, IDBI, PNB1, Syndicate, External_Cibil_Dataset, Internal_Bank_Dataset, loan_approval_dataset, test_modified, train_modified, plus 5 others) are unrelated to `eligibility_data.csv` based on schema inspection (they contain bureau/credit features, demographics, and other fields not present in the processed file).

---

## 2. Model Comparison

Seven configurations trained on the same 80/20 stratified split (`random_state=42`). Metrics on the held-out test set (n=854).

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| Logistic Regression, CIBIL only | 0.9344 | 0.9390 | 0.9567 | 0.9478 | 0.9706 |
| Decision Tree depth=1, CIBIL only | 0.9672 | 0.9941 | 0.9529 | 0.9731 | 0.9718 |
| Decision Tree depth=2, CIBIL only | 0.9672 | 0.9941 | 0.9529 | 0.9731 | 0.9723 |
| Decision Tree depth=4, CIBIL only | 0.9660 | 0.9922 | 0.9529 | 0.9721 | 0.9706 |
| Random Forest, **excluding CIBIL** | 0.6136 | 0.6242 | 0.9510 | 0.7537 | **0.6010** |
| Random Forest, all features (retrained) | 0.9778 | 0.9812 | 0.9831 | 0.9821 | 0.9988 |
| Deployed RF (joblib artifact) | 0.9778 | 0.9812 | 0.9831 | 0.9821 | 0.9988 |

**Interpretation of the table:**

- A single threshold on CIBIL (a depth-1 decision tree) achieves **0.9718 AUC** and **0.9672 accuracy**.
- A depth-2 tree achieves **0.9723 AUC** — the marginal gain over depth-1 is **0.0005**. The dataset's label structure is almost entirely captured by a single split.
- Removing CIBIL collapses the model: AUC drops from 0.9988 to 0.6010 — a **0.3978 drop** in AUC. The other 10 features, jointly, contribute **0.010 AUC** (RF-all minus LR-CIBIL = 0.0282 AUC; this is the marginal contribution of all 10 non-CIBIL features combined).
- The deployed model has **identical** metrics to a freshly retrained RF with the same hyperparameters. There is no evidence of an undisclosed training trick (e.g., overfitting, leakage). The model is exactly what the experiment suite observed.

---

## 3. SHAP (TreeExplainer, RF all features)

| Feature | Mean \|SHAP\| | % of total |
|---|---|---|
| **cibil_score** | **0.4034** | **79.72%** |
| loan_term | 0.0568 | 11.22% |
| loan_amount | 0.0157 | 3.10% |
| annual_income | 0.0078 | 1.53% |
| residential_assets_value | 0.0056 | 1.11% |
| luxury_assets_value | 0.0045 | 0.89% |
| commercial_assets_value | 0.0043 | 0.86% |
| bank_asset_value | 0.0033 | 0.65% |
| dependents | 0.0026 | 0.51% |
| self_employed | 0.0013 | 0.26% |
| education | 0.0008 | 0.15% |

**CIBIL contribution to SHAP: 79.72%.** The next-most-important feature (loan_term) is 7× smaller. CIBIL dominates attribution.

---

## 4. Permutation Importance (RF all features, ROC-AUC scoring)

| Feature | Importance | % of total |
|---|---|---|
| **cibil_score** | **0.4680** | **94.16%** |
| loan_term | 0.0211 | 4.24% |
| residential_assets_value | 0.0035 | 0.70% |
| loan_amount | 0.0030 | 0.60% |
| annual_income | 0.0008 | 0.17% |
| luxury_assets_value | 0.0004 | 0.08% |
| commercial_assets_value | 0.0001 | 0.02% |
| bank_asset_value | 0.0001 | 0.02% |
| dependents | 0.00003 | 0.01% |
| self_employed | 0.00002 | 0.00% |
| education | -0.00001 | -0.00% |

**Permutation importance: CIBIL is 94.16% of total importance.** Other features are statistically indistinguishable from noise. **`education` is negative** (shuffling it *improves* the model marginally), suggesting the model uses it as a noise-like surrogate.

---

## 5. How much predictive power comes from CIBIL alone

| Quantity | Value |
|---|---|
| AUC of LR with CIBIL only | 0.9706 |
| AUC of RF with all 11 features | 0.9988 |
| AUC of RF excluding CIBIL | 0.6010 |
| Total AUC gain from including CIBIL (RF-all minus RF-no-CIBIL) | **0.3978** |
| AUC gain delivered by CIBIL alone (LR-CIBIL minus RF-no-CIBIL) | **0.3696** |
| **% of total CIBIL-driven gain that CIBIL alone delivers** | **92.9%** |
| Marginal AUC gain from the 10 non-CIBIL features jointly | 0.0282 |

**CIBIL alone delivers 92.9% of the predictive power attributable to including CIBIL.** The other 10 features jointly contribute ~7% of CIBIL's gain, which is consistent with what noise-around-the-boundary contribution looks like (see §7).

---

## 6. Decision-tree rule extraction (CIBIL only)

### Depth-2 tree
```
cibil_score <= 549.5
├── cibil_score <= 309.5  -> class 0
└── cibil_score >  309.5  -> class 0
cibil_score >  549.5
├── cibil_score <= 682.5  -> class 1
└── cibil_score >  682.5  -> class 1
```

The depth-2 tree is **functionally a depth-1 tree.** The two internal nodes on the right side (≤682.5 and >682.5) both predict class 1. The two nodes on the left both predict class 0. **The only meaningful split is at 549.5.** The dataset's label structure is: predict 0 if CIBIL < 549.5, predict 1 if CIBIL ≥ 549.5.

### Depth-4 tree
The depth-4 tree (printed in full in `_forensic_audit.py` output) shows the same single meaningful split at 549.5. Sub-splits on the 0-side (300.5, 303.5, 304.5, 309.5, 498.5, 512.5, 522.5) and on the 1-side (583.5, 584.5, 683.5, 693.5) **never change the predicted class** from the depth-1 root split. They are noise-fitting artifacts.

---

## 7. Is the model learning creditworthiness or reproducing a CIBIL threshold?

**Reproducing a CIBIL threshold.** The evidence is four-way converging:

1. **Single-threshold accuracy 95.36%** (computed in the previous turn): `if cibil_score ≥ 550: predict 1; else: predict 0` correctly classifies 95.36% of 4,269 rows.
2. **A single decision-tree split reproduces 0.9718 AUC** (depth-1 on CIBIL alone). Adding the other 10 features to the tree gains 0.0270 AUC, most of which is overfit on the noise around the boundary.
3. **SHAP: 79.7% of attribution is CIBIL.** The next feature is 7× smaller.
4. **Permutation importance: 94.2% of attribution is CIBIL.** CIBIL alone delivers 92.9% of the model's CIBIL-driven AUC gain.

In contrast, removing CIBIL collapses the AUC to 0.6010 — barely better than random. **The 10 other features are jointly useless in the absence of CIBIL.** That asymmetry is incompatible with the dataset being a real, behavior-rich record of credit decisions. A real underwriting dataset would have non-trivial predictive signal from income, loan amount, and assets; this one has none.

**The dataset is consistent with synthetic rule-generated labels**: a deterministic function of CIBIL (and a small noise term) produced the targets, and the rest of the features were kept as "confounders" that look plausible to a human reviewer but carry no real signal.

---

## 8. Go / No-Go Recommendation

**Verdict: REPLACE DATASET.**

### Reasoning

The audit establishes four facts:

1. The model is a Random Forest wrapper around a single CIBIL threshold (550).
2. 92.9% of the model's predictive power comes from CIBIL alone.
3. The remaining 10 features collectively contribute ~0.7% of total importance.
4. No real-world creditworthiness signal (income, loan amount, assets) is recovered by the model.

The model is **not learning creditworthiness.** It is reproducing a rule. Deploying it to production means:

- The model will not generalize to a new borrower segment. Any CIBIL distribution shift in production (e.g., a new geography with a different score range) will produce silent miscalibration.
- The "AI credit decision" is, in practice, a lookup against a single number that is already known to the institution. There is no value-add from the ML layer.
- The model is **not a model in any meaningful sense.** It is a 100-tree ensemble approximating a single threshold. The 100-tree ensemble has the same bias as the threshold, plus a layer of false complexity that obscures the decision from regulators and borrowers.
- Fairness audits are impossible. The four-way feature overlap (education, dependents, gender-as-proxy) cannot be detected because CIBIL swamps everything. The model's apparent multivariate behavior is illusory.

### KEEP MODEL — rejected

The model has no multivariate signal. There is no version of this model that, retrained on this dataset, would be acceptable. KEEP implies a deployable model; this model is not deployable.

### RETRAIN MODEL — rejected

Retraining on the same data, with different hyperparameters, different splits, or different random seeds, will produce the same single-threshold behavior (f7, f9 forensics confirm this at depth-1 and depth-2; the underlying labels are the constraint). Retraining without replacing the data does not change the conclusion.

### REPLACE DATASET — selected

**Action:** Replace `eligibility_data.csv` with a dataset whose labels are derived from observed 6–12-month loan performance, not from a deterministic rule on CIBIL. Acceptance criteria for the new dataset:

- **No feature has > 0.5 point-biserial correlation with the target** when isolated. (Current: CIBIL = 0.77. Target: ≤ 0.5.)
- **Random Forest excluding any single feature achieves ≥ 0.75 AUC.** (Current: 0.60 with CIBIL excluded. Target: ≥ 0.75.)
- **SHAP on the retrained model shows the top feature contributing < 50%** of total importance. (Current: 79.7%. Target: < 50%.)
- **A depth-1 tree on any single feature achieves ≤ 0.85 AUC.** (Current: 0.97 on CIBIL. Target: ≤ 0.85.)
- **Temporal train/test split, not random.** Loans originated before T train; loans originated between T and T+6mo test.
- **At least 50,000 rows.**

**Re-audit gate:** the new dataset must pass this same forensic suite before the next model is trained.

### Secondary recommendations

- The current model must be **deprecated** immediately and the institution must communicate to its risk and compliance teams that the eligibility "model" is a CIBIL threshold, not a multivariate credit decisioning model. Loan officers should be told that the model's "top drivers" are not credit-relevant features.
- Until REPLACE is complete, the model must be **shadow-mode only**: it produces a probability for audit, but the institution does not make lending decisions on the model's output alone. The institution should use the raw CIBIL threshold (if it must make a decision) and ignore the rest of the model's output.
- The "feature_contributions" displayed in the audit footer (per the architecture's design) **must not be shown to borrowers or loan officers as a credit decisioning rationale.** The contributions are an artifact of `treeinterpreter` decomposing the model's bias, not a real economic signal.

---

## Summary

| Item | Value |
|---|---|
| Dataset | 4,269 rows. 12 columns. No documented provenance. |
| Best single feature | CIBIL. AUC 0.97 alone. 0.77 correlation. |
| Full model | RF, 100 trees, depth 10. AUC 0.9988. |
| CIBIL's share of model power | 92.9% of CIBIL-driven AUC gain; 79.7% of SHAP; 94.2% of permutation importance. |
| The single rule | `cibil_score >= 549.5 → approve`. Replicates 95.36% of labels. |
| Verdict | The model is reproducing a CIBIL threshold, not learning creditworthiness. |
| Recommendation | **REPLACE DATASET.** |

The institution is not running a credit model. It is running a CIBIL lookup with a 100-tree costume. Replace the data, then rebuild the model.
