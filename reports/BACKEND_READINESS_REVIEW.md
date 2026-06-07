# RiskIntel Backend Readiness Review

**Role:** Principal Systems Architect  
**Status:** Pre-Frontend Development Audit  

## Overview
The RiskIntel backend architecture has been heavily documented and mathematically verified at the component level. However, a system is not production-ready until the *integration* of those components is proven. This document identifies the unvalidated assumptions across all six critical layers that must be resolved before frontend engineering begins.

---

## 1. CRITICAL Risk Level

### Audit Layer: Asynchronous Fail-Closed Mechanism
*   **Unvalidated Assumption:** If the Orchestrator fails to publish an audit event to Kafka, it will successfully abort the transaction and prevent the API from returning an underwriting decision to the frontend.
*   **Why it Matters:** A "Fail Open" scenario (where a user is approved/rejected but no audit log is written) is a catastrophic violation of FCRA/ECOA regulations. We lose all ability to defend an Adverse Action.
*   **Validation Required:** We must prove that the Orchestrator intercepts Kafka producer timeouts and forces a PostgreSQL rollback.
*   **Recommended Test:** `chaos_test_audit_partition()` - Sever network access to the Kafka broker. Push an assessment payload. Assert the API returns `500 Internal Server Error` and that the `assessments` table shows `status = FAILED_PROCESSING`.

### ML Layer: Serialization Schema Parity
*   **Unvalidated Assumption:** The JSON payload validated by the API Gateway perfectly matches the strict `dtype` arrays expected by the deserialized `scikit-learn` K-Means model in Python.
*   **Why it Matters:** A single `null` value, unexpected string casing, or an unmapped categorical enum will cause the ML Inference Service to throw a `ValueError` or `TypeError`, crashing the DAG.
*   **Validation Required:** End-to-end type coercion proof between the API JSON boundary and the matrix multiplication layer.
*   **Recommended Test:** `test_ml_contract_fuzzing()` - Fire thousands of fuzzed JSON payloads (edge cases, missing fields, maximum integer bounds) at the Orchestrator. Assert that the ML Inference Service explicitly intercepts all bad data via Pydantic *before* it reaches the model's `predict()` method.

---

## 2. HIGH Risk Level

### API Layer: Hybrid Synchronous Latency
*   **Unvalidated Assumption:** The Orchestrator can execute E1 -> E2 -> E3 -> E4 -> E5 sequentially within the synchronous 500ms p95 frontend budget.
*   **Why it Matters:** If the ML Inference hops (E3, E4) introduce severe latency or cold-start pauses, the frontend will experience synchronous API timeouts, resulting in a broken user experience.
*   **Validation Required:** E2E load testing of the exact sequential DAG.
*   **Recommended Test:** `load_test_dag_execution()` - Using `k6`, sustain 100 Requests Per Second against the `POST /v1/assess` endpoint. Validate that the Orchestrator p95 stays < 500ms and that Python GIL contention does not throttle the ML service.

### Database Layer: Connection Exhaustion
*   **Unvalidated Assumption:** The Orchestrator and the backend microservices will not exhaust the PostgreSQL connection pool during a traffic surge.
*   **Why it Matters:** A single application triggers writes to `assessments`, `eligibility_results`, `archetype_results`, etc. Without connection multiplexing, a spike in API traffic will cause DB connection timeouts, crashing the entire platform.
*   **Validation Required:** Validation that `PgBouncer` (or equivalent pooling) is correctly managing transaction-level locking and queueing.
*   **Recommended Test:** `stress_test_connection_pool()` - Launch 500 concurrent Orchestrator executions. Assert that 0 database connections drop and maximum row-lock wait times remain under 50ms.

---

## 3. MEDIUM Risk Level

### Security Layer: PII Deduplication Collision
*   **Unvalidated Assumption:** The salted `tax_id_hash` (used for SSN/PAN masking) is sufficient for identity deduplication across the `applicants` table.
*   **Why it Matters:** If the salt strategy is flawed or rotates unexpectedly, the same applicant could apply twice, bypassing chronological lockout rules. If it is too weak, it becomes susceptible to rainbow table attacks.
*   **Validation Required:** Cryptographic validation of the salting logic and unique index enforcement.
*   **Recommended Test:** `test_hash_collision_prevention()` - Submit two applications with the exact same SSN. Assert the `tax_id_hash` matches identically, triggering the database `UNIQUE` constraint and returning a `409 Conflict` to the frontend.

### Deployment Layer: Artifact Rollback Integrity
*   **Unvalidated Assumption:** If a deployed ML Model (E3) exhibits extreme distribution drift in production, rolling back the `model_registry` database flag will cleanly revert the Inference Service to the previous version.
*   **Why it Matters:** If bad models cannot be instantly rolled back, faulty underwriting decisions will bleed into the loan book.
*   **Validation Required:** Proving that the ML Inference Service dynamically polls the registry and flushes its RAM without requiring a full Kubernetes pod restart.
*   **Recommended Test:** `test_dynamic_model_reload()` - While processing traffic, flip the `is_active` flag in the `model_registry` from version 2.0 back to 1.0. Assert that the next API response reflects version 1.0 output with zero downtime.

---

## 4. LOW Risk Level

### Data Layer: JSONB Query Performance
*   **Unvalidated Assumption:** The GIN index on `assessments.input_features` will provide sufficient analytical read performance for internal data science teams.
*   **Why it Matters:** As the database grows to millions of rows, complex JSON extractions could slow down reporting dashboards or cause high CPU utilization on the database cluster.
*   **Validation Required:** Query execution plan analysis on high-volume tables.
*   **Recommended Test:** `test_gin_index_utilization()` - Insert 1 million mock assessments. Run an `EXPLAIN ANALYZE` query looking for specific nested financial parameters and verify that the database engine utilizes the GIN index rather than falling back to a sequential scan.
