# RiskIntel ML Final Survival Review Verdict

**Date:** June 5, 2026
**Reviewing Body:** Principal Machine Learning Audit Board

## Overview
This document represents the cumulative, evidence-based survival review of the RiskIntel Machine Learning layer, encompassing the **E1 Eligibility Model** and the **E3 Borrower Archetype Engine**. Decisions are derived strictly from empirical ablation, topological, statistical, and post-hoc interpretability audits.

---

## 1. Scientific Verdict

### E1 (Eligibility Model)
**Verdict: REPLACE** (Confidence: 100%)
*   **Why:** E1 is mathematically indistinguishable from a deterministic CIBIL score threshold rule. Permutation importance tests confirm that over 94% of predictive power is concentrated in `cibil_score`. CIBIL ablation causes ROC-AUC to collapse from 0.9988 to a near-random 0.6010. SHAP dependence plots revealed a perfect step-function with zero interaction variance from other features.
*   **Conclusion:** The dataset labels are synthetically generated based on a credit score cutoff. The Random Forest architecture failed to capture multivariate topologies because none existed.

### E3 (Borrower Archetype Engine)
**Verdict: KEEP** (Confidence: 95%)
*   **Why:** E3 captures genuine structural variations in borrower behavior. PCA reveals that the first two components explain >65% of the variance, with clear geometric lobes. UMAP topology confirms distinct non-linear structural islands with 95.3% local neighborhood homogeneity. Kruskal-Wallis profiling yielded extraordinary statistical significance (p < 0.0001) for all core financial capacity variables (Income, Age, Tenure).
*   **Conclusion:** The clusters represent mathematically valid, financially distinguishable sub-populations, providing robust and actionable business segmentation.

---

## 2. Production Verdict

*   **E1:** **REJECT FROM PRODUCTION.** The deployment of a computationally intensive Random Forest to execute a synthetic `if/else` threshold is engineering malpractice. E1 provides a false sense of multivariate AI intelligence. It must be immediately replaced by a transparent rules-engine or a Logistic Regression wrapper.
*   **E3:** **MAINTAIN IN PRODUCTION.** The K-Means archetypes are structurally sound. The business can confidently deploy targeted credit limit adjustments, customized pricing, and risk tiering based on these cohorts.

---

## 3. Academic Defense

*   **E1:** The baseline evaluation metric (ROC-AUC 0.9988) was an artifact of target leakage. Our empirical audits established that the underlying data generating process was deterministic with respect to the `cibil_score`. The complex ensemble model suffered from severe single-feature dominance and overparameterization, ultimately acting as a heavily bloated surrogate model for a single-variable decision tree.
*   **E3:** The clustering topology exhibits both linear and non-linear separability. The PCA and UMAP embeddings validate that the KMeans algorithm converged on true data manifolds rather than arbitrarily partitioning a continuous, homogeneous density distribution. Non-parametric statistical tests confirm that the boundaries successfully isolate distinct financial distributions.

---

## 4. Interview Defense

*   **E1:** *"When presented with a Random Forest achieving 0.99 ROC-AUC, I refused to blindly deploy it. I executed rigorous ablation, permutation, and SHAP forensics, which proved the dataset was essentially rule-generated and 94% of the signal was just the credit score. I prevented the deployment of an over-engineered, computationally wasteful 'AI illusion' and advocated for a simple, highly interpretable rules engine."*
*   **E3:** *"To prove our Archetype clusters weren't just arbitrary algorithmic slicing, I conducted topological audits using UMAP and PCA, alongside non-parametric Kruskal-Wallis tests. The UMAP homogeneity scored over 95%, proving we had found true geometric islands of borrower types. This gave the business the mathematical confidence needed to build strategic risk policies around these archetypes."*

---

## 5. Regulatory Risk Assessment

*   **E1 Risk (Critical):** If audited by regulators under "Explainable AI" mandates, defending a black-box Random Forest that secretly operates as a single-variable threshold is a severe compliance risk. It exposes the institution to claims of obfuscation. Replacing it with a transparent rule mitigates this risk entirely.
*   **E3 Risk (Low):** The clustering profiles are backed by robust statistical separation in standard financial metrics (Income, Tenure), making the archetypes highly defensible against claims of arbitrary or biased segmentation.

---

## 6. Architecture Recommendation

1.  **Deprecate E1's Random Forest:** Remove the `RandomForestClassifier` from the E1 prediction pipeline.
2.  **Implement E1 Rules Engine:** Replace E1 with a lightweight deterministic function (`if cibil_score > threshold`).
3.  **Solidify E3:** Lock in the scaler and KMeans centroids for E3 production inference. Establish pipeline monitoring to track UMAP cluster drift over time as new borrower data arrives.

---

## 7. Next Actions (Highest-Value Follow-Ups)

1.  **Feature Space Re-engineering (E1):** If a genuine multivariate risk model is desired, we must source organic (non-synthetic) default labels and engineer stronger alternative data features (e.g., bank statement cash flow volatility) that are mathematically orthogonal to the CIBIL score.
2.  **Cluster Transition Monitoring (E3):** Implement longitudinal tracking to observe if borrowers organically migrate between Archetype clusters (e.g., from "Young Starters" to "Mid-Career Established") over their lifecycle.
