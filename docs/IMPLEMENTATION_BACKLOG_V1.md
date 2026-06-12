# RiskIntel V2 Implementation Backlog

## PHASE 1: Data Persistence

### WP 1.1: Database Schema & Migrations
*   **Module Name**: `persistence_layer`
*   **Purpose**: Establish the strict relational mapping for application sessions, applicant profiles (Primary/Co-Applicant), normalized verification payloads, and state transition history.
*   **Dependencies**: ADR-024 (Enums & Constants).
*   **Files To Create**: `db/schema.sql`, `db/migrations/v2_init.sql`, `models/session.py`, `models/applicant.py`
*   **Files To Modify**: None.
*   **Acceptance Criteria**: Database constraints explicitly reject non-whitelisted enums (`income_bracket`, `loan_purpose`) and bounds before the application logic runs.
*   **Unit Tests Required**: Model instantiation, field boundary checks.
*   **Integration Tests Required**: Migration rollback safety, foreign key cascade behaviors.
*   **Estimated Complexity**: Medium

---

## PHASE 2: API Endpoints

### WP 2.1: Intake API
*   **Module Name**: `api_intake`
*   **Purpose**: Implement `POST /api/v2/intake_submission` to capture the Universal 5-Question Floor and strictly route to Triage.
*   **Dependencies**: Database Schema (WP 1.1).
*   **Files To Create**: `api/intake.py`, `schemas/intake_schema.py`
*   **Files To Modify**: `api/routes.py`
*   **Acceptance Criteria**: Payload strictly adheres to defined arrays. Nullable boundaries for `co_applicant_profile` are respected.
*   **Unit Tests Required**: JSON schema validation (Valid payloads, out-of-bounds payloads).
*   **Integration Tests Required**: HTTP 400 Bad Request on invalid enums; HTTP 201 on success.
*   **Estimated Complexity**: Low

### WP 2.2: Verification Webhook API
*   **Module Name**: `api_verification`
*   **Purpose**: Implement `POST /api/v2/verification_complete` to ingest Account Aggregator and Field Officer payloads.
*   **Dependencies**: Database Schema (WP 1.1).
*   **Files To Create**: `api/verification.py`, `schemas/verification_schema.py`
*   **Files To Modify**: `api/routes.py`
*   **Acceptance Criteria**: Ingests multi-track arrays and successfully saves hashes.
*   **Unit Tests Required**: Payload parsing and type checking.
*   **Integration Tests Required**: Secure ingestion and logging.
*   **Estimated Complexity**: Low

### WP 2.3: Counter-Offer API
*   **Module Name**: `api_counter_offer`
*   **Purpose**: Implement `POST /api/v2/counter_offer_response` to mathematically resolve the `NEARLY_READY` recovery loop.
*   **Dependencies**: WP 1.1.
*   **Files To Create**: `api/counter_offer.py`, `schemas/counter_offer_schema.py`
*   **Files To Modify**: `api/routes.py`
*   **Acceptance Criteria**: Accepts only ACCEPT or REJECT boolean logic natively.
*   **Unit Tests Required**: Schema validation for actions.
*   **Integration Tests Required**: End-to-end payload routing.
*   **Estimated Complexity**: Low

### WP 2.4: Reprompt API
*   **Module Name**: `api_reprompt`
*   **Purpose**: Implement `POST /api/v2/reprompt_submission` to resume the verification freeze on missing secondary contacts.
*   **Dependencies**: WP 1.1.
*   **Files To Create**: `api/reprompt.py`, `schemas/reprompt_schema.py`
*   **Files To Modify**: `api/routes.py`
*   **Acceptance Criteria**: Updates session with corrected secondary contact.
*   **Unit Tests Required**: Reprompt enum matching.
*   **Integration Tests Required**: Successful update of the target database row.
*   **Estimated Complexity**: Low

---

## PHASE 3: Normalization & Ingestion

### WP 3.1: Canonical Normalization Layer
*   **Module Name**: `canonical_layer`
*   **Purpose**: Implement ADR-022 and ADR-025 normalization logic bridging Person A/B payloads into unified variables.
*   **Dependencies**: Verification API (WP 2.2).
*   **Files To Create**: `engines/normalization.py`
*   **Files To Modify**: None.
*   **Acceptance Criteria**: Accurately computes `canonical_verified_income`, `canonical_vintage_months`, `canonical_verification_pass`, and `co_app_canonical_verification_pass`.
*   **Unit Tests Required**: Date-diff precision tests, verification logic truth tables.
*   **Integration Tests Required**: Full pass of Person A payload vs Person B payload producing identical shapes.
*   **Estimated Complexity**: High

### WP 3.2: Bureau & Tamper Evidence Layer
*   **Module Name**: `security_ingestion_layer`
*   **Purpose**: Ingest bureau constraints and execute ADR-025 cryptographic hashes.
*   **Dependencies**: Canonical Normalization (WP 3.1).
*   **Files To Create**: `engines/cryptography.py`, `engines/bureau.py`
*   **Files To Modify**: None.
*   **Acceptance Criteria**: Generates `tamper_evidence_pass` safely.
*   **Unit Tests Required**: SHA-256 matching logic.
*   **Integration Tests Required**: Mismatched hash rejection.
*   **Estimated Complexity**: Medium

