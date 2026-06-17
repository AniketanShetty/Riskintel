# PROJECT OVERVIEW

RiskIntel V2 is an implementation-ready, deterministic underwriting engine designed to eliminate manual business rules and subjectivity in lending to thin-file and undocumented borrowers. It orchestrates complex multi-stage pipelines (Person A and Person B) through strict mathematical ceilings, cyclic recovery algorithms, and cryptographically verified artifacts.

# CURRENT STATUS

**Phase 2 (Architecture & Specification) Complete.**
**Phase 1 (Persistence Layer) Complete.**
**Tests:** 9 / 9 passing in the persistence suite.
**Date:** 2026-06-14

# ARCHITECTURE

*   **Backend:** FastAPI
*   **Database Engine:** PostgreSQL (Authoritative Persistence)
*   **ORM:** SQLAlchemy 2.0
*   **Migration Framework:** Alembic
*   **Testing:** Pytest (Configured with isolated test database overrides decoupled from production `.ini`)
*   **Determinism:** Two identical payloads must mathematically produce the exact same final database state.

# DATABASE ARCHITECTURE

The schema relies on five core tables bound by strict relational integrity:
1.  `application_sessions` (Root record, contains verification fallback retry counters)
2.  `applicant_profiles` (Primary and co-applicants discriminated by flag)
3.  `verification_records` (Tamper-evident verification attempts)
4.  `optimization_results` (Immutable underwriting decisions, including `target_emi`)
5.  `state_transition_events` (Immutable append-only audit ledger)

**Architectural Standards:**
*   **UUID Generation:** Executed instantly in Python memory prior to metaclass mapping via SQLAlchemy `@event.listens_for(Base, 'init')` hooks to preserve MRO safety.
*   **Metadata Alignment:** SQLAlchemy models contain explicitly named `Index()` objects inside `__table_args__` to perfectly mirror physical migration schema, neutralizing `autogenerate` drift.
*   **Immutability:** Triggers enforcing append-only behaviors and auto-advancing timestamps are written in raw PostgreSQL inside the migration layer.

# PHASE 1 COMPLETION EVIDENCE

The foundational Phase 1 persistence layer has been physically verified by a 100% passing test suite targeting a real PostgreSQL instance:
*   Alembic `upgrade`/`downgrade` sequences succeed.
*   Alembic `autogenerate` drift detection proves zero schema delta.
*   UUID generation in memory is validated.
*   ORM overlap collision blocks Identity Map overwrites.
*   Check constraints and Unique constraints physically reject structural violations.
*   Audit ledger immutability trigger blocks raw SQL updates/deletes.
*   `updated_at` timestamp triggers advance via database native functions.

# TEST STATUS

**9 / 9 tests passing** (`tests/phase1/test_persistence_layer.py`).

# KNOWN RISKS

*   **CRITICAL: Alembic Trigger Blind Spot:** Alembic `autogenerate` cannot detect raw PostgreSQL `op.execute` triggers (e.g., the audit ledger). Rebuilding the database from ORM models via autogenerate will permanently delete constitutional protections. Bootstrapping must use `alembic upgrade head`.
*   **CRITICAL: Enum Constraint Drift Risk:** Hardcoded strings in `CheckConstraint` definitions won't automatically sync if Python enums change in Phase 2. Modifying enums requires manual Alembic scripts to drop/recreate the constraints.
*   **MEDIUM: SQLAlchemy Identity Map Caveats:** The `overlaps` discriminators on `ApplicantProfile` relationships (`primary_applicant` / `co_applicant`) will corrupt the in-memory map if an applicant's role is dynamically mutated. Rows must be deleted and reinserted to switch roles safely.
*   **MEDIUM: Parent `updated_at` Stagnation:** The `trg_set_updated_at` PostgreSQL trigger only tracks mutations on the root `application_sessions` row. Modifying child records does not automatically bump the parent timestamp.
*   **LOW: N+1 Query Loops:** Explicit `lazy` loading definitions are currently omitted. Collection relationships will default to synchronous queries if naively looped in Phase 2 APIs.

# ACTIVE ADRS

*   **ADR-023 (Cyclic Recovery):** If a user fails the Affordability Index, the system automatically stretches the tenure or reduces the loan amount and counter-proposes.
*   **ADR-024 (Product Catalog & Constants):** Defines strict system constants (24% APR, max 60mo), valid arrays, divisibility mappings, and pincode multipliers.
*   **ADR-025 (Reprompt Loop & Tamper Evidence):** Missing secondary contacts trigger `PENDING_REPROMPT`. Tamper hashes enforce cryptographic proof.
*   **ADR-027 (Optimization Mathematics):** Strict `decimal` context, ROUND_CEILING, step-wise tenure stretching, and algebraic PV inverse reduction.
*   **ADR-028 (Identity Matching):** Token Set Ratio fuzzy matching with `0.85` threshold.
*   **ADR-029 (Verification Failure Routing):** Bounded AA retries, fallback to Person B, and definition of `UNREACHABLE` physical state.
*   **ADR-030 (Temporal Anchors):** All chronological logic explicitly anchored to `created_at` (T0). Leap-year deterministic.

# DOCUMENTATION GOVERNANCE

**`PROJECT_STATE.md` is the canonical memory layer.**
Documentation is strictly subordinate to repository reality.

Future AI agents must adhere to the following workflow:

**Before any major implementation:**
1. Read `PROJECT_STATE.md`
2. Read `PRD.md`
3. Read active ADRs

**After any major implementation:**
1. Update `PROJECT_STATE.md`
2. Update ADRs if architecture changed
3. Record new risks, assumptions, and decisions

*General Principles:*
- Mark uncertainty as UNKNOWN.
- Prefer repository reality over documentation.

# NEXT PHASE

**Phase 2: Core Business Logic & Orchestration Integration**
Based on PRD and repository reality, the verified persistence layer and mathematically complete Phase 2 specifications are ready to support the state machine and logic engines. Phase 2 must construct:
1.  **The State Machine Orchestrator:** To govern the transitions from `INTAKE` → `TRIAGE` → `PENDING_VERIFICATION` → `OPTIMIZATION`.
2.  **The Verification Processor:** To execute the cryptographic artifact hashing (SHA-256) and safely destroy/replace categorical estimates with integer truths.
3.  **The Optimization Engine:** Implementing ADR-023, ADR-024, and ADR-027 to calculate deterministic offers.

# CHANGELOG

*   **2026-06-14:** Phase 2 specification declared 100% implementation-ready. Added `target_emi` and retry counters. Added ADRs 27, 28, 29, 30.
*   **2026-06-12:** Total rewrite of `PROJECT_STATE.md` to reflect repository reality. Purged outdated V1 / SQLite dependencies. Established Phase 1 PostgreSQL Persistence Layer as the certified baseline.