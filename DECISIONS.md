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

## ADR-026: Persistence Layer & Alembic Migration Authority
**Decision**: 
1. PostgreSQL is established as authoritative persistence.
2. Alembic is adopted as the migration authority.
3. UUID generation is strictly standardized via SQLAlchemy `init` event hooks + column defaults.
4. Explicit `Index()` definitions must be physically declared in ORM `__table_args__` to eliminate metadata drift.
5. `PROJECT_STATE.md` is strictly designated as the canonical project memory layer.
**Context**: Required to shift from a V1 SQLite experimental persistence state to a production-ready, highly-constrained PostgreSQL schema that cleanly supports complex state machine transitions and audit ledgers.
**Consequences**: All persistence layer operations are now mathematically verifiable. Alembic drift alerts serve as a hard gate against implicit ORM metadata changes.
**Status**: Implemented (2026-06-12)
