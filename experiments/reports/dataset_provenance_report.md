# RiskIntel Dataset Provenance Audit

> [!CAUTION]
> A machine learning model cannot be trusted if the data generating process is unknown. This audit evaluates the operational integrity and lineage of the raw data before modeling begins.

---

## 1. Investigation Checklist

- [ ] **Original Source Verification:** Is there an exact internal DB query, API endpoint, or external vendor link that produced the raw CSV?
- [ ] **Temporal Coverage:** What are the exact start and end dates of the records? Are they continuous?
- [ ] **Target Generation Logic:** Was `loan_status` populated by an underwriter, an automated legacy rule, or a retroactive default flag?
- [ ] **Feature Lineage:** Did all features exist *at the moment of application*, or were some appended post-approval?
- [ ] **Synthetic Indicators:** Does the dataset display perfectly balanced classes, lack of missing values, or artificially smooth integer boundaries?

---

## 2. Evidence Collection Template

| Provenance Attribute | Investigator Findings | Verification Artifact |
| :--- | :--- | :--- |
| **Data Sponsor / Owner** | [Enter Name] | Email / Slack Log |
| **Extraction Query/Script** | [Enter Path] | `sql/extract_loans.sql` |
| **Data Dictionary** | [Yes/No] | Link to Confluence |
| **Temporal Range** | [Start] - [End] | DB Timestamp check |

---

## 3. Red-Flag Indicators (Synthetic/Leakage)

1. **The "Perfect Integrity" Flag:** Real financial datasets are messy. If `f0_missingness.py` reports 0 missing values across 20+ columns without explicit imputation logic, the data is likely synthetic or heavily pre-sanitized.
2. **Benford's Law Violation:** If continuous fields like `annual_income` strictly disobey Benford's Law (leading digits distribution), they were likely generated via `np.random.uniform()` rather than organic human entry.
3. **The "Time-Travel" Flag:** If features like `cibil_score` are refreshed via a live API, extracting the *current* score to predict a *past* loan approval is fatal time-travel leakage.

---

## 4. STOP WORK Conditions

Halt all ML Validation immediately if:
* **Provenance Unknown:** No engineer or business unit can definitively supply the SQL query or vendor contract that generated the raw data.
* **Target Ambiguity:** The exact definition of `loan_status` (e.g., "Approved by underwriter" vs "Approved but defaulted 3 months later") is undocumented.

---

## 5. Interview-Defense Talking Points

*"While the team was eager to optimize the Random Forest, I forced a hard stop to conduct a Provenance Audit. I understand that the most catastrophic failures in ML happen before the data even enters Python. By verifying the exact SQL query and temporal boundaries, I ensured we weren't building an illegal 'time-travel' model or overfitting to synthetic vendor data."*
