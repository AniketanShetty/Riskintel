# E1 Permutation Importance Audit Report

## Overview
This report assesses feature dominance using Permutation Importance (metric: ROC-AUC degradation). 
The objective is to quantify the relative contribution of each feature and explicitly calculate the dominance of `cibil_score` to determine if the E1 model is a genuine multivariate model or a simple CIBIL wrapper.

## Feature Importance Summary

| Feature | Importance (AUC Drop) | Relative Contribution (%) |
|---------|-----------------------|---------------------------|
| cibil_score | 0.4680 ± 0.0131 | 94.16% |
| loan_term | 0.0210 ± 0.0015 | 4.24% |
| residential_assets_value | 0.0035 ± 0.0007 | 0.70% |
| loan_amount | 0.0030 ± 0.0005 | 0.60% |
| annual_income | 0.0008 ± 0.0003 | 0.17% |
| luxury_assets_value | 0.0004 ± 0.0002 | 0.08% |
| commercial_assets_value | 0.0001 ± 0.0001 | 0.02% |
| bank_asset_value | 0.0001 ± 0.0000 | 0.02% |
| dependents | 0.0000 ± 0.0001 | 0.01% |
| self_employed | 0.0000 ± 0.0000 | 0.00% |
| education | -0.0000 ± 0.0000 | 0.00% |

## Key Metric
*   **`cibil_score` Dominance:** 94.16%
*   **Verdict:** FAIL

### Academic Defense Interpretation
The model suffers from single-feature dominance. Permutation analysis reveals that `cibil_score` alone accounts for {cibil_dominance:.2f}% of the total feature importance. The degradation in ROC-AUC when randomizing other features is negligible. This indicates the Random Forest has collapsed into a functional approximation of a single-variable threshold model, failing to capture meaningful multivariate interactions.

### Interview Talking Points
*   **"Did the model learn anything beyond the credit score?"** -> "No. Our empirical permutation tests prove the model is functionally a CIBIL wrapper. Over {cibil_dominance:.2f}% of the importance is concentrated in that single feature."
*   **"Why is this a failure?"** -> "Because deploying a complex ensemble method (Random Forest) for a single-variable decision boundary is computationally wasteful and mathematically brittle. We must either simplify the model or heavily re-engineer the alternative feature space."
