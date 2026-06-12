# PERSON A GUARDRAILS V2 (Design Document)

## 1. Problem Statement
RiskIntel's V1.0 architecture successfully delegates probabilistic risk to a machine learning engine (E1) and deterministic credit rules to a risk tier engine (E2). However, relying entirely on ML for loan affordability and biological/legal constraints exposes the system to extreme adversarial attacks and real-world regulatory violations.

Specifically, the system suffers from:
* **DTI (Debt-to-Income) / LTI Blindness:** The model may approve an applicant requesting a 100M INR loan on a 1K INR income if their CIBIL score is high enough.
* **Age-Term Blindness:** The model may approve a 90-year-old applicant for a 20-year mortgage because the ML inference was not explicitly trained on mortality-bound maturity limits.
* **Minimum-Income Concerns:** The model may approve loans to destitute borrowers living below the subsistence line, introducing severe predatory lending risks.

## 2. Existing System Architecture
The current decision flow for a Person A applicant operates as follows:

```
[Request]
   │
   ▼
[Routing] ──> Determines applicant is Person A
   │
   ├──> [E1: Eligibility Engine]  (ML Probabilities & Bias)
   ├──> [E2: Risk Tier Engine]    (CIBIL mapping to P1-P4)
   └──> [E3: Archetype Engine]    (Demographic clustering)
   │
   ▼
[Orchestrator Conflict Resolution]
   │    (Currently only contains the P4 Override: If E2 == P4 and E1 == Positive -> Force "Unlikely")
   ▼
[E4: Recommendation Engine]
   │    (Generates explainability rules based on verdicts and audit flags)
   ▼
[Audit Logging & Response]
```

## 3. Candidate Guardrails

### A. Age-Maturity Guardrail
* **Rationale:** A loan must realistically amortize during the borrower's income-generating lifespan.
* **Banking Justification:** Standard retail banks enforce a maximum maturity age (usually 65-70 years) to mitigate mortality risk.
* **Fairness Considerations:** Highly objective. Applies equally across all protected classes as a biological/legal absolute.
* **False Positive Risks:** May reject healthy, high-net-worth elderly applicants seeking liquidity against capital assets.
* **False Negative Risks:** Setting the threshold too high (e.g., 85) effectively nullifies the protection for long-term (20-year) mortgages.

### B. Loan-To-Income (LTI) Guardrail
* **Rationale:** The requested loan principal must not severely outpace the borrower's annual earning capacity.
* **Banking Justification:** Ensures Equated Monthly Installments (EMIs) remain a manageable percentage of the borrower's monthly cash flow.
* **Fairness Considerations:** Income-based checks are standard but can inadvertently disadvantage younger borrowers. Must be paired with a generous ceiling.
* **False Positive Risks:** High rejection risk for asset-rich, income-poor individuals (e.g., retirees, complex business owners). 
* **False Negative Risks:** A high ceiling allows borderline unaffordable loans to pass through to ML approval.

### C. Low-Income Review Flag
* **Rationale:** Borrowers living below the poverty or subsistence line require special intervention, regardless of credit history.
* **Banking Justification:** Prevents automated predatory lending.
* **Fairness Considerations:** Protects highly vulnerable demographics from entering automated debt spirals.
* **False Positive Risks:** May trigger manual review for individuals who have undocumented cash-based income not captured in the raw dataset.
* **False Negative Risks:** None. This is a review flag, not a hard rejection.

## 4. Open Questions & Threshold Options
*(Thresholds remain unfrozen pending business stakeholder alignment)*

1. **Age-Maturity Options:**
   * Option A: `Age + Loan_Term > 65` (Aggressive, standard salaried limit)
   * Option B: `Age + Loan_Term > 70` (Standard, accounts for self-employed)
   * Option C: `Age + Loan_Term > 75` (Generous)

2. **LTI Options:**
   * Option A: `LTI > 4.5x` (Strict affordability)
   * Option B: `LTI > 6.0x` (Generous, acts only as an anti-adversarial safety net)
   * Option C: `LTI > 8.0x` (Extremely loose)

3. **Low-Income Options:**
   * Option A: `Income < 250,000 INR` (Extreme poverty line)
   * Option B: `Income < 300,000 INR` (Standard urban subsistence)

## 5. Architecture Options

### Option A: Orchestrator Overrides (Inline)
Implement the guardrails inside `orchestrator.py`, immediately following the existing `E2_P4_REJECTION` logic.
* **Complexity:** Low. Reuses existing `policy_override_flags` array.
* **Maintainability:** Medium. `orchestrator.py` could become bloated if rules exceed 20+.
* **Explainability:** High. Directly translates to `audit.policy_override_flags` which E4 natively consumes.
* **Auditability:** High. Handled by existing fail-closed SQLite logging.

### Option B: Dedicated E7 Guardrails Engine
Create a new `backend/app/engines/guardrails/guardrails_engine.py` and invoke it alongside E1-E3.
* **Complexity:** High. Requires updating frozen API schema contracts, `output_contracts.md`, and routing logic.
* **Maintainability:** High. Cleanly isolates deterministic rules away from orchestration logic.
* **Explainability:** Medium. E4 would need to be rewritten to ingest a new `guardrails_res` dictionary.
* **Auditability:** High.

## 6. Final Recommendation

**Option A (Orchestrator Overrides) is strongly recommended.** 

The RiskIntel API operates under a strict SSOT and frozen output contract paradigm (`output_contracts.md`). Introducing an entirely new engine (Option B) breaks API compatibility, requires massive changes to the frontend display schemas, and fractures the existing `policy_override_flags` paradigm. 

By inserting these three mathematical checks directly into the Orchestrator's Conflict Resolution block, we achieve 100% of the safety goals with 0% API disruption, while perfectly preserving the ML invariant.
