# RiskIntel V2: Database Schema & Entity Map

## 1. Table Definitions
*Source: `IMPLEMENTATION_BACKLOG_V1.md` and Phase 1 Implementation Plan Hostile Audit Fixes*

| Table | Purpose | Corrected Architecture Constraints |
| :--- | :--- | :--- |
| `application_sessions` | Root state machine cursor. | `CHECK` constraints added to enforce exact string enums for `income_bracket` and `loan_purpose`. |
| `applicant_profiles` | Unified storage for Primary and Co-Applicant data. | Drops `back_populates` entirely to prevent Identity Map corruption. Requires `is_co_applicant` boolean. Composite Unique constraint guards against duplicate session roles. |
| `verification_records` | Webhook ingestion and Tamper-Evidence mapping. | Stores SHA-256 hashes immutably. Replaces categorical buckets with truth integers. |
| `optimization_results` | 1:1 Engine outputs. | Patched to include `livelihood_resilience_pass` (Boolean), overriding the stale `integer` requirement in the API contracts. |
| `state_transition_events`| Append-only event sourcing ledger. | Protected by native PostgreSQL `CREATE TRIGGER` to physically block `UPDATE` and `DELETE` commands. |

## 2. ORM Relationship Architecture (SQLAlchemy 2.x)
To support unified Applicant rows without STI (Single Table Inheritance) complexity, the relationships are explicitly defined as **Unidirectional**:
*   `session.primary_applicant` uses `overlaps="co_applicant"` and no `back_populates`.
*   `session.co_applicant` uses `overlaps="primary_applicant"` and no `back_populates`.
*   Memory synchronization is handled natively by the DB Foreign Key flushes.