---

## PHASE 4: Core Execution Engines

### WP 4.1: Scorecard Engine
*   **Module Name**: `scorecard_engine`
*   **Purpose**: Calculate Triage Math, Affordability Capacity, and Minimum Product EMI.
*   **Dependencies**: ADR-024 Constants.
*   **Files To Create**: `engines/scorecard.py`, `config/constants.py`, `registries/pincode_registry.csv`
*   **Files To Modify**: None.
*   **Acceptance Criteria**: Implements PMT formula precisely using `SYSTEM_BASE_INTEREST_RATE`. Maps geographic risk natively via the Pincode registry.
*   **Unit Tests Required**: PMT computation exactness, strict `MIN()` limits, Pincode fallback to Tier 1 logic.
*   **Integration Tests Required**: Engine instantiation sequence.
*   **Estimated Complexity**: High

### WP 4.2: Optimization Engine
*   **Module Name**: `optimization_engine`
*   **Purpose**: Compute exact target EMI, execute the Tenure Stretch lever, the Amount Reduction lever, and the Co-Applicant Reverse Algebra.
*   **Dependencies**: Scorecard Engine (WP 4.1).
*   **Files To Create**: `engines/optimization.py`
*   **Files To Modify**: None.
*   **Acceptance Criteria**: Never executes if verification is incomplete. Successfully calculates `required_coapplicant_income_baseline`.
*   **Unit Tests Required**: Reverse-algebra proofs, `FLOOR` bounds.
*   **Integration Tests Required**: Safe bounds limiting (`SYSTEM_MAX_TENURE`).
*   **Estimated Complexity**: High

### WP 4.3: Decision Table Engine
*   **Module Name**: `decision_engine`
*   **Purpose**: Act as the final gate routing engine evaluations to literal State Machine triggers.
*   **Dependencies**: Scorecard Engine, Optimization Engine, Tamper Evidence Layer.
*   **Files To Create**: `engines/decision.py`, `registries/divisibility_registry.py`
*   **Files To Modify**: None.
*   **Acceptance Criteria**: Translates variables into `READY`, `NEARLY_READY`, or `NOT_READY_YET`. Applies Divisibility constraints.
*   **Unit Tests Required**: Truth tables for Divisible vs Indivisible fallback routes.
*   **Integration Tests Required**: Tamper evidence hard failure routing.
*   **Estimated Complexity**: Medium

---

## PHASE 5: Orchestration

### WP 5.1: State Machine Engine
*   **Module Name**: `state_machine`
*   **Purpose**: Enforce the unidirectional DAG and manage the cyclic exceptions (`NEARLY_READY`, `PENDING_REPROMPT`).
*   **Dependencies**: All APIs (Phase 2), Decision Engine (WP 4.3).
*   **Files To Create**: `orchestrator/state_machine.py`, `orchestrator/transitions.py`
*   **Files To Modify**: `api/intake.py` (wiring)
*   **Acceptance Criteria**: Strictly enforces forbidden transitions (e.g., locking `OPTIMIZATION` while `PENDING_VERIFICATION`).
*   **Unit Tests Required**: State entry/exit assertions.
*   **Integration Tests Required**: Forbidden state exception throwing.
*   **Estimated Complexity**: High

---

## PHASE 6: Platform Systems

### WP 6.1: Audit & Observability
*   **Module Name**: `telemetry_layer`
*   **Purpose**: Log explicit inputs and outputs for compliance tracking.
*   **Dependencies**: State Machine Engine.
*   **Files To Create**: `utils/logger.py`, `utils/audit.py`
*   **Files To Modify**: All engines.
*   **Acceptance Criteria**: Emits secure, structured JSON logs on every state transition.
*   **Unit Tests Required**: Log format validation.
*   **Integration Tests Required**: I/O throughput testing.
*   **Estimated Complexity**: Low

### WP 6.2: Error Handling
*   **Module Name**: `error_layer`
*   **Purpose**: Formalize API exception envelopes.
*   **Dependencies**: API Endpoints (Phase 2).
*   **Files To Create**: `api/exceptions.py`, `api/middleware.py`
*   **Files To Modify**: All API routes.
*   **Acceptance Criteria**: Captures `400 Bad Request`, `403 Forbidden` (Verification Freeze), and `422 Unprocessable Entity` efficiently.
*   **Unit Tests Required**: Middleware trap assertions.
*   **Integration Tests Required**: Error response shape compliance.
*   **Estimated Complexity**: Low

---

## PHASE 7: Verification Suite

### WP 7.1: Matrix Testing
*   **Module Name**: `qa_suite`
*   **Purpose**: Execute the `STATE_TRANSITION_TEST_MATRIX.md` as CI/CD automated tests.
*   **Dependencies**: Entire system (Phases 1-6).
*   **Files To Create**: `tests/test_matrix.py`, `tests/test_e2e_scenarios.py`
*   **Files To Modify**: None.
*   **Acceptance Criteria**: 100% pass rate on defined constraints.
*   **Unit Tests Required**: N/A
*   **Integration Tests Required**: N/A
*   **End-to-End Tests Required**: Full application lifecycle mocking.
*   **Estimated Complexity**: High
