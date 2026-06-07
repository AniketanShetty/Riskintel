# RiskIntel Backend Architecture Specification

**Status:** FROZEN  
**Role:** Principal Product Architect  
**System Type:** Financial Decision-Support System  

## Executive Summary
This document serves as the frozen backend specification for the RiskIntel platform, incorporating the findings of the exhaustive ML Forensic Audit. The architecture enforces a strict bifurcation between **Deterministic Rule Engines** (for regulatory gating) and **Machine Learning Models** (for strategic profiling and limits).

### Engine States
*   **E1 (Eligibility):** Deterministic Rules Engine (Replaced ML)
*   **E2 (Risk Tiering):** Deterministic Rules Engine
*   **E3 (Borrower Archetype):** ML (K-Means Clustering)
*   **E4 (Credit Limit):** ML / Hybrid (Production Ready)
*   **E5 (Readiness):** Deterministic Rules Engine
*   **Orchestrator:** Asynchronous Decision DAG (Production Ready)

---

## 1. Service Boundaries
The backend is organized into decoupled microservices to ensure isolation between regulatory decisions and predictive profiling.

*   **API Gateway:** Handles authentication, rate limiting, and request routing.
*   **Decision Orchestrator Service:** Manages the DAG execution pipeline. Passes state between E1 -> E2 -> E3 -> E4 -> E5.
*   **Rules Engine Service (E1, E2, E5):** A high-throughput, low-latency stateless service executing deterministic `if/else` logic loaded from configuration tables. Provides perfect explainability.
*   **ML Inference Service (E3, E4):** A Python-based microservice (FastAPI) loading serialized models (Pickle/ONNX) into memory. Handles feature scaling, clustering projection, and limit inference.
*   **Audit Service:** Listens to asynchronous events from the Orchestrator and immutably logs every decision, rule triggered, and model output.

---

## 2. Database Schema
The primary datastore (PostgreSQL) separates transactional decision state from immutable audit logs and rule configurations.

**`applications` Table**
*   `id` (UUID)
*   `applicant_id` (UUID)
*   `status` (Enum: PENDING, APPROVED, REJECTED)
*   `created_at` (Timestamp)

**`decision_state` Table (JSONB Payload per Engine)**
*   `application_id` (UUID, FK)
*   `e1_eligibility` (Boolean)
*   `e2_risk_tier` (String)
*   `e3_archetype` (String)
*   `e4_approved_limit` (Numeric)
*   `e5_readiness` (Boolean)
*   `rejection_reason` (String - for Adverse Action)

**`rule_configurations` Table (Version Controlled)**
*   `engine_id` (String: "E1")
*   `rule_key` (String: "cibil_threshold")
*   `rule_value` (Numeric: 650)
*   `active_from` (Timestamp)
*   `version` (Integer)

---

## 3. Audit Architecture
Operating under financial explainability requirements demands an immutable audit trail for FCRA/ECOA compliance.

*   **Immutable Append-Only Log:** Every decision step fires an event (e.g., `E1_EVALUATED`) to a Kafka/RabbitMQ topic. The Audit Service writes these to an append-only database table.
*   **Adverse Action Payload:** If E1 rejects an applicant, the Orchestrator immediately halts the DAG and logs the exact rule version and threshold that triggered the rejection.
*   **ML Explainability:** For E3 and E4, the inference service logs the exact input feature vector and the scaler parameters used at the time of inference to guarantee reproducibility of the cluster assignment.

---

## 4. Model Registry Architecture
To safely manage the ML assets (E3, E4) and prevent silent drift.

*   **Artifact Store:** S3 bucket storing versioned model artifacts (e.g., `s3://models/e3_kmeans_v1.2.pkl`, `e3_scaler_v1.2.pkl`).
*   **Registry DB:** Tracks model lineage, training dataset hashes, and evaluation metrics (e.g., UMAP topology scores).
*   **Deployment Gate:** The ML Inference Service polls the Registry DB on startup. It only loads models flagged as `PRODUCTION`.
*   **Shadow Mode:** New models can be deployed in `SHADOW` mode, processing traffic and logging to the Audit DB without affecting the live `decision_state`.

---

## 5. API Contracts

### POST `/api/v1/decisions/evaluate`
**Request:**
```json
{
  "applicant_id": "uuid-123",
  "financial_features": {
    "cibil_score": 720,
    "net_monthly_income": 85000,
    "age": 34,
    "time_with_curr_empr": 48,
    "education": "GRADUATE"
  }
}
```

**Response (Approved):**
```json
{
  "application_id": "uuid-999",
  "status": "APPROVED",
  "decision_summary": {
    "eligibility": "PASS",
    "risk_tier": "TIER_1",
    "archetype": "Mid-Career Established",
    "credit_limit": 150000
  }
}
```

**Response (Rejected by E1):**
```json
{
  "application_id": "uuid-999",
  "status": "REJECTED",
  "rejection_reason": "Credit score below minimum required threshold (650)",
  "decision_summary": {
    "eligibility": "FAIL"
  }
}
```

---

## 6. Deployment Architecture
*   **Infrastructure:** Kubernetes (EKS/GKE) for orchestration, allowing independent scaling of the Rules Engine vs. ML Inference services.
*   **Compute Profiles:**
    *   *Rules Service:* High CPU, minimal RAM (rapid stateless execution).
    *   *ML Inference Service:* Moderate CPU, higher RAM (caching serialized models).
*   **CI/CD Pipeline:** 
    *   Code changes to the Orchestrator/Rules bypass the ML registry.
    *   Updates to rules in `rule_configurations` require a maker-checker approval in an internal admin portal.
    *   ML Model retraining triggers automated topological audits (PCA/UMAP tests). If tests fail, the CI/CD pipeline blocks deployment.
