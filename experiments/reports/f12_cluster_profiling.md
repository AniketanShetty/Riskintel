# E3 Archetype Cluster Profiling Audit

## Overview
This report profiles the RiskIntel Borrower Archetypes (E3) to determine if the clusters differ in statistically and financially meaningful ways. We employ Kruskal-Wallis H-tests to assess variance across non-parametric financial distributions and visualize the centroids via Radar charts.

## Kruskal-Wallis Test Results
| Feature | H-Statistic | p-value |
|---------|-------------|---------|
| NETMONTHLYINCOME | 3681.14 | 0.0000e+00 |
| AGE | 27234.31 | 0.0000e+00 |
| Time_With_Curr_Empr | 17499.86 | 0.0000e+00 |
| EDUCATION | 31495.45 | 0.0000e+00 |

## Statistical Profiling Verdict
**Verdict:** PASS

### Findings
The critical financial variables (`NETMONTHLYINCOME` and `Time_With_Curr_Empr`) exhibit extraordinarily low p-values (p < 0.01) in the Kruskal-Wallis test, indicating that the distributions are statistically distinct across clusters. The radar profiles confirm that the centroids exist in substantially different regions of the feature space.

### Interpretation
**Do these clusters provide actionable borrower segmentation?** Yes. The archetypes are built on robust statistical differences in core financial capacity and stability metrics.
**Are they statistically indistinguishable?** No. They are highly distinguishable.

### Production Implications
The clustering algorithm has successfully identified financially meaningful cohorts. The business can confidently deploy targeted risk strategies (e.g., differential pricing, tailored credit limits) based on these archetypes.
