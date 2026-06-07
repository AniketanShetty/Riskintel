# Minimum Viable RiskIntel (v1.1)

**Date:** 2026-06-07
**Status:** Frozen architecture definition

Minimum Viable RiskIntel is the smallest trustworthy configuration of the RiskIntel decision-support system, defined after the completion of the forensic audits.

## 1. What decisions does RiskIntel v1 actually make?

RiskIntel does not make autonomous credit decisions. It provides a set of structured, reproducible signals to a human loan officer. The specific decisions it outputs are:
- **Risk Tier Assignment:** Categorizes a bureau-scored borrower into one of four risk tiers (P1-P4) based on a deterministic policy threshold.
- **Readiness Scoring:** Computes a 0–100 heuristic score for thin-file (no bureau score) borrowers based on housing, infrastructure, financial health, household burden, and business viability.
- **Livelihood Classification:** Maps a thin-file borrower's business type into one of six deterministic categories using a fixed dictionary.
- **Explicit Thin-File Routing:** Explicitly identifies borrowers without a bureau score and routes them to the readiness pipeline or defers them to manual review rather than returning an unsupported eligibility prediction.

## 2. Which engine supports each decision?

- **Risk Tier Assignment:** Supported by **E2 (Risk Tier Engine)**.
- **Readiness Scoring:** Supported by **E5 (Readiness Engine)**.
- **Livelihood Classification:** Supported by **E6 (Livelihood Engine)**.
- **Explicit Thin-File Routing:** Supported by the core routing layer, enforcing the Thin-File Policy.

## 3. Engine Status

| Engine | Status | Reason |
|---|---|---|
| **E1 Eligibility** | **DISABLED** | Trained on synthetic-rule data, uncalibrated probabilities, fails on valid CIBIL inputs, non-monotonic. Not defensible. |
| **E2 Risk Tier** | **MANDATORY** | Defensible as a policy engine (not a learned model). |
| **E3 Archetype** | **REMOVED** | Broken 1-row cluster, fabricated labels, trained on wrong demographic population. |
| **E5 Readiness** | **MANDATORY** | Only system capable of defensibly scoring thin-file borrowers. Rule-based and deterministic. |
| **E6 Livelihood** | **MANDATORY** | Fully explainable deterministic lookup with an explicit `is_unclassified` fallback. |

## 4. What does the borrower see?

- **If they have a bureau score (Person A):** They see a risk tier (P1-P4) and an explicit message stating that the automated eligibility model is currently disabled pending data replacement and calibration. 
- **If they have no bureau score (Person B / Thin-File):** They see an explicit, plain-language notification that they are being assessed via a readiness score rather than a credit score. They see their readiness band, the component scores, and a set of educational (not financial) recommendations.
- **First-Time Borrowers in the Person A path:** They see a `THIN_FILE_NOT_SUPPORTED` message explaining that the system cannot score them without a bureau score, and they are routed to manual review. They are not silently rerouted.

## 5. What does the employee see?

- **Automated Case Reports:** Structured reports summarizing the applicant's inputs to reduce manual review.
- **Risk Tier and Readiness Band:** The specific outputs of E2, E5, and E6.
- **Explicit Overrides:** Clear flags when a policy override is applied (e.g., E2's P4 rejection override or E5's financial health floor breach).
- **Unclassified Flags:** An `is_unclassified` flag from E6 if the borrower's business type is not in the livelihood dictionary.
- **Audit Logging:** An audit trail for the application, ensuring no silent failures occur.

## 6. What must never be claimed about the system?

- **Do not claim RiskIntel is an "autonomous loan approval AI" or "ML credit decision maker."** It is a rule-based and threshold-based decision-support system.
- **Do not claim E2, E5, or E6 are machine learning models.** E2 is a threshold policy, E5 is a weighted heuristic, and E6 is a dictionary lookup.
- **Do not claim the system predicts default probability.** The system assigns risk tiers and readiness bands; it does not output a calibrated probability of default.
- **Do not claim E1 is in production.**

## 7. What is in scope for v1?

- Defensible, rule-based scoring for thin-file borrowers (E5).
- Deterministic, policy-based tiering for bureau-scored borrowers (E2).
- Deterministic business classification (E6).
- Explicit, transparent routing that does not silently mishandle missing bureau scores.
- Comprehensive audit logging for all requests.
- Complete data governance documentation (provenance, lineage, licensing, model cards).

## 8. What is explicitly out of scope for v1?

- Any use of the E1 Eligibility ML model.
- Any use of the E3 Borrower Archetype ML model.
- Calibrated probability outputs.
- Autonomous credit decisioning without a human in the loop.
- Any frontend UI development or discussion.

## 9. What is the next recovery phase?

The immediate next phase is pure **Data Governance and Documentation**:
1. Document the policy rationale for E2 thresholds and E5 weights via Model Cards.
2. Generate `provenance.json` for all production files.
3. Consolidate a central `LICENSE` inventory.
4. Establish a CI/CD pipeline with fairness, drift, and calibration monitoring gates.
5. Only after governance is complete: source a new, real-outcome dataset with a valid commercial license to begin rebuilding E1 from scratch.
