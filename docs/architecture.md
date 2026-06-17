# Architecture

RiskIntel V2 is a robust asynchronous Python application architected to prioritize data integrity and chronological state safety.

## 1. Services & Frameworks

* **API Layer:** FastAPI (Python 3.13) providing asynchronous, high-throughput endpoints.
* **Database Layer:** PostgreSQL accessed via `SQLAlchemy` (async).
* **Schema Management:** `Alembic` governs the schema as the absolute authority, explicitly preventing uncontrolled ORM metadata drift.
* **Environment Configuration:** Handled via `pydantic-settings` to enforce a fail-fast startup if essential connection strings or cryptographic secrets are missing.

## 2. Finite State Machine (FSM)

The core orchestrator of RiskIntel is a Directed Acyclic Graph (DAG) State Machine. The FSM structurally prevents illegal business operations.

**State Flow:**
`INTAKE` ➔ `TRIAGE` ➔ `PENDING_VERIFICATION` ➔ `OPTIMIZATION` ➔ (`READY` | `NEARLY_READY` | `REJECTED`)

The FSM guarantees:
* External webhook events cannot affect the application before the `TRIAGE` gate passes.
* Optimization mathematics cannot execute until both Account Aggregator (AA) and Field Officer (FO) verifications are successfully received and cryptographically verified.

## 3. Database & Persistence

The application relies on a strictly relational PostgreSQL architecture.
* **`ApplicationSession`**: The root aggregate representing a loan application, storing its current state, requested loan amounts, and demographic data.
* **`ApplicantProfile`**: Stores canonical, normalized variables derived from raw intake and verified data.
* **`VerificationRecord`**: Auditable ledgers of data injected via webhooks.
* **`OptimizationResult`**: The finalized outputs of the mathematical engine, storing target EMIs, approved limits, and counter-offer variables.
* **`StateTransitionEvent`**: An immutable append-only ledger tracking every state change for total auditability.
* **`DeadLetterWebhook`**: Stores failing or out-of-order webhook payloads for diagnostic recovery, ensuring the primary transaction can cleanly rollback without losing debugging context.

## 4. Security

* **Internal Routing (API Key):** Endpoints utilized by internal orchestrators (e.g., `/apply`, `/triage`, `/optimize`) require a strict `X-API-Key` header matching the `RISKINTEL_API_KEY` environment variable.
* **External Webhooks (HMAC-SHA256):** Because third-party integrators push data to the `/webhooks/aa` and `/webhooks/fo` endpoints, these payloads are cryptographically signed.
  * The integrator computes an HMAC-SHA256 hash of `[X-Webhook-Timestamp].[Raw JSON Body]` using the shared `RISKINTEL_WEBHOOK_SECRET`.
  * RiskIntel verifies the signature, and verifies the timestamp to explicitly block replay attacks.

## 5. Recovery Loops

RiskIntel implements active cyclical recovery hooks to rescue failing loans:

1. **The PENDING_REPROMPT Loop:** If a Field Officer submits blurry photos or missing metadata, the application enters `PENDING_REPROMPT`. The orchestrator will hold the application indefinitely until a corrected FO webhook arrives, seamlessly cycling back into verification.
2. **The Counter-Offer (NEARLY_READY):** Instead of rejecting over-leveraged applicants, the mathematical engine algebraically calculates a counter-offer by stretching the loan term to the maximum bounds. The user is placed in `NEARLY_READY` and must explicitly `/accept` to proceed to `READY`.
3. **Co-Applicant Injection:** A user who fails verification strictly due to a "Thin File" (insufficient data depth) can ping the `/decision/{session_id}/coapplicant` endpoint to restart the verification flow utilizing a secondary guarantor's financial strength.
