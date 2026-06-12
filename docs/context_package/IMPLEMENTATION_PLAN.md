# RiskIntel V2: Implementation Plan

## Phase 1: Persistence Skeleton (Corrected)
1.  Initialize standard constants (`config/constants.py`) matching ADR-024.
2.  Initialize exhaustive Enums (`models/enums.py`).
3.  Deploy `Base` ORM models dropping `back_populates` for bidirectional applicant profiles.
4.  Generate Alembic Migration `001_v2_init.py` with explicit raw SQL `CHECK` constraints, `UNIQUE` constraints, and Trigger functions.

## Phase 2: Application Interfaces
1.  Implement `api_intake` capturing the 5-question floor.
2.  Implement `api_verification` webhook listener.
3.  Implement `api_counter_offer` (ACCEPT/REJECT).
4.  Implement `api_reprompt` (Secondary Contact).

## Phase 3: Normalization & Ingestion Layer
1.  Code the Canonical Normalization engine (ADR-022 Person A/B bridge).
2.  Code the Tamper-Evidence cryptographic layer (ADR-025 SHA-256 matching).

## Phase 4: Core Execution Engines
1.  **Scorecard Engine:** Implements `PMT`, Triage Math, and Pincode Tier matching.
2.  **Optimization Engine:** Implements Tenure Stretching, Amount Reduction, and Co-Applicant Reverse Algebra.
3.  **Decision Engine:** Evaluates outputs against the Divisibility Registry and `livelihood_resilience_pass`.

## Phase 5: Orchestration
1.  **State Machine:** Wires the components to enforce the Verification Freeze and forbidden transitions.

## Phase 6 & 7: Polish
1.  Error handling envelopes, Audit log population.
2.  Execution of the `STATE_TRANSITION_TEST_MATRIX.md`.
