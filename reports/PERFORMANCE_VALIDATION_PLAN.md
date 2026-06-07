# RiskIntel Performance Validation Framework

**Role:** Principal Performance Engineer  
**Status:** Architecture Specification  
**Target SLA:** End-to-End Orchestrator p95 Latency < 500ms  

## Overview
The RiskIntel Directed Acyclic Graph (DAG) executes a hybrid sequence of deterministic rules (E1, E2, E5) and Machine Learning models (E3, E4) before committing to an audit ledger. Achieving a sub-500ms p95 latency across a synchronous API request requires microscopic latency budgets, aggressive connection pooling, and mathematically validated concurrency limits. 

This document defines the load testing protocols and acceptance thresholds required for production certification.

---

## 1. Latency Budgets Per Component
To achieve an end-to-end p95 of 500ms, the Orchestrator must strictly enforce component-level timeouts. 

| Component | Architecture | Target p50 | Target p95 | Hard Timeout (Fail) |
| :--- | :--- | :--- | :--- | :--- |
| **API Gateway (Ingress)** | Nginx / Envoy | 5ms | 15ms | 50ms |
| **E1 (Eligibility)** | Rules Engine (Go/Rust) | 10ms | 25ms | 50ms |
| **E2 (Tiering)** | Rules Engine (Go/Rust) | 10ms | 25ms | 50ms |
| **E3 (Archetypes)** | ML Inference (FastAPI) | 50ms | 120ms | 200ms |
| **E4 (Recommendations)**| ML Inference (FastAPI) | 50ms | 120ms | 200ms |
| **E5 (Readiness)** | Rules Engine (Go/Rust) | 10ms | 25ms | 50ms |
| **Audit Ledger Commit** | Kafka Producer (Async) | 5ms | 15ms | 100ms |
| **Database I/O (Total)** | PostgreSQL | 20ms | 50ms | 150ms |
| **Total E2E Orchestrator**| **Hybrid DAG** | **160ms** | **395ms** | **500ms** |

*Note: The remaining 105ms in the p95 budget accounts for internal network transit, Orchestrator serialization overhead, and garbage collection pauses.*

---

## 2. Load Testing Strategy
We will utilize `k6` to simulate sustained baseline traffic and measure degradation over time.

*   **Test Profile:** Constant Arrival Rate.
*   **Volume:** 100 Requests Per Second (RPS) sustained for 60 minutes.
*   **Acceptance Thresholds:**
    *   E2E p95 Latency < 500ms.
    *   E2E p99 Latency < 800ms.
    *   HTTP 5xx Error Rate = 0.00%.
*   **Focus:** Memory leaks in the ML Inference Service (Python memory bloat) and connection starvation in the Orchestrator.

## 3. Concurrency Testing Strategy (Spike Testing)
Simulates sudden surges (e.g., a marketing email blast triggering thousands of simultaneous applications).

*   **Test Profile:** Step-load increase (10 RPS -> 500 RPS over 30 seconds).
*   **Acceptance Thresholds:**
    *   System must not drop traffic (No 503s from Gateway).
    *   If Orchestrator queue exceeds capacity, the Gateway must return `429 Too Many Requests` gracefully, protecting the PostgreSQL connection pool.
    *   Recovery time: System must return to baseline p95 (< 500ms) within 60 seconds of the traffic spike subsiding.

---

## 4. Bottleneck Identification
During load tests, we will actively monitor the following known chokepoints:

1.  **Python GIL Contention:** Is the FastAPI ML service bottlenecked by CPU matrix math (K-Means/E3)? If so, we must switch from `uvicorn` threaded workers to multiple discrete `gunicorn` processes.
2.  **Database Connection Queue:** If the DB p95 exceeds 50ms, we must implement `PgBouncer` to multiplex connections rather than allowing the Orchestrator to open a dedicated TCP connection per request.
3.  **Kafka Producer Acks:** If the async audit commit spikes above 15ms, the Orchestrator is blocking while waiting for Kafka leader replication. We must tune `acks=1` or `linger.ms` for the producer.

---

## 5. PostgreSQL Stress Testing
The database is the ultimate state manager for the Orchestrator.

*   **Test Scenario:** 1,000 concurrent updates to the `assessments` and `results` tables.
*   **Acceptance Thresholds:**
    *   Zero Deadlocks.
    *   Max Row Lock wait time < 20ms.
    *   No exhaustion of `max_connections` (Validation of PgBouncer effectiveness).
*   **Strategy:** Run highly randomized `applicant_id` payloads to spread the B-Tree index insertions and avoid index page contention.

## 6. ML Inference Stress Testing
Python is notoriously poor at high-concurrency CPU-bound operations. 

*   **Test Scenario:** Isolate the ML Inference microservice and hit it with 200 RPS.
*   **Acceptance Thresholds:**
    *   E3 K-Means Inference p95 < 120ms.
    *   Container RAM utilization remains stable (flatline after initial load; no upward drift indicating object retention).
*   **Strategy:** Validate that the `StandardScaler` and `KMeans` models are instantiated *once* globally at application startup, not re-instantiated per request. 

## 7. Cold Start Testing
Kubernetes Horizontal Pod Autoscalers (HPA) will spin up new ML Inference pods during traffic spikes.

*   **Test Scenario:** Terminate a running ML Inference Pod. Measure the time it takes for a new Pod to pull the image, boot, download the 50MB Pickle files from S3, deserialize them, and respond `200 OK` to the `/v1/health/deep` probe.
*   **Acceptance Thresholds:**
    *   Rules Engine Pod Boot Time < 2 seconds.
    *   ML Inference Pod Boot Time < 15 seconds.
*   **Strategy:** If ML boot time exceeds 15 seconds, we must implement "Pre-baked" Docker images where the Pickle files are downloaded during the CI/CD build phase, eliminating the S3 network hop during runtime scaling.
