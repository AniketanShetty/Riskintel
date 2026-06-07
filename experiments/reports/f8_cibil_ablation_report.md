# CIBIL Ablation Experiment Verdict

## Overview
This report assesses the structural dependency of the Random Forest model on the `cibil_score` feature. 
The objective is to determine if the exceptionally high baseline ROC-AUC represents genuine multivariate predictive learning, or simple dominance by a single feature.

## Metrics Comparison

| Metric | Baseline (Full Feature Set) | Ablated (Without `cibil_score`) | Delta |
|--------|-----------------------------|---------------------------------|-------|
| ROC-AUC | 0.9988 | 0.6010 | 0.3978 |
| Precision | 0.9812 | 0.6242 | 0.3570 |
| Recall | 0.9831 | 0.9510 | 0.0320 |
| F1 Score | 0.9821 | 0.7537 | 0.2284 |

## Verdict: FAIL

### Academic Defense Interpretation
The model suffers from **single-feature dominance**. The ablated AUC falls below 0.70, indicating a systemic collapse of predictive power when `cibil_score` is removed. The baseline AUC of 0.9988 is a direct proxy for the credit score. The peripheral features provide negligible orthogonal information, essentially making the Random Forest an expensive wrapper around a single variable.

### Interview Talking Points
*   **"Why use a Random Forest if it's just looking at CIBIL?"** -> "This ablation test revealed exactly that structural weakness. Currently, the model is overly dependent on the CIBIL score. We must re-evaluate our feature space and potentially use simpler models (like Logistic Regression) if alternative data holds no independent signal."
*   **"Is the 0.99 AUC real?"** -> "It is mathematically real but practically brittle. It reflects the purity of the CIBIL score relative to the labels, not complex multivariate pattern recognition."
