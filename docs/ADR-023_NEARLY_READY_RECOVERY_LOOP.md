# ADR-023: NEARLY_READY Recovery Loop

## Context
The previous architectural iteration modeled the `NEARLY_READY` state as a terminal node, which created a cyclic state machine failure. If a borrower successfully arrived at `NEARLY_READY` and attempted to accept a counter-offer (e.g., a stretched 120-month tenure) or act on a coaching pathway (e.g., submitting a Co-Applicant), the system lacked explicit state transitions, routing rules, and API schemas to ingest their actions.

## Decision

We formally mandate a "Recovery Loop" for the `NEARLY_READY` state, converting it from a terminal node into a routing junction bounded by strict mathematical triggers. 

### 1. Legal Trigger Events

The following are the exactly 4 allowed events that can trigger an exit from `NEARLY_READY`:

*   **`user_submits_coapplicant`**: The borrower leverages the `POST /api/v2/intake_submission` Dual-Track schema to append a Co-Applicant to their session.
*   **`user_accepts_counter_offer`**: The borrower mathematically agrees to the engine's counter-offer (stretched tenure or reduced principal).
*   **`user_rejects_counter_offer`**: The borrower actively refuses the system's mathematically safe terms.
*   **`counter_offer_expired`**: The internal Time-to-Live (TTL) for the counter-offer safely elapses (implicitly defaulting to rejection to prevent stale risk exposure).

### 2. State Machine Transitions

The unidirectional DAG rule is formally overridden for the `NEARLY_READY` junction:

*   **To `PENDING_VERIFICATION`**: Executed explicitly when `user_submits_coapplicant` occurs. The system successfully cycles back to mathematically verify the Co-Applicant without losing the primary applicant's frozen verification baseline.
*   **To `READY`**: Executed explicitly when `user_accepts_counter_offer` occurs. The system successfully seals the contract terms.
*   **To `NOT_READY_YET`**: Executed explicitly when `user_rejects_counter_offer` OR `counter_offer_expired` occurs. This acts as a terminal failure lock.

### 3. API Contract Synchronization

To facilitate the exact resolution of the counter-offer events, a dedicated `POST /api/v2/counter_offer_response` API is minted. This endpoint formally maps the borrower's actions (`ACCEPT` or `REJECT`) into `READY` or `NOT_READY_YET` transitions.

To facilitate the Co-Applicant submission event, `co_applicant_profile` is formally appended to the `POST /api/v2/intake_submission` schema.
