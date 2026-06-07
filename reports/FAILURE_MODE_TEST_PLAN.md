# RiskIntel Backend Failure-Mode Test Plan

**Role:** Principal Backend Reliability Engineer  
**Status:** Architecture Specification  

## Overview
RiskIntel operates under strict regulatory constraints (FCRA, ECOA) which mandate that all underwriting decisions must be explicitly explainable and backed by an immutable audit trail. Consequently, the system must never "Fail Open" (e.g., approving an application without logging the exact rules and models used). The architecture must strictly enforce a **"Fail Closed"** paradigm across all microservices and persistence layers.

This document outlines the chaotic failure scenarios that must be simulated and validated before production deployment.

---

## 1. Database Unavailable
The primary PostgreSQL instance goes offline entirely (e.g., node crash, EBS volume failure).

*   **Expected System Behavior:** The Orchestrator cannot read assessment states or insert new applications. The application fails closed immediately.
*   **HTTP Response:** `503 Service Unavailable`.
*   **Audit Implications:** No audit log can be written for the incoming request.
*   **Regulatory Implications:** None, provided the applicant receives a generic "System Error, Please Try Again" message rather than a silent rejection. No underwriting decision was made, therefore no Adverse Action notice is required.
*   **Recovery Mechanism:** Automated Multi-AZ failover by the cloud provider (e.g., AWS RDS Aurora). API Gateway should queue or reject traffic with `503` until the `/v1/health/ready` probe succeeds.

## 2. Database Lock (Deadlock / Row Lock)
Two concurrent processes attempt to update the same `assessment_id` state simultaneously, creating a deadlock.

*   **Expected System Behavior:** The transaction throws a Deadlock Exception. The ORM/Database driver catches the exception and attempts a finite number of retries (e.g., 3 retries with exponential backoff). If retries fail, the transaction rolls back completely.
*   **HTTP Response:** `409 Conflict` or `500 Internal Server Error` (if retries exhausted).
*   **Audit Implications:** The Orchestrator must publish an `EXECUTION_FAILED` event to the Audit Ledger detailing the lock timeout, ensuring a record exists of the incomplete processing attempt.
*   **Regulatory Implications:** Low. The transaction rolled back, meaning no official underwriting decision was committed to the database.
*   **Recovery Mechanism:** Application-level retries for transient locks. Optimize transaction boundaries to be as short as possible to prevent lock escalation.

## 3. Connection Pool Exhaustion
A sudden spike in traffic causes the Orchestrator to exhaust all available PostgreSQL connections.

*   **Expected System Behavior:** New requests attempting to acquire a connection block until a timeout is reached, then fail closed.
*   **HTTP Response:** `503 Service Unavailable`.
*   **Audit Implications:** Similar to Database Unavailable; the request drops before processing begins.
*   **Regulatory Implications:** Low, as no credit decision is made.
*   **Recovery Mechanism:** Implement a connection multiplexer (e.g., PgBouncer). Configure the API Gateway to rate-limit incoming `POST /v1/assess` requests before they overwhelm the backend pool.

## 4. Audit Ledger Unavailable
The Kafka/RabbitMQ broker handling the asynchronous audit events goes down, or the Audit Service cannot write to the DB.

*   **Expected System Behavior:** **CRITICAL FAIL-CLOSED.** If the Orchestrator cannot publish the audit event (e.g., the Kafka producer `ack` times out), it *must not* return a successful response to the user. It must roll back the assessment transaction.
*   **HTTP Response:** `500 Internal Server Error`.
*   **Audit Implications:** We lose the ability to log. Therefore, we must halt all business operations. Operating without an audit log violates our compliance guarantees.
*   **Regulatory Implications:** If the system failed *open* (approved the loan without logging), it would be a catastrophic FCRA violation, rendering us unable to defend against future inquiries. Failing closed protects the business.
*   **Recovery Mechanism:** The Orchestrator should buffer events locally (e.g., in memory or a fallback Redis queue) for a very short window (e.g., 5 seconds) before failing the transaction. Broker requires highly available multi-broker clusters.

## 5. Model Registry Unavailable
The ML Inference Service attempts to boot or reload models, but the Database or the S3 Artifact Store is unreachable.

*   **Expected System Behavior:** The ML Inference Service fails its `/v1/health/deep` check and refuses to boot. If already running, it refuses to process new inference requests if it cannot verify the active model hash.
*   **HTTP Response:** `503 Service Unavailable` from the ML endpoint, causing the Orchestrator to return `500 Internal Server Error` for the overall assessment.
*   **Audit Implications:** Orchestrator logs an `E3_INFERENCE_FAILED` event to the Audit Ledger.
*   **Regulatory Implications:** Zero compliance risk, as the system safely halted.
*   **Recovery Mechanism:** ML Inference Service should cache the active `model_id` and artifact locally and operate on the last known good configuration until the registry is restored, provided the cached hash still matches.

## 6. Rules Registry Unavailable
The Rules Engine Service cannot fetch the active logic payload for E1, E2, or E5.

*   **Expected System Behavior:** The Rules Service cannot execute deterministic logic. It must fail closed.
*   **HTTP Response:** `500 Internal Server Error` from the Rules endpoint, causing the Orchestrator to fail the assessment.
*   **Audit Implications:** Orchestrator logs an `E1_EVALUATION_FAILED` event.
*   **Regulatory Implications:** A silent default to a static fallback rule (e.g., rejecting everyone) without logging the rule version would violate transparency. Failing closed is the only safe option.
*   **Recovery Mechanism:** The Rules Service should maintain an in-memory cache of the rules (updated via WebSockets or polling). If the DB goes down, it can serve from the cache, provided the cache is not stale beyond a strict TTL (e.g., 5 minutes).

## 7. Partial Transaction Failures
The Orchestrator completes E1 (Eligibility) and E2 (Tiering), but the network drops before E3 (Archetype) can execute.

*   **Expected System Behavior:** The Orchestrator's execution DAG detects the timeout from the ML service. It must run a compensating transaction (Saga pattern) or rollback the entire `assessment` state.
*   **HTTP Response:** `500 Internal Server Error`.
*   **Audit Implications:** The Audit Ledger will show `E1_SUCCESS`, `E2_SUCCESS`, and `E3_TIMEOUT`. This provides a perfect forensic trail of exactly where the DAG broke.
*   **Regulatory Implications:** If the partial state was persisted and later queried as a "final" decision, it would misrepresent the applicant's status. The database must reflect a `FAILED_PROCESSING` status, requiring the applicant to resubmit.
*   **Recovery Mechanism:** Implement idempotency keys. If the user retries with the same payload and Idempotency-Key, the Orchestrator resumes the DAG from E3, reading the cached E1/E2 results from the database.

## 8. Network Partitions
The Orchestrator can reach the Rules Service but cannot reach the Audit Ledger or the Database.

*   **Expected System Behavior:** The system strictly prioritizes consistency over availability (CP in CAP theorem). All active underwriting pipelines instantly halt.
*   **HTTP Response:** `504 Gateway Timeout` or `500 Internal Server Error`.
*   **Audit Implications:** In a partition, logs may be stranded on the Orchestrator node.
*   **Regulatory Implications:** High risk if decisions are communicated to the applicant but not logged centrally.
*   **Recovery Mechanism:** Orchestrators must implement local write-ahead logs (WAL) to disk. When the partition heals, a sidecar process flushes the local WAL to the central Kafka broker to reconstruct the audit trail.
