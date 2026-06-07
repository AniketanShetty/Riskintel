# RiskIntel Backend System Architecture Specification

**Role:** Principal Systems Architect  
**Status:** FROZEN (Final Specification)  

---

## 1. Architecture Overview
RiskIntel is a financial decision-support system deployed as a suite of decoupled microservices. The architecture enforces a strict bifurcation between **Regulatory Gating** (Deterministic Rules) and **Strategic Profiling** (Machine Learning). This ensures 100% explainability for adverse actions (FCRA/ECOA compliance) while safely operationalizing advanced ML clustering for approved applicants.

*   **E1 (Eligibility):** Rule Engine
*   **E2 (Tiering):** Rule Engine
*   **E3 (Archetypes):** ML Engine (K-Means)
*   **E4 (Recommendation):** ML/Hybrid Engine
*   **E5 (Readiness):** Rule Engine

---

## 2. Service Boundaries
The backend is divided into five core microservices:

1.  **API Gateway:** Handles JWT authentication, rate limiting, and request routing.
2.  **Orchestrator Service:** Manages the execution Directed Acyclic Graph (DAG). Maintains assessment state.
3.  **Rules Engine Service:** High-throughput, stateless Go/Rust service evaluating deterministic rules from the Rule Registry.
4.  **ML Inference Service:** Python (FastAPI) service loading serialized Pickles/ONNX models into memory to compute non-linear projections.
5.  **Audit Ledger Service:** Asynchronous consumer pulling events from Kafka and writing immutable compliance logs to PostgreSQL.

```mermaid
graph TD
    Client[Client App] --> Gateway[API Gateway]
    Gateway --> Orchestrator[Orchestrator Service]
    
    Orchestrator -->|Evaluate E1, E2, E5| Rules[Rules Engine Service]
    Orchestrator -->|Evaluate E3, E4| ML[ML Inference Service]
    
    Orchestrator -.->|Async Events| Kafka[Message Broker Kafka]
    Kafka -.-> Audit[Audit Ledger Service]
    
    Rules --> DB[(PostgreSQL DB)]
    ML --> DB
    Audit --> DB
    Orchestrator --> DB
```

---

## 3. Orchestrator Flow (Request Lifecycle)
The Orchestrator manages the DAG. If an applicant fails a deterministic gate (E1), the DAG immediately halts, returning a rejection (Person B Flow). If they pass, the DAG completes the ML profiling (Person A Flow).

```mermaid
stateDiagram-v2
    [*] --> Ingestion
    Ingestion --> E1_Eligibility
    
    E1_Eligibility --> E1_Fail : Rule Triggered
    E1_Fail --> [*] : Return REJECTED & Adverse Action Code
    
    E1_Eligibility --> E2_Tiering : PASS
    E2_Tiering --> E3_Archetype
    E3_Archetype --> E4_Recommendation
    E4_Recommendation --> E5_Readiness
    E5_Readiness --> [*] : Return APPROVED & Profiling Data
```

---

## 4. Rule Engine Flow
The Rules Engine Service is completely stateless. It fetches the active configuration for the requested rule and evaluates the applicant payload against it.

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant R as Rules Service
    participant DB as PostgreSQL (rule_registry)
    
    O->>R: POST /evaluate (Engine=E1, Payload)
    R->>DB: GET active_rule (engine_id=E1)
    DB-->>R: Returns Rule Logic (e.g. cibil_min: 650, version: v1.0)
    R->>R: Evaluate Payload vs Logic
    alt Fails Threshold
        R-->>O: Response (FAIL, rejection_reason, rule_version)
    else Passes Threshold
        R-->>O: Response (PASS, rule_version)
    end
```

---

## 5. ML Inference Flow
The ML Inference Service requires strict lineage tracking. Models are version-controlled in an S3 registry.

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant ML as ML Inference Service
    participant S3 as Model Artifact Store
    participant DB as PostgreSQL (model_registry)
    
    ML->>DB: Startup: Get Active Models
    DB-->>ML: Return S3 URIs
    ML->>S3: Download Pickles/ONNX
    S3-->>ML: Artifacts Loaded into Memory
    
    O->>ML: POST /predict (Engine=E3, Features)
    ML->>ML: Apply StandardScaler
    ML->>ML: Compute K-Means Centroid Distances
    ML-->>O: Response (Archetype Label, model_id)
```

---

## 6. Audit Flow
Compliance mandates an immutable ledger. The Orchestrator does not write audit logs synchronously. It publishes events to Kafka, ensuring the API response remains low-latency while guaranteeing eventual consistency in the audit log.

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant K as Kafka (audit_topic)
    participant A as Audit Service
    participant DB as PostgreSQL (audit_log)
    
    O->>K: Publish Event (E1_EVALUATED, Payload, correlation_id)
    O-->>Client: 200 OK (Fast Return)
    K->>A: Consume Event
    A->>DB: INSERT into audit_log (Immutable Append)
```

---

## 7. Database Flow
The database enforces Referential Integrity between the `assessments` (the applicant request) and the `registry` (the rules/models used).

```mermaid
erDiagram
    ASSESSMENTS ||--o| ELIGIBILITY_RESULTS : has
    ASSESSMENTS ||--o| ARCHETYPE_RESULTS : has
    RULE_REGISTRY ||--o{ ELIGIBILITY_RESULTS : traces_to
    MODEL_REGISTRY ||--o{ ARCHETYPE_RESULTS : traces_to
    
    ASSESSMENTS {
        uuid id
        jsonb input_features
    }
    ELIGIBILITY_RESULTS {
        uuid rule_id FK
        boolean is_eligible
    }
    ARCHETYPE_RESULTS {
        uuid model_id FK
        varchar archetype
    }
```

---

## 8. Health Check Architecture
Kubernetes requires specialized health endpoints to manage routing and pod lifecycles safely.

*   `GET /v1/health/live`: Simple `200 OK`. If this fails, K8s kills and restarts the pod.
*   `GET /v1/health/ready`: Checks DB/Redis connection. If this fails, K8s stops routing traffic to the pod but does not kill it.
*   `GET /v1/health/deep`: Iterates through the `model_registry` and validates that all models marked `active` in the database are successfully loaded in RAM. Used for Datadog/Prometheus monitoring.

---

## 9. Security Architecture
*   **Authentication:** The API Gateway validates JWTs issued by the Identity Provider (e.g., Auth0/Okta).
*   **PII Hashing:** Applicant Tax IDs (SSN/PAN) are never stored in plaintext. They are salted and hashed via SHA-256 (`tax_id_hash`) at the API Gateway. This allows for duplicate application detection without exposing raw identity vectors.
*   **Data at Rest/Transit:** All PostgreSQL volumes use AES-256 encryption at rest. Internal service-to-service communication occurs over mTLS (mutual TLS) managed by a service mesh (e.g., Istio).

---

## 10. Deployment Architecture
*   **Infrastructure:** Kubernetes (EKS/GKE).
*   **Compute Profiles:**
    *   *Rules Service Pods:* High CPU, Low Memory, horizontally scaled aggressively.
    *   *ML Inference Pods:* Moderate CPU, High Memory (caching large matrices), scaled based on custom metrics (e.g., inference queue length).
*   **CI/CD Pipeline (ML Gate):**
    *   Pushing a new model to the Registry triggers an automated UMAP topology pipeline in Jenkins/GitHub Actions.
    *   If the Local Neighborhood Homogeneity score drops below `0.90`, the pipeline automatically fails, blocking the degraded model from production deployment.
