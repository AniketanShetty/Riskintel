# Change Log

## [2026-06-10] Person A Guardrails V1.1
- **Feature**: Enforced deterministic guardrails for Person A (Credit-Aware) borrowers inside `orchestrator.py`.
- **Feature**: Added `OVERRIDE_AGE_TERM_REJECTION`, `OVERRIDE_LTI_REJECTION`, and `FLAG_LOW_INCOME_REVIEW` audit signals.
- **Explainability**: Added explicit explanations `A-POLICY-002`, `A-POLICY-003`, and `A-POLICY-004` that override standard ML factor lists when a guardrail is tripped.
- **Tests**: Reached 318 passing tests with new adversarial coverage from `JUDGE_ATTACK_MATRIX_V2`.
