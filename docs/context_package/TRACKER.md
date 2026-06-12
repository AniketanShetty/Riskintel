# RiskIntel V2: Implementation Tracker

| Module / Artifact | Phase | Status | Assignee | Notes / Audit Warnings |
| :--- | :--- | :--- | :--- | :--- |
| **Constants & Registries** | Phase 1 | `READY` | Backend Lead | ADR-024 Constants perfectly mapped. |
| **SQLAlchemy Models** | Phase 1 | `READY` | Backend Lead | `back_populates` bugs resolved. STI rejected. |
| **Alembic Migrations** | Phase 1 | `READY` | Backend Lead | `CHECK` constraints and Triggers required in raw SQL. |
| **Intake API** | Phase 2 | `PENDING` | - | Must patch `Nullable` tags from Co-Applicant payload (Stale Arch warning). |
| **Verification Webhook API** | Phase 2 | `PENDING` | - | - |
| **Counter-Offer API** | Phase 2 | `PENDING` | - | Implements ADR-023 cyclic resolution. |
| **Reprompt API** | Phase 2 | `PENDING` | - | Implements ADR-025 cyclic resolution. |
| **Normalization Engine** | Phase 3 | `PENDING` | - | Must implement ADR-022 canonical logic. |
| **Tamper-Evidence Layer** | Phase 3 | `PENDING` | - | Must implement ADR-025 SHA-256 checks. |
| **Scorecard Engine** | Phase 4 | `PENDING` | - | Uses `SYSTEM_BASE_INTEREST_RATE` (0.24). |
| **Optimization Engine** | Phase 4 | `PENDING` | - | Required Co-Applicant Algebra. |
| **Decision Engine** | Phase 4 | `PENDING` | - | Uses Divisibility Registry. |
| **State Machine DAG** | Phase 5 | `PENDING` | - | Enforces Verification Freeze. |
