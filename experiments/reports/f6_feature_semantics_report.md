# Feature Semantics Audit Report

## Objective
A machine learning model can perform flawlessly on mathematical tests (like cross-validation) and still be entirely useless in production if its features contain "semantic leakage." 

Semantic Leakage occurs when a feature physically exists in the database, but represents an event that happens **after** the loan decision is made (e.g., "Days in Arrears", "Recovery Amount", or "Dynamic Bureau Score").

## Required Analysis per Feature

Every feature in the `eligibility_data.csv` must be rigorously cross-examined against the production data-generating process. The automated script (`f6_feature_semantics.py`) provides the baseline Knowledge Base (KB) mapping.

For any feature flagged as **Unknown** or **High Risk**, the Auditor must answer:
1. **What does it measure?** (e.g., Does 'cibil_score' mean the score at the time of application, or the score today?)
2. **When does it become available?** (e.g., Does this field populate via a cron-job 30 days after the loan originates?)
3. **Could it leak future outcomes?** (e.g., If the loan defaults, does a downstream system overwrite this column?)

## Red Flags

If any of the following features exist in the training matrix `X`, the model is fundamentally corrupted:

* **Post-Loan Information:** `months_since_last_payment`, `current_balance`
* **Repayment Outcomes:** `total_principal_paid`, `late_fees_accrued`
* **Recovery Information:** `collection_agency_assigned`, `recovery_value`
* **Default-Derived Information:** `dynamic_cibil_score`, `internal_behavioral_score`

## Final Verdict Criteria

Based on the output of `metrics/f6_feature_semantics.csv`, a final verdict must be issued:

* **SAFE:** All features are categorically proven to be mathematically frozen at the exact millisecond the applicant hits "Submit Application."
* **REVIEW_REQUIRED:** The dataset contains poorly named columns (e.g., `score_v2`) where the exact generation timestamp is unknown and requires database engineer verification.
* **HIGH_LEAKAGE_RISK:** The dataset explicitly contains post-decision metrics, or dynamic metrics (like CIBIL) that were pulled retroactively.

---
**Verdict Result:** [To be populated after execution]
