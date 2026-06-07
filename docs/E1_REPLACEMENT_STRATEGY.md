# RiskIntel — E1 Replacement Strategy

**Date:** 2026-06-07
**Status:** Binding Strategic Directive

This document defines the strict requirements for replacing the disabled E1 Eligibility Engine. The previous iteration of E1 was downgraded and disabled due to synthetic labels, uncalibrated probabilities, out-of-distribution crashes, and unlicensed training data. 

Any rebuild of E1 must satisfy the following criteria before entering the RiskIntel codebase.

## 1. Target Label Replacement
The current synthetic "approved/rejected" rule-based labels must be abandoned. The replacement dataset must use a **real-world, observed financial outcome** as the target label. Acceptable targets include explicit delinquency markers (e.g., "90+ days past due within 12 months") or verified charge-off events. The model must predict the probability of default, not the probability of an underwriter's approval.

## 2. Required Data Properties
The dataset must:
- Accurately represent the target demographic (e.g., Indian retail and micro-enterprise borrowers), rather than foreign populations (e.g., the removed Czech/Russian Home Credit data).
- Contain a continuous and representative distribution of credit bureau scores to allow the model to learn a valid monotonic relationship.
- Include a sufficient volume of true positive and true negative real-world outcomes without artificial inflation.

## 3. License and Provenance Requirements
No dataset may enter the pipeline without passing strict governance gates:
- **Commercial License:** The data must have a verifiable, documented license permitting commercial use in a production lending system.
- **Provenance:** A complete `provenance.json` must be generated detailing the source URL, legal owner, geographic population, exact row/column counts, and SHA256 checksums.

## 4. Required Fairness Tests
The replacement model must pass a rigorous Disparate Impact audit to ensure it does not encode proxy discrimination. Specifically, the model must be tested against proxy variables for protected classes (e.g., age, geographic location, or proxy-income indicators).

## 5. Required Calibration Tests
The current model treats raw random-forest vote shares as probabilities, which is mathematically invalid. The replacement must:
- Use formal probability calibration (e.g., Isotonic Regression or Platt scaling via `CalibratedClassifierCV`).
- Prove that a predicted 10% probability of default mathematically aligns with an observed 10% default rate in a held-out test set (measured via Brier Score and Expected Calibration Error).
- **Enforce Monotonicity:** It must be mathematically impossible for a borrower with identical features but a *higher* credit score to receive a *lower* approval probability.

## 6. Drift and Out-of-Distribution (OOD) Protections
The previous E1 crashed when encountering 7 out of 17 standard CIBIL bands. The new engine must:
- Explicitly define the valid distribution boundaries for all continuous inputs.
- Implement an explicit OOD detection layer at the API boundary.
- Fail gracefully. If a borrower falls outside the calibrated range, the system must catch the anomaly, log it, and return a clean fallback requiring manual review, rather than raising an unhandled backend exception.

## 7. Acceptance Criteria for a Valid Replacement Model
A replacement E1 engine will only be approved by the Model Risk Committee if it delivers:
1. A commercially licensed, real-outcome dataset with a complete `provenance.json`.
2. Empirically calibrated probability outputs.
3. A proven monotonic relationship with core credit indicators.
4. Robust OOD handling that logs and gracefully defers out-of-bounds applicants.
5. A comprehensive Model Card detailing all of the above.

## 8. Fallback: What if no suitable licensed dataset exists?
**Do not rebuild E1.** 

If a legally defensible, real-outcome dataset cannot be sourced, the RiskIntel system must not attempt to fake a machine learning capability. E1 must remain completely disabled. The platform will continue to operate strictly and honestly as a deterministic decision-support system relying on the E2 Risk Tier policy engine and the E5 Readiness heuristic.
