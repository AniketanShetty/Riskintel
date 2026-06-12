# Architectural Decision Records

## ADR-004: Freeze Person A Guardrail Thresholds
**Decision**: We have established hard thresholds for Person A Guardrails: Age + Term > 70, LTI > 6.0, and Income < 300,000 INR.
**Context**: Required to prevent impossible maturity ages and adversarial leverage ratios from passing purely on ML probability.
**Alternatives**: Using a continuous penalty function. Rejected because policy breaches must be deterministic rejections, not probabilities.
**Consequences**: The orchestrator now intercepts these edge cases, emitting explicit override flags (`OVERRIDE_AGE_TERM_REJECTION`, etc.) which E4 uses to explain the rejection definitively.
**Status**: Implemented (V1.1)

## ADR-005: Deterministic Policy Overrides for Person B
**Decision**: Establish hard policy bounds for Person B applicants: `OVERRIDE_E5_FLOOR_BREACH`, `OVERRIDE_EXTREME_DEBT` (LTI > 3.0), `FLAG_PURPOSE_MISMATCH` (capping score at 74), and `FLAG_LOW_INCOME_REVIEW` (income < 300,000 INR).
**Context**: Required to mitigate mathematical masking risks in the E5 weighted sum model, specifically regarding misaligned loan purposes, mathematically unserviceable debt relative to revenue, and critical financial health floors.
**Alternatives**: Altering the E5 mathematical weights. Rejected because changing weights would not guarantee fail-safe bounds and would disrupt historical testing baselines.
**Consequences**: The orchestrator now evaluates these deterministic rules post-E5, actively modifying `band` and `score` before handing off to E4 for explanation generation. This implements a fail-closed hierarchy prioritizing the highest risks first.
**Status**: Implemented (V1.1)
