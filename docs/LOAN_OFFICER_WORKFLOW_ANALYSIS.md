# RiskIntel Task — Loan Officer Workflow Analysis

**Date:** 2026-06-07
**Focus:** Operational Workflow and Employee Utility

## Section 1. Current Manual Workflow

Before RiskIntel, a typical loan officer at an MFI or small bank follows a highly manual, subjective process.

### Bureau Borrower (Person A)
1. **Intake & Data Entry:** Collect application details.
2. **Bureau Pull:** Retrieve CIBIL score.
3. **Policy Mapping:** Manually look up the CIBIL score against the bank's risk-tier matrices.
4. **Capacity Calculation:** Calculate Debt-to-Income (DTI) and Fixed Obligation to Income Ratios.
5. **KYC & Fraud Review:** Verify identity documents.
6. **Underwriting Justification:** Write a summary justifying the risk level and recommended terms.
7. **Final Decision:** Approve, Reject, or Escalate.

### Thin-File Borrower (Person B)
1. **Intake & Interview:** Extensive interview to estimate informal cash flows, expenses, and living conditions.
2. **Business Categorization:** Try to fit the applicant's unique micro-enterprise into the bank's standard risk categories.
3. **Subjective Capacity Math:** Manually weigh housing type, family size, and estimated income to guess a risk level.
4. **Field Verification:** Visit the business and residence to verify existence and scale.
5. **Exception Routing:** Draft a custom justification for lending to a borrower with no credit history.
6. **KYC & Fraud Review:** Verify identity documents.
7. **Final Decision:** Approve, Reject, or Escalate (usually requires branch manager sign-off).

---

## Section 2. Mapping to RiskIntel

| Workflow Step | RiskIntel Impact | Reason |
|---|---|---|
| Intake & Data Entry | **Unchanged** | Data must still be collected and entered. |
| Bureau Pull | **Unchanged** | Bureau fetching happens outside RiskIntel. |
| Policy Mapping (Bureau) | **Eliminated** | RiskIntel instantly maps CIBIL to Risk Tier (P1-P4). |
| Business Categorization | **Eliminated** | RiskIntel standardizes free-text businesses into 6 clusters. |
| Capacity Math / Scoring | **Reduced** | RiskIntel computes a standardized 0-100 readiness score. |
| Underwriting Justification | **Reduced** | RiskIntel generates structured reports with explicit strengths/risks. |
| KYC & Fraud Review | **Unchanged** | RiskIntel does not verify identity. |
| Field Verification | **Unchanged** | Physical reality must still be verified by a human. |
| Final Decision | **Unchanged** | A human must still sign the approval. |

---

## Section 3. Engine Contributions

- **E2 (Risk Tier):** Eliminates the manual work of checking CIBIL scores against policy matrices. It instantly categorizes the risk and applies hard rejection overrides (P4) so the officer does not waste time reviewing guaranteed rejections.
- **E5 (Readiness Engine):** Reduces subjective mental math for thin-file borrowers. It replaces the loan officer's "gut feeling" about housing and family size with a standardized, reproducible 0-100 score and explicit component breakdowns.
- **E6 (Livelihood Engine):** Eliminates manual business categorization. It maps raw, messy applicant text into one of 6 predefined clusters instantly, removing ambiguity and standardizing the portfolio view.

---

## Section 4. Remaining Manual Work

RiskIntel is a decision-support system, not an autonomous agent. The following critical tasks remain entirely manual:
- **KYC Verification:** Ensuring the applicant is who they say they are.
- **Fraud Review:** Checking for forged documents or synthetic identities.
- **Document Review:** Comparing stated income against bank statements or utility bills.
- **Field Verification:** Physically visiting the home or business to confirm operations and assets.
- **Final Approval:** Taking legal and financial responsibility for the credit decision.

---

## Section 5. Dangerous Automation

RiskIntel must **NEVER** automate the following:

- **The Final Approval/Rejection Decision:** Credit decisions require human accountability. An algorithm cannot be held legally or ethically accountable for discriminatory lending or systemic portfolio defaults. 
- **Fraud/KYC Verification:** AI systems are vulnerable to adversarial inputs and hallucinations; identity verification requires deterministic, authoritative checks against government databases.
- **Policy Exceptions:** Deciding when to break a standard rule (e.g., approving a loan despite a low readiness score due to extenuating circumstances) requires human empathy, context, and managerial discretion that a rigid system cannot encode safely.

---

## Section 6. Loan Officer Decision Flow

```text
1. Application Received
      │
2. KYC & Fraud Check (Manual)
      │
3. RiskIntel API Call (Automated)
      ├── If Bureau: E2 Risk Tier assigned.
      └── If Thin-File: E6 Livelihood mapped, E5 Readiness scored.
      │
4. RiskIntel Generates Structured Report & Flags Overrides
      │
5. Loan Officer Reviews RiskIntel Report
      ├── If E2 = P4 or E5 = Not Ready (Policy Override):
      │       └── Fast-track to Reject / Request Info
      └── Else:
              └── Proceed to Verification
      │
6. Field & Document Verification (Manual)
      │
7. Final Decision (Manual: Approve / Reject / Escalate)
```

---

## Section 7. Quantifying Value

- **Minutes Saved:** Estimated **10-15 minutes per application**. RiskIntel eliminates the need to calculate manual ratios, categorize business types, and format the initial case summary.
- **Review Steps Removed:** **2 to 3 steps** (manual tier mapping, business classification, initial capacity arithmetic).
- **Consistency Gains:** **High**. RiskIntel ensures every thin-file borrower is scored using the exact same mathematical baseline, removing individual underwriter bias or "bad day" subjectivity.
- **Auditability Gains:** **High**. Every policy threshold, categorization, and override is permanently logged with a correlation ID, ending the era of undocumented "gut feeling" approvals.

---

## Section 8. Final Verdict

**Can RiskIntel honestly claim it "reduces manual review effort"?**

**Yes.**

- **How:** By automating the initial arithmetic of capacity scoring, standardizing unstructured inputs (business types), and generating a formatted, objective baseline report that flags immediate policy rejections.
- **By how much:** It removes approximately 10-15 minutes of initial assessment friction per case and standardizes the starting point for every review.
- **Under what limitations:** It does not, and cannot, replace field verification, document review, or the final human judgment required to originate a loan. It reduces the *friction* of the review, not the *responsibility* of the reviewer.
