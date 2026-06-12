# RiskIntel V2: Technical Specification

## 1. Technology Stack
*   **Backend Application:** Python (FastAPI/Starlette recommended for async JSON payloads).
*   **Database Engine:** PostgreSQL (required for native Enum, Rule, and Check Constraint support).
*   **ORM Layer:** SQLAlchemy 2.x.
*   **Migrations:** Alembic.

## 2. Core Architectural Principles
*   **The Verification Freeze:** The Optimization engine is mathematically blocked from executing while the application is in `INTAKE` or `PENDING_VERIFICATION` states.
*   **Unified Persistence:** Primary and Co-Applicants share a single `applicant_profiles` table, mapped without `back_populates` to prevent Identity Map corruption (Resolved via Hostile Audit).
*   **Audit Immutability:** The `state_transition_events` table is physically protected by PostgreSQL `CREATE TRIGGER` logic to prevent `UPDATE` and `DELETE` commands.

## 3. External API Contracts
*Source: `API_CONTRACTS.md` & `ADR-023` & `ADR-025`*

| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/api/v2/intake_submission` | POST | Captures the 5-Question floor and executes Triage math. |
| `/api/v2/verification_complete` | POST | Webhook for Account Aggregator and Field Officer JSON. |
| `/api/v2/optimization_run` | POST | Internal trigger to unfreeze the DAG and execute the engine. |
| `/api/v2/counter_offer_response` | POST | Resolves the `NEARLY_READY` recovery loop (ACCEPT/REJECT). |
| `/api/v2/reprompt_submission` | POST | Fixes `MISSING_SECONDARY_CONTACT` to resume verification. |

## 4. Known Nullability Mismatches
*   **Co-Applicant Intake:** `API_CONTRACTS.md` currently lists `co_applicant_profile` fields as `Nullable`. **Repository Reality overrides this:** `ADR-021` and `ADR-023` mandate Co-Applicants be verified identically to Primary Applicants. The backend database correctly enforces `nullable=False` for national IDs and Pincodes. The API Contract is structurally stale and must be patched in Phase 2.
